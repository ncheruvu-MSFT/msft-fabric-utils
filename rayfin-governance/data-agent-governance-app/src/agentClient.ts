// Conversational data-agent client for the data-agent-governance-app.
//
// When `VITE_RAYFIN_AGENT_URL` is configured the question is forwarded to a
// Fabric Data Agent grounded on the agent registry. Otherwise a lightweight
// local engine answers over the rows already loaded in the browser, so the
// "Ask" experience works offline against seed data.

import { Agent, AgentStatus } from './dataClient';

const AGENT_URL = import.meta.env.VITE_RAYFIN_AGENT_URL;

export interface AgentAnswer {
  text: string;
  source: 'agent' | 'local';
}

const STATUSES: AgentStatus[] = ['Draft', 'In review', 'Approved', 'Suspended'];

function findStatus(q: string): AgentStatus | undefined {
  const lower = q.toLowerCase();
  if (lower.includes('suspend')) return 'Suspended';
  if (lower.includes('review')) return 'In review';
  if (lower.includes('approv')) return 'Approved';
  if (lower.includes('draft')) return 'Draft';
  return STATUSES.find((s) => lower.includes(s.toLowerCase()));
}

function describe(a: Agent): string {
  const hitl = a.requiresHumanApproval ? ' · requires human approval' : '';
  return `**${a.name}** (${a.domain}, ${a.status}) — model ${a.modelDeployment}${hitl}. _Owner ${a.owner}._`;
}

function answerLocally(question: string, agents: Agent[]): string {
  const q = question.trim().toLowerCase();
  if (!q) {
    return 'Ask me about registered agents — for example, "which agents need human approval?" or "how many are approved?".';
  }

  // Human-in-the-loop questions.
  if (/(human|approval|hitl|reviewed by a person|sign.?off)/.test(q)) {
    const matches = agents.filter((a) => a.requiresHumanApproval);
    if (matches.length === 0) {
      return 'No agents currently require human approval.';
    }
    return (
      `Agents requiring human approval (${matches.length}):\n` +
      matches.map((a) => `- ${describe(a)}`).join('\n')
    );
  }

  // Count questions, optionally scoped by status.
  if (/(how many|count|number of|total)/.test(q)) {
    const status = findStatus(q);
    if (status) {
      const n = agents.filter((a) => a.status === status).length;
      return `There ${n === 1 ? 'is' : 'are'} **${n}** agent${
        n === 1 ? '' : 's'
      } with status **${status}**.`;
    }
    return `There are **${agents.length}** registered agents across ${
      new Set(agents.map((a) => a.domain)).size
    } domains.`;
  }

  // Named agent lookup.
  const named = agents.find((a) => q.includes(a.name.toLowerCase()));
  if (named) {
    return describe(named);
  }

  // Status scoped.
  const status = findStatus(q);
  if (status) {
    const matches = agents.filter((a) => a.status === status);
    if (matches.length === 0) {
      return `There are no **${status}** agents right now.`;
    }
    return (
      `${status} agents (${matches.length}):\n` +
      matches.map((a) => `- ${describe(a)}`).join('\n')
    );
  }

  // Domain scoped.
  const domains = Array.from(new Set(agents.map((a) => a.domain)));
  const domain = domains.find((d) => q.includes(d.toLowerCase()));
  if (domain) {
    const matches = agents.filter((a) => a.domain === domain);
    return (
      `Agents in the **${domain}** domain (${matches.length}):\n` +
      matches.map((a) => `- ${describe(a)}`).join('\n')
    );
  }

  // Keyword fallback.
  const tokens = q.split(/\W+/).filter((w) => w.length > 2);
  const hits = agents.filter((a) => {
    const hay = `${a.name} ${a.domain} ${a.modelDeployment}`.toLowerCase();
    return tokens.some((w) => hay.includes(w));
  });
  if (hits.length > 0) {
    return (
      `I found ${hits.length} matching agent${hits.length === 1 ? '' : 's'}:\n` +
      hits.slice(0, 5).map((a) => `- ${describe(a)}`).join('\n')
    );
  }

  return "I couldn't find anything matching that. Try asking about a status (draft, in review, approved, suspended), a domain, human approval, or an agent name.";
}

export async function askAgent(
  question: string,
  agents: Agent[],
): Promise<AgentAnswer> {
  if (!AGENT_URL) {
    return { text: answerLocally(question, agents), source: 'local' };
  }
  const res = await fetch(`${AGENT_URL}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context: { entity: 'Agent' } }),
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Agent ${res.status}: ${await res.text()}`);
  }
  const json = (await res.json()) as { answer?: string; reply?: string };
  return { text: json.answer ?? json.reply ?? '(no answer)', source: 'agent' };
}
