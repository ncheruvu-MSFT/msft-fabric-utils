// Conversational data-agent client for the lineage-app.
//
// When `VITE_RAYFIN_AGENT_URL` is configured the question is forwarded to a
// Fabric Data Agent (or any compatible chat endpoint) grounded on the lineage
// graph. When it is not configured, a lightweight local engine answers
// questions directly over the edges already loaded in the browser, so the "Ask"
// experience works offline against seed data.

import { LineageEdge, categorize, shortName } from './dataClient';

const AGENT_URL = import.meta.env.VITE_RAYFIN_AGENT_URL;

export interface AgentAnswer {
  text: string;
  source: 'agent' | 'local';
}

function describe(e: LineageEdge): string {
  return `**${shortName(e.sourceQname)}** → **${shortName(e.targetQname)}** _(${e.processName}, ${categorize(e.processType)})_`;
}

/** Find an asset mentioned in the question by matching against short names. */
function findAsset(q: string, edges: LineageEdge[]): string | undefined {
  const names = new Set<string>();
  for (const e of edges) {
    names.add(shortName(e.sourceQname));
    names.add(shortName(e.targetQname));
  }
  const lower = q.toLowerCase();
  let best: string | undefined;
  for (const n of names) {
    if (lower.includes(n.toLowerCase())) {
      if (!best || n.length > best.length) best = n;
    }
  }
  return best;
}

function matchesAsset(qname: string, asset: string): boolean {
  return shortName(qname).toLowerCase() === asset.toLowerCase();
}

// Heuristic natural-language answering over the loaded edges.
function answerLocally(question: string, edges: LineageEdge[]): string {
  const q = question.trim().toLowerCase();

  if (!q) {
    return 'Ask me about lineage — for example, "what feeds fact_sales?", "what is downstream of Customers?", or "how many Spark processes are there?".';
  }

  const asset = findAsset(question, edges);

  // Upstream — what feeds / produces this asset.
  if (asset && /(upstream|feeds?|sources?|produces?|where does|comes? from|inputs?)/.test(q)) {
    const ups = edges.filter((e) => matchesAsset(e.targetQname, asset));
    if (ups.length === 0) {
      return `**${asset}** has no upstream edges in the current graph — it looks like a source.`;
    }
    return (
      `Upstream of **${asset}** (${ups.length}):\n` +
      ups.map((e) => `- ${describe(e)}`).join('\n')
    );
  }

  // Downstream — what consumes / is produced from this asset.
  if (asset && /(downstream|consumes?|feeds? into|targets?|where does .* go|outputs?|used by|depends?)/.test(q)) {
    const downs = edges.filter((e) => matchesAsset(e.sourceQname, asset));
    if (downs.length === 0) {
      return `**${asset}** has no downstream edges — it is a leaf / final consumer.`;
    }
    return (
      `Downstream of **${asset}** (${downs.length}):\n` +
      downs.map((e) => `- ${describe(e)}`).join('\n')
    );
  }

  // Generic impact: show both directions for an asset.
  if (asset && /(impact|lineage|trace|both|connected|relate)/.test(q)) {
    const ups = edges.filter((e) => matchesAsset(e.targetQname, asset));
    const downs = edges.filter((e) => matchesAsset(e.sourceQname, asset));
    return (
      `Lineage for **${asset}**:\n` +
      `Upstream (${ups.length}):\n` +
      (ups.map((e) => `- ${describe(e)}`).join('\n') || '- (none)') +
      `\nDownstream (${downs.length}):\n` +
      (downs.map((e) => `- ${describe(e)}`).join('\n') || '- (none)')
    );
  }

  // Count / how-many, optionally scoped by process category.
  if (/(how many|count|number of|total)/.test(q)) {
    const cats = ['adf', 't-sql', 'tsql', 'power bi', 'pbi', 'spark', 'dataflow', 'pipeline'];
    const hit = cats.find((c) => q.includes(c));
    if (hit) {
      const n = edges.filter((e) =>
        categorize(e.processType).toLowerCase().replace(/[^a-z]/g, '').includes(hit.replace(/[^a-z]/g, '')),
      ).length;
      return `There ${n === 1 ? 'is' : 'are'} **${n}** ${hit.toUpperCase()} edge${n === 1 ? '' : 's'}.`;
    }
    if (/asset|node|table|dataset/.test(q)) {
      const assets = new Set<string>();
      edges.forEach((e) => {
        assets.add(e.sourceQname);
        assets.add(e.targetQname);
      });
      return `There are **${assets.size}** distinct data assets connected by **${edges.length}** lineage edges.`;
    }
    return `There are **${edges.length}** lineage edges in the graph.`;
  }

  // List by process category.
  const catMap: Record<string, string> = {
    adf: 'ADF',
    tsql: 'T-SQL',
    'power bi': 'Power BI',
    pbi: 'Power BI',
    spark: 'Spark',
    dataflow: 'Dataflow',
    pipeline: 'Pipeline',
  };
  const catKey = Object.keys(catMap).find((c) => q.includes(c));
  if (catKey && /(list|show|which|what)/.test(q)) {
    const target = catMap[catKey];
    const matches = edges.filter((e) => categorize(e.processType) === target);
    if (matches.length === 0) {
      return `There are no ${target} edges right now.`;
    }
    return (
      `${target} edges (${matches.length}):\n` +
      matches.map((e) => `- ${describe(e)}`).join('\n')
    );
  }

  // Sources / sinks.
  if (/(roots?|sources?|origins?)/.test(q)) {
    const targets = new Set(edges.map((e) => shortName(e.targetQname)));
    const roots = Array.from(
      new Set(edges.map((e) => shortName(e.sourceQname))),
    ).filter((s) => !targets.has(s));
    return `Source roots (no upstream): ${roots.map((r) => `**${r}**`).join(', ') || '(none)'}.`;
  }
  if (/(leaf|leaves|sinks?|final|consumers?)/.test(q)) {
    const sources = new Set(edges.map((e) => shortName(e.sourceQname)));
    const leaves = Array.from(
      new Set(edges.map((e) => shortName(e.targetQname))),
    ).filter((t) => !sources.has(t));
    return `Leaf assets (no downstream): ${leaves.map((l) => `**${l}**`).join(', ') || '(none)'}.`;
  }

  // Keyword search fallback across qnames + process names.
  const tokens = q.split(/\W+/).filter((w) => w.length > 2);
  const hits = edges.filter((e) => {
    const hay = `${e.sourceQname} ${e.targetQname} ${e.processName} ${e.processType}`.toLowerCase();
    return tokens.some((w) => hay.includes(w));
  });
  if (hits.length > 0) {
    return (
      `I found ${hits.length} matching edge${hits.length === 1 ? '' : 's'}:\n` +
      hits.slice(0, 6).map((e) => `- ${describe(e)}`).join('\n')
    );
  }

  return "I couldn't find anything matching that. Try asking about an asset name, a process type (ADF, T-SQL, Power BI, Spark), or upstream/downstream lineage.";
}

export async function askAgent(
  question: string,
  edges: LineageEdge[],
): Promise<AgentAnswer> {
  if (!AGENT_URL) {
    return { text: answerLocally(question, edges), source: 'local' };
  }
  const res = await fetch(`${AGENT_URL}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context: { entity: 'LineageEdge' } }),
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Agent ${res.status}: ${await res.text()}`);
  }
  const json = (await res.json()) as { answer?: string; reply?: string };
  return { text: json.answer ?? json.reply ?? '(no answer)', source: 'agent' };
}
