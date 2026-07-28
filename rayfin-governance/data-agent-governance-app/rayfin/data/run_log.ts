import { entity, uuid, text, int, date, authenticated } from '@microsoft/rayfin-core';

// Append-only. Agent runtimes POST here.
@entity()
@authenticated(['read'])
@authenticated(['create'], {
  policy: (claims) =>
    claims.role.eq('agent-runtime').or(claims.role.eq('agent-admin')),
})
@authenticated(['delete'], {
  policy: (claims) => claims.role.eq('agent-admin'),
})
export class RunLog {
  @uuid() id!: string;
  @text({ max: 200 }) agentId!: string;
  @text({ max: 200 }) promptTemplateId!: string;
  @text({ max: 200 }) callerSub!: string;
  @text({ max: 100 }) status!: string;
  @int() inputTokens!: number;
  @int() outputTokens!: number;
  @text({ optional: true, max: 4000 }) toolCallsJson?: string;
  @text({ optional: true, max: 4000 }) redactedInput?: string;
  @text({ optional: true, max: 4000 }) redactedOutput?: string;
  @date() startedAt!: Date;
  @date() finishedAt!: Date;
}
