/**
 * Component Thanh tiêu đề trên cùng (Application Header):
 * - Hiển thị Logo thương hiệu PaperFlow AI Multi-Agent.
 * - Hiển thị chủ đề nghiên cứu hiện tại đang mở.
 * - Báo cáo trạng thái kết nối Backend API (Online / Offline) và LLM Model đang cấu hình.
 * - Các nút thao tác nhanh: Cài đặt hệ thống (Settings), Tạo phiên nghiên cứu mới (Create Session).
 */

import React from 'react';
import {
  Sparkles,
  Settings as SettingsIcon,
  Plus,
  Server,
  Cpu,
  Menu,
} from 'lucide-react';
import type { Session, SystemConfig } from '../../types';

interface HeaderProps {
  currentSession: Session | null;
  config: SystemConfig | null;
  backendHealthy: boolean;
  onOpenCreateSession: () => void;
  onOpenSettings: () => void;
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentSession,
  config,
  backendHealthy,
  onOpenCreateSession,
  onOpenSettings,
  onToggleSidebar,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-md border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand & Sidebar toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
            title="Toggle Sessions Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-lg bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                  PaperFlow
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  AI Multi-Agent
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Current Session Topic */}
        <div className="hidden md:flex items-center max-w-md truncate px-3 py-1.5 rounded-lg bg-gray-800/40 border border-gray-800">
          <span className="text-xs text-gray-400 mr-2 shrink-0">Chủ đề hiện tại:</span>
          {currentSession ? (
            <span className="text-xs font-medium text-gray-200 truncate">
              {currentSession.topic}
            </span>
          ) : (
            <span className="text-xs text-gray-500 italic">Chưa chọn phiên nghiên cứu</span>
          )}
        </div>

        {/* Right: Status & Actions */}
        <div className="flex items-center gap-2.5">
          {/* Backend Status indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-800/60 border border-gray-800 text-xs">
            <Server className="w-3.5 h-3.5 text-gray-400" />
            <span
              className={`w-2 h-2 rounded-full ${
                backendHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-gray-300 text-[11px]">
              {backendHealthy ? 'API Online' : 'API Offline'}
            </span>
          </div>

          {/* Model indicator */}
          {config && (
            <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-800/60 border border-gray-800 text-xs">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-gray-300 font-mono text-[11px]">
                {config.llm_provider}: {config.default_model}
              </span>
            </div>
          )}

          {/* Settings button */}
          <button
            onClick={onOpenSettings}
            className="p-2 text-gray-300 hover:text-white rounded-xl bg-gray-800/60 hover:bg-gray-800 border border-gray-800 transition-colors"
            title="Cài đặt LLM & Hệ thống"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>

          {/* Create session button */}
          <button
            onClick={onOpenCreateSession}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>Tạo Session Mới</span>
          </button>
        </div>
      </div>
    </header>
  );
};
