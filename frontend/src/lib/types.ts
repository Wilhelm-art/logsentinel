/* ── API Types ── */

export type TaskStatus =
  | "pending"
  | "parsing"
  | "sanitizing"
  | "enriching"
  | "llm_analysis"
  | "completed"
  | "failed";

export type SeverityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export interface UploadResponse {
  task_id: string;
  status: string;
  message: string;
  file_hash: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  progress_stage: string;
  created_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface Incident {
  severity: SeverityLevel;
  attack_type: string;
  target_endpoint: string;
  actor_hash: string;
  description: string;
}

export interface SecurityReport {
  summary: string;
  incidents: Incident[];
  waf_rule_suggestions: string[];
}

export interface ReportResponse {
  task_id: string;
  timestamp: string;
  original_filename: string;
  file_hash: string;
  log_format?: string;
  line_count?: number;
  sampled?: number;
  llm_provider?: string;
  llm_model?: string;
  processing_time_seconds?: number;
  report: SecurityReport;
}

export interface HistoryItem {
  task_id: string;
  status: TaskStatus;
  original_filename: string;
  file_hash: string;
  log_format?: string;
  line_count?: number;
  created_at: string;
  completed_at?: string;
  incident_count?: number;
  top_severity?: string;
}
