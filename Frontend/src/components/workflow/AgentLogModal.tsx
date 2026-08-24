/**
 * Component Modal Xem Chi Tiết Nhật Ký Thực Thi của Tác Tử (Agent Log Modal):
 * - Hiển thị Input Data và Output Data dạng JSON có định dạng.
 * - Xem thông tin lỗi (Error message) và thời gian thực thi nếu có.
 * - Hỗ trợ nút sao chép nhanh dữ liệu JSON vào Clipboard.
 */

import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import type { AgentRun } from '../../types';
import { Badge } from '../common/Badge';
import { Copy, Check, Terminal, Clock } from 'lucide-react';

interface AgentLogModalProps {
  run: AgentRun | null;
  isOpen: boolean;
  onClose: () => void;
}

export const AgentLogModal: React.FC<AgentLogModalProps> = ({ run, isOpen, onClose }) => {
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  if (!run) return null;

  const copyToClipboard = (text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const getStatusBadge = () => {
    switch (run.status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'failed':
        return <Badge variant="danger">Failed</Badge>;
      case 'running':
        return <Badge variant="info">Running</Badge>;
      default:
        return <Badge variant="neutral">{run.status}</Badge>;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Nhật ký Agent: ${run.agent_name}`}
      subtitle={`Run ID: ${run.id} • ${run.step_description || 'Không có mô tả'}`}
      maxWidth="4xl"
    >
      <div className="space-y-4 text-xs">
        {/* Status & Time */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-gray-800/60 border border-gray-700/50">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Trạng thái:</span>
            {getStatusBadge()}
          </div>
          <div className="flex items-center gap-4 text-gray-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-gray-500" /> Bắt đầu: {new Date(run.started_at).toLocaleTimeString('vi-VN')}
            </span>
            {run.ended_at && (
              <span>Kết thúc: {new Date(run.ended_at).toLocaleTimeString('vi-VN')}</span>
            )}
          </div>
        </div>

        {/* Error message if any */}
        {run.error_message && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300">
            <p className="font-semibold mb-1">Lỗi thực thi:</p>
            <p className="font-mono text-xs">{run.error_message}</p>
          </div>
        )}

        {/* Input Data */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-indigo-400" /> Input Payload
            </span>
            <button
              onClick={() => copyToClipboard(JSON.stringify(run.input_data, null, 2), 'input')}
              className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-indigo-300"
            >
              {copiedSection === 'input' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copiedSection === 'input' ? 'Đã sao chép' : 'Sao chép JSON'}
            </button>
          </div>
          <pre className="p-3.5 rounded-xl bg-gray-950 border border-gray-800 text-gray-300 font-mono text-[11px] overflow-x-auto max-h-48 custom-scrollbar">
            {JSON.stringify(run.input_data, null, 2)}
          </pre>
        </div>

        {/* Output Data */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-emerald-400" /> Output Result
            </span>
            <button
              onClick={() => copyToClipboard(JSON.stringify(run.output_data, null, 2), 'output')}
              className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-indigo-300"
            >
              {copiedSection === 'output' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              {copiedSection === 'output' ? 'Đã sao chép' : 'Sao chép JSON'}
            </button>
          </div>
          <pre className="p-3.5 rounded-xl bg-gray-950 border border-gray-800 text-gray-300 font-mono text-[11px] overflow-x-auto max-h-64 custom-scrollbar">
            {JSON.stringify(run.output_data, null, 2)}
          </pre>
        </div>
      </div>
    </Modal>
  );
};
