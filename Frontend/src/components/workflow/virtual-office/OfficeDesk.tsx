// @trace: REQ-VO-002, REQ-VO-003, REQ-VO-005
import React from 'react';
import type { AgentRun } from '../../../types';
import { AgentCharacter, type CharacterStatus } from './AgentCharacter';
import { Coffee, Terminal, CheckCircle2, AlertCircle, Clock, Loader2, ExternalLink } from 'lucide-react';
import './officeTheme.css';

interface OfficeDeskProps {
  id: string;
  name: string;
  label: string;
  description: string;
  currentActiveAgent?: string;
  latestRun?: AgentRun;
  onClick: () => void;
}

export const OfficeDesk: React.FC<OfficeDeskProps> = ({
  name,
  label,
  description,
  currentActiveAgent,
  latestRun,
  onClick,
}) => {
  const runStatus = (latestRun?.status || '').toLowerCase();
  const isCurrentlyRunning = currentActiveAgent === name || runStatus === 'running';
  const isCompleted = !isCurrentlyRunning && runStatus === 'completed';
  const isFailed = !isCurrentlyRunning && runStatus === 'failed';

  const characterStatus: CharacterStatus = isCurrentlyRunning
    ? 'running'
    : isCompleted
    ? 'completed'
    : isFailed
    ? 'failed'
    : 'idle';

  // Screen terminal text depending on agent and state
  const getTerminalSnippet = () => {
    if (isCurrentlyRunning) {
      return '> RUNNING AI AGENT...';
    }
    if (isCompleted) {
      return '> 100% SUCCESS PASS';
    }
    if (isFailed) {
      return '> ERROR TRACEBACK';
    }
    return '> IDLE STANDBY...';
  };

  return (
    <div
      onClick={onClick}
      className={`relative group cursor-pointer p-4 rounded-3xl border transition-all duration-300 flex flex-col items-center select-none ${
        isCurrentlyRunning
          ? 'bg-slate-900/90 border-indigo-500 shadow-2xl shadow-indigo-500/20 ring-2 ring-indigo-500/40'
          : isCompleted
          ? 'bg-slate-900/70 border-emerald-500/30 hover:border-emerald-500/60 shadow-lg'
          : isFailed
          ? 'bg-slate-900/70 border-rose-500/30 hover:border-rose-500/60'
          : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 shadow-md'
      }`}
    >
      {/* Desk Status Glow in Background */}
      {isCurrentlyRunning && (
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent pointer-events-none anim-desk-pulse" />
      )}

      {/* Top Label & Badge */}
      <div className="w-full flex items-center justify-between gap-2 mb-2 z-10">
        <span className="text-xs font-bold text-gray-200 group-hover:text-white transition-colors truncate">
          {label}
        </span>
        <div className="flex items-center gap-1">
          {isCurrentlyRunning && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-950/90 border border-indigo-500/50 text-[10px] text-indigo-300 font-semibold">
              <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
              Đang chạy
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/40 text-[10px] text-emerald-300 font-medium">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              Hoàn tất
            </span>
          )}
          {isFailed && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-950/80 border border-rose-500/40 text-[10px] text-rose-300 font-medium">
              <AlertCircle className="w-3 h-3 text-rose-400" />
              Lỗi
            </span>
          )}
          {!isCurrentlyRunning && !isCompleted && !isFailed && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800/80 text-[10px] text-gray-400 font-normal">
              <Clock className="w-3 h-3 text-gray-500" />
              Chờ
            </span>
          )}
        </div>
      </div>

      {/* Computer Desk Area (Clean Modern Isometric Office Layout) */}
      <div className="relative w-full flex flex-col items-center justify-center my-2">
        {/* 1. Mascot Character Sitting at the Desk (Behind) */}
        <div className="relative z-10 -mb-4">
          <AgentCharacter agentName={name} status={characterStatus} currentTask={description} />
        </div>

        {/* 2. Desk Surface (Table with Laptop/Monitor on Top) */}
        <div className="relative z-20 w-full rounded-2xl bg-gradient-to-b from-slate-700 via-slate-800 to-slate-900 border border-slate-600/60 shadow-xl p-3 flex flex-col items-center gap-2">
          {/* Monitor Screen on Desk */}
          <div
            className={`w-full h-16 rounded-xl p-2 flex flex-col justify-between border transition-all duration-300 ${
              isCurrentlyRunning
                ? 'bg-slate-950 border-indigo-400 shadow-lg anim-screen-glow'
                : isCompleted
                ? 'bg-slate-950 border-emerald-500/50'
                : isFailed
                ? 'bg-slate-950 border-rose-500/50'
                : 'bg-slate-950 border-slate-800'
            }`}
          >
            {/* Screen Header */}
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-1">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              </div>
              <span className="text-[9px] text-gray-400 font-mono flex items-center gap-1">
                <Terminal className="w-2.5 h-2.5 text-indigo-400" />
                {name.replace('Agent', '')}
              </span>
            </div>

            {/* Terminal Status Output */}
            <div className="font-mono text-[9px] text-gray-300 truncate">
              <span className={isCurrentlyRunning ? 'text-indigo-400 font-semibold' : isCompleted ? 'text-emerald-400' : 'text-gray-500'}>
                {getTerminalSnippet()}
              </span>
              {isCurrentlyRunning && <span className="inline-block w-1.5 h-2.5 bg-indigo-400 ml-1 anim-terminal-cursor" />}
            </div>
          </div>

          {/* Desk Items Bar: Keyboard & Coffee Mug */}
          <div className="w-full flex items-center justify-between px-2 pt-1 border-t border-slate-700/50">
            {/* Keyboard Mat */}
            <div className="w-20 h-2.5 rounded bg-slate-950 border border-slate-700/60" />

            {/* Coffee Mug */}
            <div className="relative flex items-center justify-center">
              <Coffee className="w-3.5 h-3.5 text-amber-400" />
              {(isCurrentlyRunning || isCompleted) && (
                <div className="absolute -top-2.5 left-1 flex gap-0.5 pointer-events-none">
                  <span className="w-1 h-2 rounded-full bg-amber-200/50 anim-steam-1" />
                  <span className="w-1 h-2 rounded-full bg-amber-200/50 anim-steam-2" />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Desk Bottom Details & Log Link */}
      <div className="w-full mt-1 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-gray-400">
        <span className="truncate max-w-[130px] text-gray-500">
          {latestRun ? `Log #${latestRun.id.substring(0, 6)}` : 'Sẵn sàng'}
        </span>
        <span className="flex items-center gap-1 text-indigo-400 font-medium group-hover:text-indigo-300 group-hover:underline">
          Chi tiết <ExternalLink className="w-3 h-3" />
        </span>
      </div>
    </div>
  );
};

