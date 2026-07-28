export declare class AttestationRun {
    id: string;
    workspaceId: string;
    policyName: string;
    result: string;
    pipelineRunUrl: string;
    commitSha: string;
    submittedBySub: string;
    findingsJson?: string;
    runAt: Date;
}
