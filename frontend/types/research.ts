/**
 * Research-related TypeScript types.
 */

export type ResearchStatus =
  | "created"
  | "clarifying"
  | "planning"
  | "ready"
  | "executing"
  | "synthesizing"
  | "complete"
  | "error";

export interface ResearchTask {
  source: string;
  description: string;
  query: string;
  expected_output: string;
  status: string;
}

export interface ResearchPhase {
  name: string;
  description: string;
  estimated_time_minutes: number;
  tasks: ResearchTask[];
  status: string;
}

export interface ResearchPlan {
  title: string;
  objective: string;
  estimated_time_minutes: number;
  phases: ResearchPhase[];
  deliverables: string[];
}

export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ResearchSession {
  id: string;
  query: string;
  status: ResearchStatus;
  created_at: string;
  updated_at?: string;
  messages: Message[];
  plan?: ResearchPlan;
  has_results: boolean;
  has_report: boolean;
  error?: string;
}

export interface Visualization {
  type: "bar_chart" | "line_chart" | "pie_chart" | "table" | "metric" | "area_chart";
  title: string;
  description: string;
  data: Record<string, unknown>;
}

export interface ReportSection {
  title: string;
  content: string;
  visualizations: Visualization[];
  citations: string[];
}

export interface Report {
  id: string;
  title: string;
  executive_summary: string;
  sections: ReportSection[];
  key_findings: string[];
  recommendations: string[];
  generated_at: string;
  metadata: Record<string, unknown>;
}

// SSE Event Types
export interface ChatDeltaEvent {
  type: "chat_delta";
  content: string;
}

export interface StatusChangeEvent {
  type: "status_change";
  status: ResearchStatus;
}

export interface PlanningStartEvent {
  type: "planning_start";
  message: string;
}

export interface PlanReadyEvent {
  type: "plan_ready";
  plan: ResearchPlan;
}

export interface ExecutionStartEvent {
  type: "execution_start";
  total_phases: number;
}

export interface PhaseStartEvent {
  type: "phase_start";
  phase_index: number;
  phase_name: string;
  tasks: string[];
}

export interface TaskCompleteEvent {
  type: "task_complete";
  phase_index: number;
  task: string;
  success: boolean;
  result_count: number;
}

export interface PhaseCompleteEvent {
  type: "phase_complete";
  phase_index: number;
}

export interface SynthesisStartEvent {
  type: "synthesis_start";
}

export interface ReportReadyEvent {
  type: "report_ready";
  report: Report;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type SSEEvent =
  | ChatDeltaEvent
  | StatusChangeEvent
  | PlanningStartEvent
  | PlanReadyEvent
  | ExecutionStartEvent
  | PhaseStartEvent
  | TaskCompleteEvent
  | PhaseCompleteEvent
  | SynthesisStartEvent
  | ReportReadyEvent
  | ErrorEvent;
