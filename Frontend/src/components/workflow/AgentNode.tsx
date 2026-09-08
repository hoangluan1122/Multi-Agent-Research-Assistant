/**
 * Component Node Tác Tử trong Sơ đồ Luồng (Agent Node Component):
 * - Hiển thị tên tác tử, biểu tượng chuyên biệt và mô tả chức năng.
 * - Thể hiện trạng thái trực quan: Đang chạy (Hiệu ứng sóng xung), Hoàn thành (Tick xanh), Lỗi (Đỏ) hoặc Chờ (Xám).
 * - Cho phép nhấp vào để mở xem nhật ký thực thi chi tiết của Agent.
 */

import React from 'react';
import {
  Search,
  BookOpen,
  FileSpreadsheet,
  PenTool,
  CheckCircle2,
  Quote,
  Loader2,
  AlertCircle,
  Clock,
} from 'lucide-react';
import type { AgentRun } from '../../types';
import { useI18n } from '../../i18n/context';

interface AgentNodeProps {
  id?: string;
  name: string;
  label: string;
  description: string;
  currentActiveAgent?: string;
  latestRun?: AgentRun;
  onClick: () => void;
}

export const AgentNode: React.FC<AgentNodeProps> = ({
  name,
  label,
  description,
  currentActiveAgent,
  latestRun,
  onClick,
}) => {
  const { t } = useI18n();
  const runStatus = (latestRun?.status || '').toLowerCase();
  const isCurrentlyRunning = currentActiveAgent === name || runStatus === 'running';
  const isCompleted = !isCurrentlyRunning && runStatus === 'completed';
  const isFailed = !isCurrentlyRunning && runStatus === 'failed';

  const getIcon = () => {
    switch (name) {
      case 'SearchAgent':
        return <Search className="w-5 h-5" />;
      case 'ReadingAgent':
        return <BookOpen className="w-5 h-5" />;
      case 'SummarizationAgent':
        return <FileSpreadsheet className="w-5 h-5" />;
      case 'WritingAgent':
        return <PenTool className="w-5 h-5" />;
      case 'ReviewAgent':
        return <CheckCircle2 className="w-5 h-5" />;
      case 'CitationAgent':
        return <Quote className="w-5 h-5" />;
      default:
        return <Search className="w-5 h-5" />;
    }
  };

  const getStatusBorderAndBg = () => {
    if (isCurrentlyRunning) {
      return 'border-indigo-500 bg-indigo-950/40 shadow-lg shadow-indigo-500/25 animate-pulse';
    }
    if (isFailed) {
      return 'border-rose-500/50 bg-rose-950/30';
    }
    if (isCompleted) {
      return 'border-emerald-500/40 bg-emerald-950/20';
    }
    return 'border-gray-800 bg-gray-900/40 hover:border-gray-700';
  };

  const getIconColor = () => {
    if (isCurrentlyRunning) return 'text-indigo-400';
    if (isFailed) return 'text-rose-400';
    if (isCompleted) return 'text-emerald-400';
    return 'text-gray-400';
  };

  return (
    <div
      onClick={onClick}
      className={`relative flex flex-col p-4 rounded-2xl border transition-all cursor-pointer select-none group ${getStatusBorderAndBg()}`}
    >
      <div className="flex items-center justify-between gap-3 mb-2">
        <div
          className={`w-9 h-9 rounded-xl flex items-center justify-center bg-gray-800/80 border border-gray-700/50 ${getIconColor()}`}
        >
          {getIcon()}
        </div>

        {/* Status indicator */}
        <div className="flex items-center gap-1.5 text-xs">
          {isCurrentlyRunning && (
            <span className="flex items-center gap-1 text-indigo-400 font-semibold text-[11px]">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {t.statusInProgress}
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-1 text-emerald-400 font-medium text-[11px]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {t.statusDone}
            </span>
          )}
          {isFailed && (
            <span className="flex items-center gap-1 text-rose-400 font-medium text-[11px]">
              <AlertCircle className="w-3.5 h-3.5" />
              {t.statusError}
            </span>
          )}
          {!latestRun && !isCurrentlyRunning && (
            <span className="flex items-center gap-1 text-gray-500 text-[11px]">
              <Clock className="w-3.5 h-3.5" />
              {t.statusWaiting}
            </span>
          )}
        </div>
      </div>

      <h4 className="text-sm font-semibold text-gray-200 group-hover:text-white transition-colors">
        {label}
      </h4>
      <p className="text-xs text-gray-400 mt-1 line-clamp-2">{description}</p>

      {latestRun && (
        <div className="mt-3 pt-2 border-t border-gray-800/80 flex items-center justify-between text-[10px] text-gray-500">
          <span>Log: #{latestRun.id.substring(0, 6)}</span>
          <span className="text-indigo-400 group-hover:underline">{t.logDetail}</span>
        </div>
      )}
    </div>
  );
};
