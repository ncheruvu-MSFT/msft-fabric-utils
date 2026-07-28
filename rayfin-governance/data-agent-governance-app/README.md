# data-agent-governance-app

Rayfin port of the data-agent governance surface
([fabric-data-agent-governance](../../fabric-data-agent-governance)).

## Entities

| Entity | Purpose |
|---|---|
| `Agent` | Registered data agent (name, domain, owner, model deployment, HITL flag) |
| `Tool` | Tools an agent may call (endpoint, auth mode, sensitivity, domain allowlist) |
| `PromptTemplate` | Versioned prompt bound to an agent |
| `RunLog` | Append-only execution record (tokens, tool calls, redacted IO) |
| `RedTeamFinding` | Red-team / safety findings against an agent |

## Authorization model

| Role | Capabilities |
|---|---|
| `agent-admin` | Full control of all entities |
| `agent-author` | Create + update own `Agent` and `PromptTemplate` |
| `agent-runtime` | `create` `RunLog` only (issued to the agent runtime SP) |
| `red-team` | `create` `RedTeamFinding`, update findings they own |
| authenticated | Read everything (so domain stewards can audit) |

## Why this lives in Rayfin

The governance surface is essentially CRUD + RBAC + audit log — exactly
Rayfin's sweet spot. The agent **runtime** stays where it is; only the
control-plane registry and audit store move here, called via the generated
GraphQL endpoint.

## Runtime integration sketch

```ts
// inside the agent runtime
await client.data.RunLog.create({
  agentId, promptTemplateId, callerSub,
  status: 'success',
  inputTokens, outputTokens,
  toolCallsJson: JSON.stringify(toolCalls),
  redactedInput, redactedOutput,
  startedAt, finishedAt,
});
```
