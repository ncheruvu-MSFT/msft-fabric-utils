export declare class Agent {
    id: string;
    name: string;
    description: string;
    domainId: string;
    ownerSub: string;
    status: string;
    modelDeployment: string;
    requiresHumanApproval: boolean;
    auditCreatedAt: Date;
    auditUpdatedAt?: Date;
}
