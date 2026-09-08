// @trace: REQ-VO-001, REQ-VO-002, REQ-VO-006, REQ-STICKMAN-001, REQ-STICKMAN-002, REQ-STICKMAN-003
import React, { useState } from 'react';
import type { Session, WorkflowStatus, AgentRun } from '../../../types';
import { OfficeDesk } from './OfficeDesk';
import { PantryBar, TreadmillGym, KanbanBoard } from './OfficeDecorations';
import { StickmanCourier } from './StickmanCourier';
import { Sparkles, Building2, Users, ShieldCheck, Send } from 'lucide-react';
import './officeTheme.css';

interface VirtualOfficeProps {
  session: Session;
  workflowStatus: WorkflowStatus | null;
  isRunning: boolean;
  agentsMetadata: Array<{
    id: string;
    name: string;
    label: string;
    description: string;
  }>;
  onAgentClick: (agentName: string) => void;
}

export const VirtualOffice: React.FC<VirtualOfficeProps> = ({
  session,
  workflowStatus,
  isRunning,
  agentsMetadata,
  onAgentClick,
}) => {
  const currentActiveAgent = workflowStatus?.current_agent;
  const agentRuns = workflowStatus?.agent_runs || [];

  const [demoIndex, setDemoIndex] = useState<number | null>(null);
  const [isDemoRunning, setIsDemoRunning] = useState(false);

  const getLatestRunForAgent = (agentName: string): AgentRun | undefined => {
    const runs = agentRuns.filter((r) => r.agent_name === agentName);
    return runs.length > 0 ? runs[runs.length - 1] : undefined;
  };

  const progress = workflowStatus?.progress_percentage ?? (session.status === 'completed' ? 100 : 0);

  // Count active / completed agents
  const completedCount = agentsMetadata.filter((a) => {
    const latest = getLatestRunForAgent(a.name);
    return latest?.status?.toLowerCase() === 'completed';
  }).length;

  // Interactive Demo: Stickman courier walks across all 6 desks delivering documents
  const handleDemoWalk = () => {
    if (isDemoRunning) return;
    setIsDemoRunning(true);
    let step = 0;
    setDemoIndex(0);

    const interval = setInterval(() => {
      step += 1;
      if (step < 6) {
        setDemoIndex(step);
      } else {
        setDemoIndex(6); // Celebration
        clearInterval(interval);
        setTimeout(() => {
          setDemoIndex(null);
          setIsDemoRunning(false);
        }, 2200);
      }
    }, 1800);
  };

  return (
    <div className="relative p-6 rounded-3xl bg-slate-950 border border-slate-800/80 shadow-2xl overflow-hidden select-none">
      {/* Ambient Lighting */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Office Header */}
      <div className="relative z-10 flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-0.5 shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full rounded-[14px] bg-slate-950 flex items-center justify-center text-indigo-400">
              <Building2 className="w-6 h-6" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-wide">
                Văn Phòng Ảo 6 AI Agents
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-[10px] text-indigo-300 font-semibold flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                Live Office
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Mô phỏng 6 nhân viên AI & Người que 2D giao nhận tài liệu thời gian thực
            </p>
          </div>
        </div>

        {/* Header Badges & Demo Walk Button */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleDemoWalk}
            disabled={isDemoRunning || isRunning}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-semibold shadow-md transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Kích hoạt người que 2D chạy thử nghiệm chuyển tài liệu qua 6 bàn"
          >
            <Send className={`w-3.5 h-3.5 text-amber-400 ${isDemoRunning ? 'animate-spin' : ''}`} />
            <span>{isDemoRunning ? 'Người Que Đang Giao Việc...' : '🚶‍♂️ Demo Giao Việc'}</span>
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-gray-400">Nhân sự:</span>
            <span className="font-semibold text-white">6 Agents</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-gray-400">Hoàn thành:</span>
            <span className="font-semibold text-emerald-400">{completedCount}/6</span>
          </div>
        </div>
      </div>

      {/* Top Office Decor / Breakroom Row */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-4 my-5">
        <PantryBar />
        <TreadmillGym isRunning={isRunning} />
        <KanbanBoard progress={progress} />
      </div>

      {/* Office Floor Container with 2D Stickman Courier Layer */}
      <div className="relative z-10">
        {/* 2D Stickman Courier Navigating and Handing Over Documents */}
        <StickmanCourier
          currentActiveAgent={currentActiveAgent}
          isRunning={isRunning}
          totalCompleted={completedCount}
          customTargetIndex={demoIndex}
        />

        {/* Main Office Work Area (Grid 2 Rows x 3 Desks) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {agentsMetadata.map((agent) => (
            <OfficeDesk
              key={agent.id}
              id={agent.id}
              name={agent.name}
              label={agent.label}
              description={agent.description}
              currentActiveAgent={currentActiveAgent}
              latestRun={getLatestRunForAgent(agent.name)}
              onClick={() => onAgentClick(agent.name)}
            />
          ))}
        </div>
      </div>

      {/* Footer hint */}
      <div className="relative z-10 mt-5 pt-4 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-400">
        <span>💡 Người que 2D sẽ tự động chạy sang từng bàn để trao tập hồ sơ và giao việc khi workflow chạy.</span>
        <span className="text-slate-400 font-mono">PaperFlow Office Engine v2.0 • 2D Courier</span>
      </div>
    </div>
  );
};

