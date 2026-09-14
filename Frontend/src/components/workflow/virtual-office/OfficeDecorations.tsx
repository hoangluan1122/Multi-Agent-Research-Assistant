// @trace: REQ-VO-004
import React from 'react';
import { Coffee, Activity, FileText } from 'lucide-react';
import './officeTheme.css';

export const PantryBar: React.FC = () => {
  return (
    <div className="relative p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md flex items-center justify-between gap-3 select-none">
      <div className="flex items-center gap-2.5">
        <div className="w-10 h-10 rounded-xl bg-amber-950/60 border border-amber-500/30 flex items-center justify-center text-amber-400">
          <Coffee className="w-5 h-5" />
        </div>
        <div>
          <h5 className="text-xs font-semibold text-gray-200">Quầy Cà Phê AI</h5>
          <p className="text-[10px] text-gray-400">Pantry & Nạp Năng Lượng</p>
        </div>
      </div>
      <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-amber-300 font-mono">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
        <span>Espresso Free</span>
      </div>
    </div>
  );
};

export const TreadmillGym: React.FC<{ isRunning: boolean }> = ({ isRunning }) => {
  return (
    <div className="relative p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md flex items-center justify-between gap-3 select-none">
      <div className="flex items-center gap-2.5">
        <div className="w-10 h-10 rounded-xl bg-sky-950/60 border border-sky-500/30 flex items-center justify-center text-sky-400">
          <Activity className={`w-5 h-5 ${isRunning ? 'anim-running' : ''}`} />
        </div>
        <div>
          <h5 className="text-xs font-semibold text-gray-200">Máy Chạy Bộ</h5>
          <p className="text-[10px] text-gray-400">{isRunning ? 'Agents Đang Nạp Calo...' : 'Nghỉ ngơi'}</p>
        </div>
      </div>
      <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-slate-950 border border-slate-800 text-[10px] text-sky-300 font-mono">
        <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-sky-400 animate-ping' : 'bg-gray-500'}`} />
        <span>{isRunning ? '12.5 km/h' : '0 km/h'}</span>
      </div>
    </div>
  );
};

export const KanbanBoard: React.FC<{ progress: number }> = ({ progress }) => {
  return (
    <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md flex flex-col justify-between select-none">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-gray-200 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-indigo-400" />
          Bảng Tiến Độ Dự Án
        </span>
        <span className="text-xs font-bold text-indigo-400 font-mono">{progress}%</span>
      </div>
      <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

