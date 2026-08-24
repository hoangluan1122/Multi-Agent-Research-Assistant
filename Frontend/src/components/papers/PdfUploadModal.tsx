/**
 * Component Modal Tải lên Tài liệu PDF (PDF Upload Modal - UC003):
 * - Hỗ trợ kéo thả tệp (Drag and Drop) hoặc chọn tệp qua nút duyệt.
 * - Kiểm tra định dạng .pdf trước khi gửi lên máy chủ.
 * - Hiển thị trạng thái tải lên và xử lý phân tích tài liệu.
 */

import React, { useState, useRef } from 'react';
import { Modal } from '../common/Modal';
import { UploadCloud, Loader2, CheckCircle2 } from 'lucide-react';

interface PdfUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<void>;
}

export const PdfUploadModal: React.FC<PdfUploadModalProps> = ({
  isOpen,
  onClose,
  onUpload,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
        setSelectedFile(file);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Tải Lên File PDF Bài Báo"
      subtitle="Thêm tài liệu nghiên cứu của riêng bạn vào phiên làm việc"
      maxWidth="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="file"
          accept=".pdf"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`p-8 border-2 border-dashed rounded-2xl text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-3 ${
            isDragOver
              ? 'border-indigo-500 bg-indigo-950/30'
              : 'border-gray-700 hover:border-indigo-500/50 bg-gray-800/40 hover:bg-gray-800/70'
          }`}
        >
          <div className="w-12 h-12 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center">
            <UploadCloud className="w-6 h-6" />
          </div>

          {selectedFile ? (
            <div className="space-y-1">
              <p className="text-xs font-semibold text-emerald-400 flex items-center justify-center gap-1.5">
                <CheckCircle2 className="w-4 h-4" /> {selectedFile.name}
              </p>
              <p className="text-[11px] text-gray-400">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              <p className="text-xs font-medium text-gray-200">
                Kéo thả file PDF vào đây hoặc <span className="text-indigo-400 underline">chọn từ máy tính</span>
              </p>
              <p className="text-[10px] text-gray-500">Chỉ chấp nhận file .PDF (Tối đa 50MB)</p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            Hủy
          </button>
          <button
            type="submit"
            disabled={!selectedFile || loading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Đang tải lên & trích xuất...</span>
              </>
            ) : (
              <span>Tải lên ngay</span>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
