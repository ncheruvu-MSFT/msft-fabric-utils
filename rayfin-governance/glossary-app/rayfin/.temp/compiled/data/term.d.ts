export declare class Term {
    id: string;
    name: string;
    definition: string;
    domainId: string;
    status: string;
    submittedBySub: string;
    approvedBySub?: string;
    purviewQualifiedName?: string;
    auditCreatedAt: Date;
    auditUpdatedAt?: Date;
}
