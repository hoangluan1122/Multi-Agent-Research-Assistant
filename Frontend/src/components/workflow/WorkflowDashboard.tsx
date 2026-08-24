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
} from 'lucide-react';
import type { Session, WorkflowStatus, AgentRun } from '../../types';
import { AgentNode } from './AgentNode';
import { AgentLogModal } from './AgentLogModal';

interface WorkflowDashboardProps {
  session: Session;
  workflowStatus: WorkflowStatus | null;
  isRunning: boolean;
  onStartWorkflow: (autoSearch: boolean, maxPapers: number) => Promise<void>;
  onRefreshStatus: () => void;
}


const AGENTS_METADATA = [
  {
    id: 'search',
    name: 'SearchAgent',
    label: '1. Search Agent',
    description: 'Tìm kiếm & thu thập bài báo từ arXiv, Semantic Scholar.',
  },
  {
    id: 'reading',
    name: 'ReadingAgent',
    label: '2. Reading Agent',
    description: 'Đọc sâu trích xuất Phương pháp, Dataset, Kết quả & Đóng góp.',
  },
  {
    id: 'summarization',
    name: 'SummarizationAgent',
    label: '3. Summarization Agent',
    description: 'Tóm tắt tổng quan & lập bảng đối chiếu ma trận so sánh.',
  },
  {
    id: 'writing',
    name: 'WritingAgent',
    label: '4. Writing Agent',
    description: 'Soạn thảo bài tổng quan tài liệu (Literature Review) chi tiết.',
  },
  {
    id: 'review',
    name: 'ReviewAgent',
    label: '5. Review Agent',
    description: 'Chấm điểm chất lượng, phản biện & rà soát Hallucination.',
  },
  {
    id: 'citation',
    name: 'CitationAgent',
    label: '6. Citation Agent',
    description: 'Kiểm chứng trích dẫn và chuẩn hóa định dạng IEEE/APA.',
  },
];

export const WorkflowDashboard: React.FC<WorkflowDashboardProps> = ({
  session,
  workflowStatus,
  isRunning,
  onStartWorkflow,
  onRefreshStatus,
}) => {
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);

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
              Phiên nghiên cứu
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
            title="Làm mới trạng thái"
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
                <span>Multi-Agent Đang Xử Lý...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Chạy Toàn Bộ Workflow</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Progress & Live Step Status Bar */}
      <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-300">Tiến độ quy trình:</span>
            <span className="text-indigo-400 font-bold">{progress}%</span>
            {workflowStatus?.current_agent && (
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[11px] font-mono">
                Agent: {workflowStatus.current_agent}
              </span>
            )}
          </div>
          <span className="text-gray-400 text-[11px]">
            {workflowStatus?.message || session.current_step || 'Sẵn sàng'}
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

      {/* 6 AI Agents Visual Pipeline Graph */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            Đồ Thị Điều Phối Đa Tác Tử (Multi-Agent Graph)
          </h3>
          <span className="text-xs text-gray-500">Nhấn vào Agent để xem JSON log chi tiết</span>
        </div>

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
      </div>

      {/* Execution Runs History List */}
      <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 space-y-3">
        <h3 className="text-xs font-semibold text-gray-300 uppercase tracking-wider">
          Lịch sử thực thi của các Agent ({agentRuns.length} lượt chạy)
        </h3>

        {agentRuns.length === 0 ? (
          <p className="text-xs text-gray-500 py-4 text-center">
            Chưa có lượt chạy agent nào. Nhấn "Chạy Toàn Bộ Workflow" để bắt đầu.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-300">
              <thead className="text-[11px] text-gray-400 border-b border-gray-800 uppercase tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Mô tả bước</th>
                  <th className="py-2.5 px-3">Trạng thái</th>
                  <th className="py-2.5 px-3">Bắt đầu</th>
                  <th className="py-2.5 px-3 text-right">Chi tiết</th>
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
                      {run.step_description || 'Thực thi quy trình'}
                    </td>
                    <td className="py-2.5 px-3">
                      {run.status === 'completed' && (
                        <span className="text-emerald-400 font-medium flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Hoàn tất
                        </span>
                      )}
                      {run.status === 'failed' && (
                        <span className="text-rose-400 font-medium flex items-center gap-1">
                          <AlertCircle className="w-3.5 h-3.5" /> Thất bại
                        </span>
                      )}
                      {run.status === 'running' && (
                        <span className="text-indigo-400 font-medium flex items-center gap-1">
                          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Đang chạy
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-gray-500">
                      {new Date(run.started_at).toLocaleTimeString('vi-VN')}
                    </td>
                    <td className="py-2.5 px-3 text-right text-indigo-400 font-medium hover:underline">
                      Xem log &rarr;
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
