export declare class LineageEdge {
    id: string;
    sourceQname: string;
    sourceType: string;
    targetQname: string;
    targetType: string;
    processName: string;
    processType: string;
    artifactRef: string;
    harvestedBySub: string;
    columnsJson?: string;
    extraJson?: string;
    harvestedAt: Date;
}
