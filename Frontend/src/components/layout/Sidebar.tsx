/**
 * Component Thanh điều hướng bên (Sidebar Navigation):
 * - Hiển thị danh sách các phiên nghiên cứu đã tạo (Sessions List).
 * - Tìm kiếm, lọc nhanh phiên theo từ khóa trong chủ đề hoặc câu hỏi.
 * - Hiển thị trạng thái hoàn thành / đang xử lý của từng phiên bằng Badge.
 * - Hỗ trợ thao tác chuyển đổi phiên, tạo mới và xóa bỏ phiên nghiên cứu.
 */

import React, { useState } from 'react';
import {
  FolderOpen,
  Plus,
  Trash2,
  FileText,
  Clock,
  Search,
  Layers,
  X,
} from 'lucide-react';
import type { Session } from '../../types';
import { Badge } from '../common/Badge';
import { useI18n } from '../../i18n/context';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  isOpen: boolean;
  onSelectSession: (session: Session) => void;
  onCreateSession: () => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  isOpen,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onCloseMobile,
}) => {
  const { language, t } = useI18n();
  const [filterQuery, setFilterQuery] = useState('');

  const filteredSessions = sessions.filter(
    (s) =>
      s.topic.toLowerCase().includes(filterQuery.toLowerCase()) ||
      (s.research_question &&
        s.research_question.toLowerCase().includes(filterQuery.toLowerCase()))
  );

  const getStatusBadge = (status: string) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'completed':
        return <Badge variant="success">{t.statusCompleted}</Badge>;
      case 'failed':
        return <Badge variant="danger">{t.statusFailed}</Badge>;
      case 'created':
      case 'ready':
        return <Badge variant="neutral">{t.statusCreated}</Badge>;
      default:
        return <Badge variant="info">{t.statusProcessing}</Badge>;
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(language === 'vi' ? 'vi-VN' : 'en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:static top-16 bottom-0 left-0 z-40 w-80 bg-gray-900/95 lg:bg-gray-900/50 backdrop-blur-md border-r border-gray-800 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Top Action & Search */}
        <div className="p-4 border-b border-gray-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              <FolderOpen className="w-4 h-4 text-indigo-400" />
              <span>{t.researchSessions} ({sessions.length})</span>
            </div>
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1 text-gray-400 hover:text-white rounded"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <button
            onClick={onCreateSession}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-gray-800 hover:bg-gray-750 text-indigo-300 hover:text-white text-xs font-medium border border-gray-700/60 hover:border-indigo-500/40 transition-all shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>{t.createSessionBtn}</span>
          </button>

          {/* Search bar */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-gray-500" />
            <input
              type="text"
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              placeholder={t.searchSessionsPlaceholder}
              className="w-full bg-gray-800/60 text-xs text-gray-200 pl-8 pr-3 py-1.5 rounded-lg border border-gray-700/50 focus:border-indigo-500 focus:outline-none placeholder-gray-500 transition-colors"
            />
          </div>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-2">
          {filteredSessions.length === 0 ? (
            <div className="text-center py-10 px-4">
              <Layers className="w-8 h-8 text-gray-600 mx-auto mb-2" />
              <p className="text-xs text-gray-400">
                {filterQuery ? t.noSessionsFound : t.noSessionsYet}
              </p>
            </div>
          ) : (
            filteredSessions.map((session) => {
              const isActive = session.id === activeSessionId;
              return (
                <div
                  key={session.id}
                  onClick={() => {
                    onSelectSession(session);
                    onCloseMobile();
                  }}
                  className={`group relative p-3 rounded-xl border cursor-pointer transition-all ${
                    isActive
                      ? 'bg-indigo-950/40 border-indigo-500/50 shadow-md shadow-indigo-900/20'
                      : 'bg-gray-800/30 hover:bg-gray-800/70 border-gray-800/80 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4
                      className={`text-xs font-semibold line-clamp-2 ${
                        isActive ? 'text-indigo-200' : 'text-gray-200 group-hover:text-white'
                      }`}
                    >
                      {session.topic}
                    </h4>
                    <button
                      onClick={(e) => onDeleteSession(session.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 text-gray-500 hover:text-rose-400 rounded hover:bg-gray-700/50 transition-all shrink-0"
                      title={t.deleteSessionTitle}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {session.research_question && (
                    <p className="text-[11px] text-gray-400 line-clamp-1 mt-1">
                      {session.research_question}
                    </p>
                  )}

                  <div className="flex items-center justify-between gap-2 mt-2.5 pt-2 border-t border-gray-800/60 text-[10px] text-gray-400">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3 h-3 text-gray-500" />
                      <span>{formatDate(session.created_at)}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {session.paper_count !== undefined && session.paper_count > 0 && (
                        <span className="flex items-center gap-1 text-gray-400">
                          <FileText className="w-3 h-3 text-indigo-400" />
                          {session.paper_count}
                        </span>
                      )}
                      {getStatusBadge(session.status)}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </>
  );
};
