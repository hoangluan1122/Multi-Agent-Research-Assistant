/**
 * Cấu hình Tailwind CSS cho giao diện người dùng PaperFlow.
 * Quét các tệp HTML, TSX, JSX trong thư mục src để sinh CSS tối ưu.
 * @type {import('tailwindcss').Config}
 */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

