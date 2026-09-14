/**
 * Service giao tiếp API Quản lý tài liệu nghiên cứu (UC002, UC003, UC004, UC005):
 * - Tìm kiếm bài báo học thuật từ ArXiv/Semantic Scholar (searchPapers).
 * - Lấy danh sách bài báo của phiên (getSessionPapers).
 * - Kích hoạt đọc sâu và bóc tách cấu trúc (analyzePaper).
 * - Cập nhật chọn lọc bài báo tham gia báo cáo (updatePaperSelection).
 * - Tải lên tệp PDF bài báo (uploadPaper).
 */

import { apiClient } from './api';
import type { Paper, PaperSearchRequest } from '../types';

export const paperService = {
  /** Tìm kiếm bài báo học thuật trực tuyến */
  async searchPapers(params: PaperSearchRequest): Promise<Paper[]> {
    const response = await apiClient.post<Paper[]>('/api/v1/papers/search', params);
    return response.data;
  },

  /** Lấy danh sách toàn bộ bài báo trong một phiên nghiên cứu */
  async getSessionPapers(sessionId: string): Promise<Paper[]> {
    const response = await apiClient.get<Paper[]>(`/api/v1/papers/session/${sessionId}`);
    return response.data;
  },

  /** Lấy thông tin chi tiết của một bài báo */
  async getPaper(paperId: string): Promise<Paper> {
    const response = await apiClient.get<Paper>(`/api/v1/papers/${paperId}`);
    return response.data;
  },

  /** Kích hoạt ReadingAgent phân tích sâu cấu trúc cho bài báo */
  async analyzePaper(paperId: string): Promise<Paper> {
    const response = await apiClient.post<Paper>(`/api/v1/papers/${paperId}/analyze`);
    return response.data;
  },

  /** Cập nhật trạng thái chọn lọc bài báo (is_selected) */
  async updatePaperSelection(paperIds: string[], isSelected: boolean = true): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/api/v1/papers/selection', {
      paper_ids: paperIds,
      is_selected: isSelected,
    });
    return response.data;
  },

  /** Tải lên file PDF trực tiếp từ máy tính người dùng */
  async uploadPaper(sessionId: string, file: File): Promise<Paper> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);

    const response = await apiClient.post<Paper>('/api/v1/papers/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /** Dịch tiêu đề và tóm tắt của một bài báo sang Tiếng Việt */
  async translatePaper(paperId: string): Promise<Paper> {
    const response = await apiClient.post<Paper>(`/api/v1/papers/${paperId}/translate`);
    return response.data;
  },

  /** Dịch toàn bộ bài báo trong một phiên sang Tiếng Việt */
  async translateAllPapers(sessionId: string): Promise<Paper[]> {
    const response = await apiClient.post<Paper[]>(`/api/v1/papers/session/${sessionId}/translate-all`);
    return response.data;
  },
};

