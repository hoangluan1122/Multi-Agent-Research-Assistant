/**
 * Định nghĩa kiểu dữ liệu TypeScript (TypeScript Type Definitions) cho Frontend PaperFlow:
 * - Session: Phiên nghiên cứu khoa học.
 * - Paper & PaperAnalysis: Tài liệu bài báo và kết quả bóc tách 5 thành phần.
 * - AgentRun & WorkflowStatus: Trạng thái điều phối và lịch sử chạy của các tác tử Multi-Agent.
 * - Report, Review & Citation: Bản thảo báo cáo, thẻ điểm thẩm định và danh mục trích dẫn.
 * - SystemConfig: Cấu hình hệ thống và tham số vận hành.
 */

// ==========================================
// 1. Session Types (Phiên nghiên cứu - UC001)
// ==========================================
export interface SessionCreate {
  topic: string;
  research_question?: string;
  year_start?: number;
  year_end?: number;
  max_papers?: number;
  sources?: string[];
  citation_style?: string;
  parameters?: Record<string, any>;
}

export interface Session {
  id: string;
  topic: string;
  research_question?: string;
  parameters?: Record<string, any>;
  status: 'created' | 'searching' | 'reading' | 'summarizing' | 'drafting' | 'reviewing' | 'completed' | 'failed';
  current_step: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
  paper_count?: number;
  has_report?: boolean;
  latest_report_id?: string;
}

// ==========================================
// 2. Paper Types (Tài liệu nghiên cứu - UC002, UC004)
// ==========================================
export interface PaperAnalysis {
  id: string;
  paper_id: string;
  method?: string;
  dataset?: string;
  metrics?: string;
  results?: string;
  limitations?: string;
  summary?: string;
  raw_analysis?: Record<string, any>;
  created_at: string;
}

export interface Paper {
  id: string;
  session_id: string;
  title: string;
  authors: string[];
  abstract?: string;
  year?: number;
  venue?: string;
  doi?: string;
  url?: string;
  source: string;
  relevance_score: number;
  is_selected: boolean;
  ingestion_status: string;
  created_at: string;
  analysis?: PaperAnalysis;
}

export interface PaperSearchRequest {
  session_id: string;
  query: string;
  year_start?: number;
  year_end?: number;
  max_results?: number;
  sources?: string[];
}

// ==========================================
// 3. Agent & Workflow Types (Tác tử Multi-Agent)
// ==========================================
export interface AgentRun {
  id: string;
  session_id: string;
  agent_name: string;
  status: 'running' | 'completed' | 'failed';
  step_description?: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  error_message?: string;
  started_at: string;
  ended_at?: string;
}

export interface WorkflowStartRequest {
  session_id: string;
  auto_search?: boolean;
  auto_select_papers?: boolean;
  max_papers?: number;
  custom_outline?: string[];
}

export interface WorkflowStatus {
  session_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  current_step: string;
  current_agent?: string;
  progress_percentage: number;
  message: string;
  agent_runs: AgentRun[];
  error_message?: string;
}

// ==========================================
// 4. Report & Review Types (Báo cáo & Thẩm định - UC009, UC010)
// ==========================================
export interface Review {
  id: string;
  report_id: string;
  session_id: string;
  score: number;
  status: string;
  issues: Array<{ type?: string; description?: string; severity?: string }>;
  feedback?: string;
  hallucination_risks: Array<{ claim?: string; risk?: string; reason?: string }>;
  citation_coverage: number;
  created_at: string;
}

export interface Report {
  id: string;
  session_id: string;
  title: string;
  outline: Array<{ title: string; level: number; section_id?: string }>;
  content: string;
  comparison_table?: string;
  version: number;
  review_status: string;
  created_at: string;
  updated_at: string;
  reviews: Review[];
}

export interface Citation {
  id: string;
  session_id: string;
  paper_id: string;
  claim_text?: string;
  citation_key?: string;
  citation_text: string;
  style: string;
  is_verified: boolean;
  verification_status: string;
  created_at: string;
}

// ==========================================
// 5. System Config Types (Cấu hình hệ thống - UC013)
// ==========================================
export interface SystemConfig {
  project_name: string;
  version: string;
  environment: string;
  llm_provider: string;
  default_model: string;
  has_gemini_key: boolean;
  has_openai_key: boolean;
  qdrant_host: string;
  qdrant_use_memory: boolean;
  max_search_papers: number;
  max_review_retries: number;
}

export interface SystemConfigUpdate {
  llm_provider?: string;
  default_model?: string;
  gemini_api_key?: string;
  openai_api_key?: string;
  openai_base_url?: string;
  max_search_papers?: number;
  max_review_retries?: number;
}

