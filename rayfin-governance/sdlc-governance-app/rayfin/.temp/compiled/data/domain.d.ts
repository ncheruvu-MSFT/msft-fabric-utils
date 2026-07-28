export declare class Domain {
    id: string;
    name: string;
    description?: string;
    type: string;
    envKey: string;
    status: string;
    parentId?: string;
    fabricWorkspace?: string;
    purviewCollection?: string;
    ownerEmail: string;
    isActive: boolean;
    auditCreatedAt: Date;
    auditUpdatedAt?: Date;
}
