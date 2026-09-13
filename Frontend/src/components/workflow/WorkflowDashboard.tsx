/**
 * Component Bảng Điều Khiển Luồng Tác Tử (Multi-Agent Workflow Dashboard):
 * - Nút điều khiển khởi chạy chu trình nghiên cứu tự động (Run Workflow).
 * - Thanh hiển thị tiến độ % thời gian thực và thông điệp trạng thái hiện tại.
 * - Sơ đồ trực quan liên kết 5 tác tử (SearchAgent -> ReadingAgent -> SummarizationAgent -> WritingAgent -> ReviewAgent).
 * - Bảng nhật ký hoạt động thời gian thực (Live Agent Execution History).
 */

import React, { useState } from 'react';
import {
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Layers,
  RefreshCw,
  Building2,
} from 'lucide-react';
import type { Session, WorkflowStatus, AgentRun } from '../../types';
import { AgentNode } from './AgentNode';
import { AgentLogModal } from './AgentLogModal';
import { VirtualOffice } from './virtual-office/VirtualOffice';
import { useI18n } from '../../i18n/context';

interface WorkflowDashboardProps {
  session: Session;
  workflowStatus: WorkflowStatus | null;
  isRunning: boolean;
  onStartWorkflow: (autoSearch: boolean, maxPapers: number) => Promise<void>;
  onRefreshStatus: () => void;
}

