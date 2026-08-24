/**
 * Service giao tiếp API Điều phối Multi-Agent Workflow:
 * - Kích hoạt chạy quy trình Multi-Agent tự động nền (startWorkflow).
 * - Lấy trạng thái tiến độ và lịch sử chạy của từng tác tử (getWorkflowStatus).
 */

import { apiClient } from './api';
import type { WorkflowStartRequest, WorkflowStatus } from '../types';

export const workflowService = {
  /** Kích hoạt chạy toàn bộ luồng tác tử Multi-Agent cho một phiên */
  async startWorkflow(params: WorkflowStartRequest): Promise<{ status: string; message: string; session_id: string }> {
    const response = await apiClient.post<{ status: string; message: string; session_id: string }>(
      '/api/v1/workflow/start',
      params
    );
    return response.data;
  },

  /** Tra cứu trạng thái tiến độ thực thi của quy trình */
  async getWorkflowStatus(sessionId: string): Promise<WorkflowStatus> {
    const response = await apiClient.get<WorkflowStatus>(`/api/v1/workflow/status/${sessionId}`);
    return response.data;
  },
};

