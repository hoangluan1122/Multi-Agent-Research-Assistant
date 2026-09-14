/**
 * Module cấu hình Axios HTTP Client tập trung:
 * - Thiết lập Base URL, timeout 60 giây, Content-Type JSON.
 * - Đăng ký Response Interceptor để chuẩn hóa và bắt lỗi API thống nhất.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
});

// Interceptor tự động đính kèm JWT Bearer Token nếu người dùng đã đăng nhập
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('paperflow_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// @trace: REQ-011
// Interceptor xử lý phản hồi và trích xuất thông điệp lỗi chi tiết từ FastAPI backend
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'Đã xảy ra lỗi không xác định';
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail
        .map((d: any) => (typeof d === 'object' && d ? d.msg || d.message || JSON.stringify(d) : String(d)))
        .join('; ');
    } else if (detail && typeof detail === 'object') {
      message = detail.msg || detail.message || JSON.stringify(detail);
    } else if (error.message) {
      message = error.message;
    }

    console.error('API Error:', message, error);
    return Promise.reject(new Error(message));
  }
);