export const WorkflowDashboard: React.FC<WorkflowDashboardProps> = ({
  session,
  workflowStatus,
  isRunning,
  onStartWorkflow,
  onRefreshStatus,
}) => {
  const { language, t } = useI18n();
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'office' | 'graph'>('graph');

  const AGENTS_METADATA = [
    {
      id: 'search',
      name: 'SearchAgent',
      label: t.agentSearchLabel,
      description: t.agentSearchDesc,
    },
    {
      id: 'reading',
      name: 'ReadingAgent',
      label: t.agentReadingLabel,
      description: t.agentReadingDesc,
    },
    {
      id: 'summarization',
      name: 'SummarizationAgent',
      label: t.agentSummarizationLabel,
      description: t.agentSummarizationDesc,
    },
    {
      id: 'writing',
      name: 'WritingAgent',
      label: t.agentWritingLabel,
      description: t.agentWritingDesc,
    },
    {
      id: 'review',
      name: 'ReviewAgent',
      label: t.agentReviewLabel,
      description: t.agentReviewDesc,
    },
    {
      id: 'citation',
      name: 'CitationAgent',
      label: t.agentCitationLabel,
      description: t.agentCitationDesc,
    },
  ];

  const agentRuns = workflowStatus?.agent_runs || [];

  const getLatestRunForAgent = (agentName: string) => {
    const runs = agentRuns.filter((r) => r.agent_name === agentName);
    return runs.length > 0 ? runs[runs.length - 1] : undefined;
  };

  const handleAgentClick = (agentName: string) => {
    const latest = getLatestRunForAgent(agentName);
    if (latest) {
      setSelectedRun(latest);
      setIsLogModalOpen(true);
    }
  };

  const progress = workflowStatus?.progress_percentage ?? (session.status === 'completed' ? 100 : 0);

  return (
    <div className="space-y-6">
      {/* Session Title & Action Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-gray-900 via-gray-800/90 to-gray-900 border border-gray-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              {t.sessionLabel}
            </span>
            <span className="text-xs text-gray-500">•</span>
            <span className="text-xs text-gray-400">ID: {session.id.substring(0, 8)}...</span>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">{session.topic}</h2>
          {session.research_question && (
            <p className="text-xs text-gray-400 max-w-2xl">{session.research_question}</p>
          )}
        </div>

        {/* Workflow Runner Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={onRefreshStatus}
            className="p-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700 transition-colors"
            title={t.refreshTooltip}
          >
            <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => onStartWorkflow(true, 5)}
            disabled={isRunning}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t.workflowRunning}</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>{t.runWorkflowBtn}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress & Live Step Status Bar */}
      <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-300">{t.progressLabel}</span>
            <span className="text-indigo-400 font-bold">{progress}%</span>
            {workflowStatus?.current_agent && (
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[11px] font-mono">
                Agent: {workflowStatus.current_agent}
              </span>
            )}
          </div>
          <span className="text-gray-400 text-[11px]">
            {workflowStatus?.message || session.current_step || t.currentStepReady}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-2.5 bg-gray-800 rounded-full overflow-hidden p-0.5 border border-gray-700/50">
          <div
            className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-full transition-all duration-500 shadow-sm shadow-indigo-500/50"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Multi-Agent Visual Area with View Switch */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {viewMode === 'office' ? (
              <Building2 className="w-4 h-4 text-indigo-400" />
            ) : (
              <Layers className="w-4 h-4 text-indigo-400" />
            )}
            <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
              {viewMode === 'office' ? 'Văn Phòng Ảo 6 AI Agents' : t.graphTitle}
            </h3>
          </div>

          {/* View Mode Toggle Switch */}
          <div className="flex items-center p-1 rounded-xl bg-gray-900 border border-gray-800 shadow-inner">
            <button
              onClick={() => setViewMode('office')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'office'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>{t.viewModeOffice}</span>
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'graph'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/25'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>{t.viewModeGraph}</span>
            </button>
          </div>
        </div>

        {/* Conditional Rendering: Virtual Office vs Classic Graph */}
        {viewMode === 'office' ? (
          <VirtualOffice
            session={session}
            workflowStatus={workflowStatus}
            isRunning={isRunning}
            agentsMetadata={AGENTS_METADATA}
            onAgentClick={handleAgentClick}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {AGENTS_METADATA.map((agent) => (
              <AgentNode
                key={agent.id}
                name={agent.name}
                label={agent.label}
                description={agent.description}
                currentActiveAgent={workflowStatus?.current_agent}
                latestRun={getLatestRunForAgent(agent.name)}
                onClick={() => handleAgentClick(agent.name)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Execution Runs History List */}
      <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-3">
        <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
          {t.runHistoryTitle} ({agentRuns.length})
        </h3>

        {agentRuns.length === 0 ? (
          <p className="text-xs text-gray-500 py-4 text-center">
            {t.noRunsYet}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="text-[11px] text-gray-400 border-b border-gray-800 uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">{t.colAgent}</th>
                  <th className="py-2.5 px-3">{t.colStep}</th>
                  <th className="py-2.5 px-3">{t.colStatus}</th>
                  <th className="py-2.5 px-3">{t.colStarted}</th>
                  <th className="py-2.5 px-3 text-right">{t.colDetails}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {agentRuns.map((run) => (
                  <tr
                    key={run.id}
                    onClick={() => {
                      setSelectedRun(run);
                      setIsLogModalOpen(true);
                    }}
                    className="hover:bg-gray-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-2.5 px-3 font-semibold text-indigo-300">{run.agent_name}</td>
                    <td className="py-2.5 px-3 text-gray-400 max-w-xs truncate">
                      {run.step_description || t.stepExecuting}
                    </td>
                    <td className="py-2.5 px-3">
                      {run.status?.toLowerCase() === 'completed' && (
                        <span className="text-emerald-400 font-medium flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> {t.statusDone}
                        </span>
                      )}
                      {run.status?.toLowerCase() === 'failed' && (
                        <span className="text-rose-400 font-medium flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" /> {t.statusError}
                        </span>
                      )}
                      {run.status?.toLowerCase() === 'running' && (
                        <span className="text-indigo-400 font-medium flex items-center gap-1">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> {t.statusInProgress}
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-gray-500">
                      {new Date(run.started_at).toLocaleTimeString(language === 'vi' ? 'vi-VN' : 'en-US')}
                    </td>
                    <td className="py-2.5 px-3 text-right text-indigo-400 font-medium hover:underline">
                      {t.viewLogLink}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Log Modal */}
      <AgentLogModal
        run={selectedRun}
        isOpen={isLogModalOpen}
        onClose={() => setIsLogModalOpen(false)}
      />
    </div>
  );
};
