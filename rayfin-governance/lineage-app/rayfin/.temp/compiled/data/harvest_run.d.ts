export declare class HarvestRun {
    id: string;
    harvesterType: string;
    status: string;
    edgeCount: number;
    triggeredBySub: string;
    errorMessage?: string;
    startedAt: Date;
    finishedAt?: Date;
}
