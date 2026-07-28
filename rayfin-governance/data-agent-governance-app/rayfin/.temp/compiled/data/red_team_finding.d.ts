export declare class RedTeamFinding {
    id: string;
    agentId: string;
    severity: string;
    category: string;
    title: string;
    description: string;
    status: string;
    reporterSub: string;
    assigneeSub?: string;
    mitigationNote?: string;
    reportedAt: Date;
    resolvedAt?: Date;
}
