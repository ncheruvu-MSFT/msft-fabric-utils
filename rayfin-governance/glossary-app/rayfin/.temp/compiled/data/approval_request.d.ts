export declare class ApprovalRequest {
    id: string;
    targetType: string;
    targetId: string;
    workflowName: string;
    status: string;
    requesterSub: string;
    assigneeSub?: string;
    decisionNote?: string;
    auditCreatedAt: Date;
    decidedAt?: Date;
}
