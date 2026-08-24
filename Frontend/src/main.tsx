/**
 * Điểm khởi chạy chính (Entry Point) của ứng dụng React PaperFlow.
 * Gắn kết component gốc <App /> vào thẻ DOM '#root' với chế độ StrictMode.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

