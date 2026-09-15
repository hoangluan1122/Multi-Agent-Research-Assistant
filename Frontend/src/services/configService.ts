/**
 * Service giao tiếp API Cấu hình hệ thống (UC013):
 * - Lấy cấu hình hệ thống hiện tại (getConfig).
 * - Cập nhật thông số mô hình LLM, API Key, Quota (updateConfig).
 * - Kiểm tra kết nối LLM (testLlm).
 */

import { apiClient } from './api';
import type { SystemConfig, SystemConfigUpdate, TestLlmRequest } from '../types';

// @trace: REQ-011, REQ-012, REQ-041, REQ-042
export const configService = {
  /** Lấy thông tin cấu hình hệ thống từ máy chủ */
  async getConfig(): Promise<SystemConfig> {
    const response = await apiClient.get<SystemConfig>('/api/v1/config');
    return response.data;
  },

  /** Cập nhật thông số cấu hình và khóa API */
  async updateConfig(params: SystemConfigUpdate): Promise<SystemConfig> {
    const response = await apiClient.put<SystemConfig>('/api/v1/config', params);
    return response.data;
  },

  /** Gửi yêu cầu kiểm tra kết nối với LLM Provider (hỗ trợ kiểm tra động thông số form đang nhập) */
  async testLlm(payload?: TestLlmRequest): Promise<{ status: string; message: string; response?: string }> {
    const response = await apiClient.post<{ status: string; message: string; response?: string }>(
      '/api/v1/config/test-llm',
      payload || {}
    );
    return response.data;
  },
};

