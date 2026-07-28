export declare class InfraRequest {
    id: string;
    requestType: string;
    displayName: string;
    environment: string;
    domain?: string;
    capacitySku?: string;
    region?: string;
    targetCapacity?: string;
    justification: string;
    costCenter?: string;
    status: string;
    approverSub?: string;
    approvalNote?: string;
    githubIssueUrl?: string;
    githubIssueNumber?: number;
    ownerSub: string;
    auditCreatedBy: string;
    auditCreatedAt: Date;
    auditUpdatedAt?: Date;
}
