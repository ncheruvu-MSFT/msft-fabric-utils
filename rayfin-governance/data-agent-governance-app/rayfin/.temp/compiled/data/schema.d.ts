import { Agent } from './agent.js';
import { Tool } from './tool.js';
import { PromptTemplate } from './prompt_template.js';
import { RunLog } from './run_log.js';
import { RedTeamFinding } from './red_team_finding.js';
export declare const schema: {
    Agent: typeof Agent;
    Tool: typeof Tool;
    PromptTemplate: typeof PromptTemplate;
    RunLog: typeof RunLog;
    RedTeamFinding: typeof RedTeamFinding;
};
