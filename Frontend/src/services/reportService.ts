/**
 * Service giao tiếp API Báo cáo & Xuất bản (UC009, UC010, UC012):
 * - Lấy danh sách báo cáo theo phiên (getSessionReports).
 * - Lấy chi tiết nội dung bản thảo báo cáo (getReport).
 * - Lấy danh mục trích dẫn học thuật gắn liền (getReportCitations).
 * - Xuất bản báo cáo ra file Markdown, DOCX hoặc PDF (exportReport).
 */

import { apiClient } from './api';
import type { Report, Citation } from '../types';

export const reportService = {
  /** Lấy danh sách toàn bộ các phiên bản báo cáo của một phiên */
  async getSessionReports(sessionId: string): Promise<Report[]> {
    const response = await apiClient.get<Report[]>(`/api/v1/reports/session/${sessionId}`);
    return response.data;
  },

  /** Lấy chi tiết nội dung bản thảo báo cáo và lịch sử review */
  async getReport(reportId: string): Promise<Report> {
    const response = await apiClient.get<Report>(`/api/v1/reports/${reportId}`);
    return response.data;
  },

  /** Lấy danh sách trích dẫn tham khảo chuẩn hóa liên kết với báo cáo */
  async getReportCitations(reportId: string): Promise<Citation[]> {
    const response = await apiClient.get<Citation[]>(`/api/v1/reports/${reportId}/citations`);
    return response.data;
  },

  /** Xuất bản file báo cáo theo định dạng lựa chọn (Markdown, DOCX, PDF) */
  async exportReport(reportId: string, format: 'markdown' | 'docx' | 'pdf'): Promise<Blob> {
    const response = await apiClient.post(
      `/api/v1/reports/${reportId}/export`,
      { format, include_citations: true, include_comparison_table: true },
      { responseType: 'blob' }
    );
    return response.data;
  },
};

