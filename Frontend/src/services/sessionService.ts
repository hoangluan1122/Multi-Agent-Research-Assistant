/**
 * Service giao tiếp API Phiên nghiên cứu (UC001):
 * - Lấy danh sách các phiên nghiên cứu (getSessions).
 * - Lấy thông tin chi tiết một phiên (getSession).
 * - Khởi tạo phiên nghiên cứu mới (createSession).
 * - Xóa phiên nghiên cứu (deleteSession).
 */

import { apiClient } from './api';
import type { Session, SessionCreate } from '../types';

export const sessionService = {
  /** Lấy danh sách các phiên nghiên cứu gần nhất */
  async getSessions(): Promise<Session[]> {
    const response = await apiClient.get<Session[]>('/api/v1/sessions');
    return response.data;
  },

  /** Lấy chi tiết thông tin một phiên theo ID */
  async getSession(id: string): Promise<Session> {
    const response = await apiClient.get<Session>(`/api/v1/sessions/${id}`);
    return response.data;
  },

  /** Tạo một phiên nghiên cứu mới với chủ đề và câu hỏi */
  async createSession(data: SessionCreate): Promise<Session> {
    const response = await apiClient.post<Session>('/api/v1/sessions', data);
    return response.data;
  },

  /** Xóa phiên nghiên cứu khỏi cơ sở dữ liệu */
  async deleteSession(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/sessions/${id}`);
  },

  /** REQ-008: Kiểm tra hạn mức dùng thử còn lại của khách */
  async getGuestQuota(): Promise<{ is_logged_in: boolean; used: number; max: number; remaining: number; is_exceeded: boolean }> {
    const response = await apiClient.get('/api/v1/sessions/guest/quota');
    return response.data;
  },
};

