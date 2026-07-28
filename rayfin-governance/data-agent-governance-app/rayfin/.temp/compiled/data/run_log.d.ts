export declare class RunLog {
    id: string;
    agentId: string;
    promptTemplateId: string;
    callerSub: string;
    status: string;
    inputTokens: number;
    outputTokens: number;
    toolCallsJson?: string;
    redactedInput?: string;
    redactedOutput?: string;
    startedAt: Date;
    finishedAt: Date;
}
