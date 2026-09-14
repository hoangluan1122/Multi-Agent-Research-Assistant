// @trace: REQ-023
/**
 * Phân giải liên kết trực tiếp tới bài báo khoa học hoặc tài liệu PDF toàn văn.
 * - Ưu tiên mở PDF trực tiếp nếu có (pdf_path).
 * - Tự động chuyển đổi các liên kết arXiv abstract dạng /abs/ sang /pdf/ kèm đuôi .pdf
 * - Giữ nguyên DOI URL (https://doi.org/...) hoặc trang của nhà xuất bản nếu là nguồn chính thức.
 */
export function getDirectPaperUrl(paper: { url?: string; pdf_path?: string | null }): string {
  if (paper.pdf_path && (paper.pdf_path.startsWith('http://') || paper.pdf_path.startsWith('https://'))) {
    return paper.pdf_path;
  }

  if (paper.url) {
    let cleanUrl = paper.url.trim();
    if (cleanUrl.startsWith('http://')) {
      cleanUrl = cleanUrl.replace('http://', 'https://');
    }

    // Nếu là arXiv /abs/ -> Chuyển thành direct PDF viewer
    if (cleanUrl.includes('arxiv.org/abs/')) {
      let pdfUrl = cleanUrl.replace('/abs/', '/pdf/');
      if (!pdfUrl.endsWith('.pdf')) {
        pdfUrl = `${pdfUrl}.pdf`;
      }
      return pdfUrl;
    }

    return cleanUrl;
  }

  return paper.pdf_path || '#';
}

/**
 * Kiểm tra xem URL đích có phải là file PDF hay không
 */
export function isPdfUrl(url: string): boolean {
  if (!url || url === '#') return false;
  const lower = url.toLowerCase();
  return lower.includes('.pdf') || lower.includes('/pdf/') || lower.includes('blobtype=pdf');
}
