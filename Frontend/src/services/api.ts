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

// Interceptor xử lý phản hồi và trích xuất thông điệp lỗi chi tiết từ FastAPI backend
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.message ||
      'Đã xảy ra lỗi không xác định';
    console.error('API Error:', message, error);
    return Promise.reject(new Error(message));
  }
);

