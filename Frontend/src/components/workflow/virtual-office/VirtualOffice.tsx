// @trace: REQ-VO-001, REQ-VO-002, REQ-VO-006
import React from 'react';
import type { Session, WorkflowStatus, AgentRun } from '../../../types';
import { OfficeDesk } from './OfficeDesk';
import { PantryBar, TreadmillGym, KanbanBoard } from './OfficeDecorations';
import { Sparkles, Building2, Users, ShieldCheck } from 'lucide-react';
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
              Mô phỏng 6 nhân viên AI cộng tác theo thời gian thực (Multi-Agent Simulation)
            </p>
          </div>
        </div>

        {/* Header Badges */}
        <div className="flex items-center gap-3">
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

      {/* Main Office Work Area (Grid 2 Rows x 3 Desks) */}
      <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
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

      {/* Footer hint */}
      <div className="relative z-10 mt-5 pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs text-gray-400">
        <span>💡 Nhấp vào bất kỳ bàn làm việc nào của Agent để xem chi tiết nhật ký thực thi (JSON Log).</span>
        <span className="text-slate-400 font-mono">PaperFlow Office Engine v2.0</span>
      </div>
    </div>
  );
};

