// Conversational data-agent client for the sdlc-governance-app.
//
// When `VITE_RAYFIN_AGENT_URL` is configured the question is forwarded to a
// Fabric Data Agent grounded on the attestation data. Otherwise a lightweight
// local engine answers over the rows already loaded in the browser, so the
// "Ask" experience works offline against seed data.

import { AttestationResult, AttestationRun } from './dataClient';

const AGENT_URL = import.meta.env.VITE_RAYFIN_AGENT_URL;

export interface AgentAnswer {
  text: string;
  source: 'agent' | 'local';
}

const RESULTS: AttestationResult[] = ['Pass', 'Fail', 'Warning'];

function findResult(q: string): AttestationResult | undefined {
  const lower = q.toLowerCase();
  if (lower.includes('fail')) return 'Fail';
  if (lower.includes('warn')) return 'Warning';
  if (lower.includes('pass')) return 'Pass';
  return RESULTS.find((r) => lower.includes(r.toLowerCase()));
}

function describe(r: AttestationRun): string {
  return `**${r.workspaceId}** · ${r.policyName} → **${r.result}** (commit ${r.commitSha})`;
}

function answerLocally(question: string, runs: AttestationRun[]): string {
  const q = question.trim().toLowerCase();
  if (!q) {
    return 'Ask me about attestation runs — for example, "which workspaces are failing?" or "how many runs passed?".';
  }

  // Count questions, optionally scoped by result.
  if (/(how many|count|number of|total)/.test(q)) {
    const result = findResult(q);
    if (result) {
      const n = runs.filter((r) => r.result === result).length;
      return `There ${n === 1 ? 'is' : 'are'} **${n}** run${
        n === 1 ? '' : 's'
      } with result **${result}**.`;
    }
    return `There are **${runs.length}** attestation runs across ${
      new Set(runs.map((r) => r.workspaceId)).size
    } workspaces.`;
  }

  // Failing / warning / passing workspaces.
  const result = findResult(q);
  if (result) {
    const matches = runs.filter((r) => r.result === result);
    if (matches.length === 0) {
      return `No runs are currently **${result}**.`;
    }
    return (
      `${result} runs (${matches.length}):\n` +
      matches.map((r) => `- ${describe(r)}`).join('\n')
    );
  }

  // Policy scoped.
  const policies = Array.from(new Set(runs.map((r) => r.policyName)));
  const policy = policies.find((p) => q.includes(p.toLowerCase()));
  if (policy) {
    const matches = runs.filter((r) => r.policyName === policy);
    return (
      `Runs for policy **${policy}** (${matches.length}):\n` +
      matches.map((r) => `- ${describe(r)}`).join('\n')
    );
  }

  // Workspace scoped.
  const match = runs.find((r) => q.includes(r.workspaceId.toLowerCase()));
  if (match) {
    const all = runs.filter((r) => r.workspaceId === match.workspaceId);
    return (
      `Latest runs for **${match.workspaceId}** (${all.length}):\n` +
      all.map((r) => `- ${r.policyName} → **${r.result}** (${r.commitSha})`).join('\n')
    );
  }

  // Keyword fallback.
  const tokens = q.split(/\W+/).filter((w) => w.length > 2);
  const hits = runs.filter((r) => {
    const hay = `${r.workspaceId} ${r.policyName}`.toLowerCase();
    return tokens.some((w) => hay.includes(w));
  });
  if (hits.length > 0) {
    return (
      `I found ${hits.length} matching run${hits.length === 1 ? '' : 's'}:\n` +
      hits.slice(0, 5).map((r) => `- ${describe(r)}`).join('\n')
    );
  }

  return "I couldn't find anything matching that. Try asking about a result (pass, warning, fail), a policy name, or a workspace.";
}

export async function askAgent(
  question: string,
  runs: AttestationRun[],
): Promise<AgentAnswer> {
  if (!AGENT_URL) {
    return { text: answerLocally(question, runs), source: 'local' };
  }
  const res = await fetch(`${AGENT_URL}/api/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context: { entity: 'AttestationRun' } }),
    credentials: 'include',
  });
  if (!res.ok) {
    throw new Error(`Agent ${res.status}: ${await res.text()}`);
  }
  const json = (await res.json()) as { answer?: string; reply?: string };
  return { text: json.answer ?? json.reply ?? '(no answer)', source: 'agent' };
}
