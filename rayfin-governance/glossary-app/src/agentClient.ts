// Conversational data-agent client for the glossary-app.
//
// When `VITE_RAYFIN_AGENT_URL` is configured the question is forwarded to a
// Fabric Data Agent (or any compatible chat endpoint) that has been grounded on
// the glossary data. When it is not configured, a lightweight local engine
// answers questions directly over the rows already loaded in the browser, so the
// "Ask" experience works offline against seed data.

import { Term, TermStatus } from './dataClient';

const AGENT_URL = import.meta.env.VITE_RAYFIN_AGENT_URL;

export interface AgentAnswer {
  text: string;
  source: 'agent' | 'local';
}

const STATUSES: TermStatus[] = ['Draft', 'Pending', 'Approved', 'Rejected'];

function findStatus(q: string): TermStatus | undefined {
  const lower = q.toLowerCase();
  return STATUSES.find((s) => lower.includes(s.toLowerCase()));
}

function describe(t: Term): string {
  return `**${t.name}** (${t.domainName}, ${t.status}) — ${t.definition} _Submitted by ${t.submittedBy}._`;
}

// Heuristic natural-language answering over the loaded terms.
function answerLocally(question: string, terms: Term[]): string {
  const q = question.trim().toLowerCase();

  if (!q) {
    return 'Ask me about glossary terms — for example, "how many terms are pending?" or "what does Net Revenue mean?".';
  }

  // Direct definition lookup: match a term name mentioned in the question.
  const named = terms.find((t) => q.includes(t.name.toLowerCase()));
  if (named && /(what|define|definition|mean|meaning|who|status|owns?|submitted)/.test(q)) {
    if (/who|submitted|owns?/.test(q)) {
      return `**${named.name}** was submitted by ${named.submittedBy} and is currently **${named.status}**.`;
    }
    return describe(named);
  }

  // Count / how-many questions, optionally scoped by status.
  if (/(how many|count|number of|total)/.test(q)) {
    const status = findStatus(q);
    if (status) {
      const n = terms.filter((t) => t.status === status).length;
      return `There ${n === 1 ? 'is' : 'are'} **${n}** ${status.toLowerCase()} term${n === 1 ? '' : 's'}.`;
    }
    return `There are **${terms.length}** terms in the glossary across ${
      new Set(terms.map((t) => t.domainName)).size
    } domains.`;
  }

  // List by status.
  const status = findStatus(q);
  if (status && /(list|show|which|what)/.test(q)) {
    const matches = terms.filter((t) => t.status === status);
    if (matches.length === 0) {
      return `There are no ${status.toLowerCase()} terms right now.`;
    }
    return (
      `${status} terms (${matches.length}):\n` +
      matches.map((t) => `- ${describe(t)}`).join('\n')
    );
  }

  // Domain scoped.
  const domains = Array.from(new Set(terms.map((t) => t.domainName)));
  const domain = domains.find((d) => q.includes(d.toLowerCase()));
  if (domain) {
    const matches = terms.filter((t) => t.domainName === domain);
    return (
      `Terms in the **${domain}** domain (${matches.length}):\n` +
      matches.map((t) => `- ${describe(t)}`).join('\n')
    );
  }

  // Keyword search fallback across name + definition.
  const tokens = q.split(/\W+/).filter((w) => w.length > 2);
  const hits = terms.filter((t) => {
    const hay = `${t.name} ${t.definition}`.toLowerCase();
    return tokens.some((w) => hay.includes(w));
  });
  if (hits.length > 0) {
    return (
      `I found ${hits.length} matching term${hits.length === 1 ? '' : 's'}:\n` +
      hits.slice(0, 5).map((t) => `- ${describe(t)}`).join('\n')
    );
  }

  return "I couldn't find anything matching that. Try asking about a term name, a status (draft, pending, approved, rejected), or a domain.";
}

export async function askAgent(
  question: string,
  terms: Term[],
): Promise<AgentAnswer> {
  if (!AGENT_URL) {
    return { text: answerLocally(question, terms), source: 'local' };
  }
  const res = await fetch(`${AGENT_URL}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context: { entity: 'Term' } }),
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Agent ${res.status}: ${await res.text()}`);
  }
  const json = (await res.json()) as { answer?: string; reply?: string };
  return { text: json.answer ?? json.reply ?? '(no answer)', source: 'agent' };
}
