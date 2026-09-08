// @trace: REQ-VO-001, REQ-VO-002, REQ-VO-006, REQ-DINO-HANDOVER-001, REQ-DINO-HANDOVER-002
import React, { useState, useEffect, useRef } from 'react';
import type { Session, WorkflowStatus, AgentRun } from '../../../types';
import { OfficeDesk } from './OfficeDesk';
import { PantryBar, TreadmillGym, KanbanBoard } from './OfficeDecorations';
import { AgentDinoHandover, type HandoverInfo } from './AgentDinoHandover';
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

const DINO_SPECS: Array<{
  name: string;
  skin: 'doux' | 'vita' | 'tard' | 'mort';
  accessory: string;
  filter?: string;
  roleTitle: string;
}> = [
  { name: 'SearchAgent', skin: 'doux', accessory: '🔍', roleTitle: 'Search Dino' },
  { name: 'ReadingAgent', skin: 'vita', accessory: '📖', roleTitle: 'Reading Dino' },
  { name: 'SummarizationAgent', skin: 'tard', accessory: '⚡', roleTitle: 'Summary Dino' },
  { name: 'WritingAgent', skin: 'mort', accessory: '✍️', roleTitle: 'Writing Dino' },
  { name: 'ReviewAgent', skin: 'doux', accessory: '⚖️', filter: 'hue-rotate(140deg) saturate(1.4)', roleTitle: 'Review Dino' },
  { name: 'CitationAgent', skin: 'vita', accessory: '🏛️', filter: 'hue-rotate(200deg) brightness(1.1)', roleTitle: 'Citation Dino' },
];

const HANDOVER_MESSAGES = [
  '🔍 Search Dino mang kết quả tìm kiếm sang bàn Reading Agent!',
  '📖 Reading Dino chuyển trích xuất tài liệu sang bàn Summary Agent!',
  '⚡ Summary Dino chuyển ma trận đối sánh sang bàn Writing Agent!',
  '✍️ Writing Dino nộp bản thảo bài báo sang bàn Review Agent!',
  '⚖️ Review Dino chuyển hồ sơ thẩm định sang bàn Citation Agent!',
  '🏛️ Citation Dino hoàn thành đóng dấu chuẩn IEEE/APA 100%!',
];

export const VirtualOffice: React.FC<VirtualOfficeProps> = ({
  session,
  workflowStatus,
  isRunning,
  agentsMetadata,
  onAgentClick,
}) => {
  const currentActiveAgent = workflowStatus?.current_agent;
  const agentRuns = workflowStatus?.agent_runs || [];

  const [activeHandover, setActiveHandover] = useState<HandoverInfo | null>(null);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const prevActiveAgentRef = useRef<string | undefined>(undefined);

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

  // Trigger handover when workflow transitions to next agent
  useEffect(() => {
    if (!currentActiveAgent) {
      prevActiveAgentRef.current = undefined;
      return;
    }

    const prevAgent = prevActiveAgentRef.current;
    if (prevAgent && prevAgent !== currentActiveAgent) {
      const fromIdx = agentsMetadata.findIndex((a) => a.name === prevAgent);
      const toIdx = agentsMetadata.findIndex((a) => a.name === currentActiveAgent);

      if (fromIdx >= 0 && toIdx >= 0 && toIdx === fromIdx + 1) {
        const spec = DINO_SPECS[fromIdx];
        setActiveHandover({
          fromIndex: fromIdx,
          toIndex: toIdx,
          senderAgent: prevAgent,
          receiverAgent: currentActiveAgent,
          senderSkin: spec.skin,
          senderAccessory: spec.accessory,
          senderFilter: spec.filter,
          message: HANDOVER_MESSAGES[fromIdx] || `🦖 ${spec.roleTitle} chuyển tài liệu sang bàn tiếp theo!`,
        });
      }
    }
    prevActiveAgentRef.current = currentActiveAgent;
  }, [currentActiveAgent, agentsMetadata]);

  // Interactive Demo: Each Agent's Dino gets up and runs to the next desk to deliver work!
  const handleDemoWalk = () => {
    if (isDemoRunning || isRunning) return;
    setIsDemoRunning(true);

    const runStep = (idx: number) => {
      if (idx < 5) {
        const spec = DINO_SPECS[idx];
        setActiveHandover({
          fromIndex: idx,
          toIndex: idx + 1,
          senderAgent: spec.name,
          receiverAgent: DINO_SPECS[idx + 1].name,
          senderSkin: spec.skin,
          senderAccessory: spec.accessory,
          senderFilter: spec.filter,
          message: HANDOVER_MESSAGES[idx],
        });

        setTimeout(() => {
          runStep(idx + 1);
        }, 2400);
      } else {
        // Final completion celebration
        setActiveHandover(null);
        setTimeout(() => {
          setIsDemoRunning(false);
        }, 800);
      }
    };

    runStep(0);
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
                Văn Phòng Ảo 6 AI Dino Agents
              </h3>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-[10px] text-indigo-300 font-semibold flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                Live Dino Office
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              6 chú khủng long AI làm việc & tự động chạy giao tài liệu sang bàn tiếp theo khi xong việc
            </p>
          </div>
        </div>

        {/* Header Badges & Demo Handover Button */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleDemoWalk}
            disabled={isDemoRunning || isRunning}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-semibold shadow-md transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Khủng long mỗi bàn hoàn thành việc sẽ tự động chạy sang bàn kế tiếp để giao hồ sơ"
          >
            <Send className={`w-3.5 h-3.5 text-amber-400 ${isDemoRunning ? 'animate-spin' : ''}`} />
            <span>{isDemoRunning ? 'Dino Đang Chạy Giao Việc...' : '🦖 Demo Dino Giao Việc'}</span>
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <Users className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-gray-400">Nhân sự:</span>
            <span className="font-semibold text-white">6 Dino Agents</span>
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

      {/* Office Floor Container with Dynamic Dino Handover Runner Layer */}
      <div className="relative z-10">
        {/* Active Handover Dino Running from Sender Desk to Receiver Desk */}
        <AgentDinoHandover
          handover={activeHandover}
          onHandoverComplete={() => setActiveHandover(null)}
        />

        {/* Main Office Work Area (Grid 2 Rows x 3 Desks) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {agentsMetadata.map((agent, index) => (
            <OfficeDesk
              key={agent.id}
              id={agent.id}
              name={agent.name}
              label={agent.label}
              description={agent.description}
              currentActiveAgent={currentActiveAgent}
              latestRun={getLatestRunForAgent(agent.name)}
              isDelivering={activeHandover?.fromIndex === index}
              onClick={() => onAgentClick(agent.name)}
            />
          ))}
        </div>
      </div>

      {/* Footer hint */}
      <div className="relative z-10 mt-5 pt-4 border-t border-slate-800/60 flex flex-wrap items-center justify-between gap-2 text-xs text-gray-400">
        <span>💡 Mỗi bàn là 1 chú khủng long chuyên môn riêng. Khi xong việc, Dino sẽ rời bàn và trực tiếp chạy sang bàn kế tiếp để bàn giao tài liệu.</span>
        <span className="text-slate-400 font-mono">PaperFlow Dino Office v2.0</span>
      </div>
    </div>
  );
};
