/**
 * Component Modal Danh Mục Trích Dẫn (Citation List Modal - UC008):
 * - Hiển thị toàn bộ danh sách trích dẫn đã chuẩn hóa theo quy chuẩn IEEE/APA.
 * - Hiển thị trạng thái xác thực nguồn (VERIFIED / UNVERIFIED).
 * - Cung cấp nút sao chép trích dẫn nhanh vào Clipboard.
 */

import React from 'react';
import { Modal } from '../common/Modal';
import type { Citation } from '../../types';
import { Copy, Check } from 'lucide-react';
import { Badge } from '../common/Badge';

interface CitationListModalProps {
  citations: Citation[];
  isOpen: boolean;
  onClose: () => void;
}

export const CitationListModal: React.FC<CitationListModalProps> = ({
  citations,
  isOpen,
  onClose,
}) => {
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const copyCitation = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Danh Mục Trích Dẫn Đã Xác Thực (Citation Agent)"
      subtitle={`Tổng cộng ${citations.length} nguồn trích dẫn được liên kết chính xác với các luận điểm`}
      maxWidth="4xl"
    >
      <div className="space-y-3">
        {citations.length === 0 ? (
          <p className="text-xs text-gray-500 py-6 text-center">
            Chưa có trích dẫn nào được khởi tạo cho báo cáo này.
          </p>
        ) : (
          citations.map((c) => (
            <div
              key={c.id}
              className="p-4 rounded-xl bg-gray-800/40 border border-gray-700/60 space-y-2 text-xs"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[11px] font-bold">
                    {c.citation_key || `[${c.style}]`}
                  </span>
                  <Badge variant={c.is_verified ? 'success' : 'warning'}>
                    {c.is_verified ? 'Đã xác thực nguồn' : 'Chưa xác thực'}
                  </Badge>
                </div>

                <button
                  onClick={() => copyCitation(c.citation_text, c.id)}
                  className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-indigo-300 transition-colors"
                >
                  {copiedId === c.id ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                  <span>{copiedId === c.id ? 'Đã chép' : 'Sao chép'}</span>
                </button>
              </div>

              {/* Formatted Citation */}
              <p className="text-gray-200 font-medium leading-relaxed pl-2 border-l-2 border-indigo-500/50">
                {c.citation_text}
              </p>

              {/* Claim context */}
              {c.claim_text && (
                <div className="pt-2 border-t border-gray-800/80 text-[11px] text-gray-400">
                  <span className="text-gray-500 font-semibold">Luận điểm tương ứng:</span>{' '}
                  <span className="italic">"{c.claim_text}"</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </Modal>
  );
};
