export declare class Domain {
    id: string;
    name: string;
    description?: string;
    parentId?: string;
    ownerSub: string;
    isActive: boolean;
    auditCreatedAt: Date;
    auditUpdatedAt?: Date;
}
