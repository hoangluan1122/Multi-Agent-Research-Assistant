/**
 * Component chính (Main App Component) của giao diện PaperFlow:
 * - Quản lý State toàn cục: Danh sách phiên nghiên cứu (sessions), phiên đang mở (activeSession), danh sách bài báo (papers), bản thảo báo cáo (report), trích dẫn (citations) và trạng thái workflow.
 * - Điều hướng giữa 3 tab nghiệp vụ chính: Workflow Dashboard, Paper Discovery & Management, Literature Review Report.
 * - Cơ chế Polling thời gian thực để cập nhật tiến độ của hệ thống Multi-Agent.
 * - Xử lý thông báo Toast và các Modal tương tác (Create Session, PDF Upload, Paper Analysis, Settings).
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Sparkles,
  Search,
  FileText,
  FolderPlus,
} from 'lucide-react';
import type {
  Session,
  SessionCreate,
  Paper,
  WorkflowStatus,
  Report,
  Citation,
  SystemConfig,
  SystemConfigUpdate,
} from './types';
import { sessionService } from './services/sessionService';
import { paperService } from './services/paperService';
import { workflowService } from './services/workflowService';
import { reportService } from './services/reportService';
import { configService } from './services/configService';

import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { CreateSessionModal } from './components/session/CreateSessionModal';
import { WorkflowDashboard } from './components/workflow/WorkflowDashboard';
import { PaperDiscovery } from './components/papers/PaperDiscovery';
import { ReportView } from './components/reports/ReportView';
import { SettingsModal } from './components/settings/SettingsModal';
import { AuthModal } from './components/auth/AuthModal';
import { ToastContainer } from './components/common/Toast';
import type { ToastMessage } from './components/common/Toast';
import { useI18n } from './i18n/context';
import { useAuth } from './context/AuthContext';
import { Welcome } from './components/Welcome';

export function App() {
  const { t, language } = useI18n();
  const { user } = useAuth();
  const [showWelcome, setShowWelcome] = useState(true);

  // State quản lý dữ liệu toàn cục
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [papers, setPapers] = useState<Paper[]>([]);
  const [report, setReport] = useState<Report | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [config, setConfig] = useState<SystemConfig | null>(null);

  // State điều khiển hiển thị giao diện UI
  const [activeTab, setActiveTab] = useState<'workflow' | 'papers' | 'report'>('workflow');
  const [backendHealthy, setBackendHealthy] = useState<boolean>(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState<boolean>(false);
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  // Polling ref
  const pollingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const addToast = (type: ToastMessage['type'], message: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // 1. Initial Load: Sessions & Config
  const loadInitialData = useCallback(async () => {
    try {
      const [sessionList, sysConfig] = await Promise.all([
        sessionService.getSessions().catch(() => []),
        configService.getConfig().catch(() => null),
      ]);

      setSessions(sessionList);
      setConfig(sysConfig);
      setBackendHealthy(true);

      if (sessionList.length > 0) {
        if (!activeSession || !sessionList.some((s) => s.id === activeSession.id)) {
          setActiveSession(sessionList[0]);
        }
      } else {
        setActiveSession(null);
      }
    } catch (err: any) {
      setBackendHealthy(false);
      addToast('error', 'Không thể kết nối đến Backend server');
    }
  }, [activeSession]);

  useEffect(() => {
    loadInitialData();
  }, [user]);

  // 2. Load Session Details (Papers, Reports, Citations, Workflow Status)
  const loadSessionDetails = useCallback(async (session: Session) => {
    setIsLoading(true);
    try {
      const [sessionPapers, sessionReports, wfStatus] = await Promise.all([
        paperService.getSessionPapers(session.id).catch(() => []),
        reportService.getSessionReports(session.id).catch(() => []),
        workflowService.getWorkflowStatus(session.id).catch(() => null),
      ]);

      setPapers(sessionPapers);
      setWorkflowStatus(wfStatus);

      if (sessionReports.length > 0) {
        const latestReport = sessionReports[0];
        setReport(latestReport);
        const reportCitations = await reportService
          .getReportCitations(latestReport.id)
          .catch(() => []);
        setCitations(reportCitations);
      } else {
        setReport(null);
        setCitations([]);
      }
    } catch (err: any) {
      addToast('error', `Lỗi tải chi tiết phiên: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeSession) {
      loadSessionDetails(activeSession);
    }
  }, [activeSession, loadSessionDetails]);

  // 3. Workflow Real-time Polling
  const wfStatusStr = (workflowStatus?.status || '').toLowerCase();
  const sessionStatusStr = (activeSession?.status || '').toLowerCase();

  const isWorkflowRunning =
    wfStatusStr === 'running' ||
    ['searching', 'reading', 'summarizing', 'drafting', 'reviewing', 'running'].includes(sessionStatusStr);

  useEffect(() => {
    if (!activeSession || !isWorkflowRunning) {
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
      return;
    }

    pollingTimerRef.current = setInterval(async () => {
      try {
        const status = await workflowService.getWorkflowStatus(activeSession.id);
        setWorkflowStatus(status);

        const currentWfStatus = (status.status || '').toLowerCase();
        if (currentWfStatus === 'completed') {
          addToast('success', 'Quy trình Multi-Agent đã hoàn thành thành công!');
          // Refresh session details & session list
          const updatedSession = await sessionService.getSession(activeSession.id);
          setActiveSession(updatedSession);
          loadSessionDetails(updatedSession);
          sessionService.getSessions().then(setSessions);
        } else if (currentWfStatus === 'failed') {
          addToast('error', `Quy trình bị lỗi: ${status.error_message || 'Không rõ'}`);
          const updatedSession = await sessionService.getSession(activeSession.id);
          setActiveSession(updatedSession);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2500);

    return () => {
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    };
  }, [activeSession, isWorkflowRunning, loadSessionDetails]);

  // Handler: Create Session
  const handleCreateSession = async (data: SessionCreate) => {
    try {
      const newSession = await sessionService.createSession(data);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSession(newSession);
      setActiveTab('workflow');
      addToast('success', `Đã khởi tạo phiên: "${newSession.topic}"`);
    } catch (err: any) {
      addToast('error', `Tạo phiên thất bại: ${err.message}`);
    }
  };

  // Handler: Delete Session
  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Bạn có chắc chắn muốn xóa phiên nghiên cứu này?')) return;

    try {
      await sessionService.deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSession?.id === id) {
        const remaining = sessions.filter((s) => s.id !== id);
        setActiveSession(remaining.length > 0 ? remaining[0] : null);
      }
      addToast('info', 'Đã xóa phiên nghiên cứu.');
    } catch (err: any) {
      addToast('error', `Xóa phiên thất bại: ${err.message}`);
    }
  };

  // Handler: Start Workflow
  const handleStartWorkflow = async (autoSearch: boolean, maxPapers: number) => {
    if (!activeSession) return;

    try {
      await workflowService.startWorkflow({
        session_id: activeSession.id,
        auto_search: autoSearch,
        max_papers: maxPapers,
      });
      addToast('info', 'Đã kích hoạt hệ thống Multi-Agent!');

      // Set running state locally to start polling
      setWorkflowStatus((prev) => ({
        session_id: activeSession.id,
        status: 'running',
        current_step: 'Bắt đầu quy trình...',
        current_agent: 'SearchAgent',
        progress_percentage: 5,
        message: 'Khởi chạy các Agent...',
        agent_runs: prev?.agent_runs || [],
      }));
    } catch (err: any) {
      addToast('error', `Khởi chạy workflow thất bại: ${err.message}`);
    }
  };

  // Handler: Search Papers
  const handleSearchPapers = async (
    query: string,
    maxResults: number,
    sources: string[],
    yearStart?: number,
    yearEnd?: number
  ) => {
    if (!activeSession) return;

    try {
      const results = await paperService.searchPapers({
        session_id: activeSession.id,
        query,
        max_results: maxResults,
        sources,
        year_start: yearStart,
        year_end: yearEnd,
      });
      setPapers((prev) => {
        const existingIds = new Set(prev.map((p) => p.id));
        const newOnes = results.filter((p) => !existingIds.has(p.id));
        return [...newOnes, ...prev];
      });
      addToast('success', `Tìm thấy ${results.length} bài báo mới.`);
    } catch (err: any) {
      addToast('error', `Tìm kiếm bài báo thất bại: ${err.message}`);
    }
  };

  // Handler: Upload PDF
  const handleUploadPaper = async (file: File) => {
    if (!activeSession) return;

    try {
      const uploaded = await paperService.uploadPaper(activeSession.id, file);
      setPapers((prev) => [uploaded, ...prev]);
      addToast('success', `Tải lên thành công: ${file.name}`);
    } catch (err: any) {
      addToast('error', `Tải file thất bại: ${err.message}`);
    }
  };

  // Handler: Toggle Paper Selection
  const handleToggleSelectPaper = async (paper: Paper) => {
    try {
      const nextSelected = !paper.is_selected;
      await paperService.updatePaperSelection([paper.id], nextSelected);
      setPapers((prev) =>
        prev.map((p) => (p.id === paper.id ? { ...p, is_selected: nextSelected } : p))
      );
    } catch (err: any) {
      addToast('error', `Cập nhật lựa chọn thất bại: ${err.message}`);
    }
  };

  // Handler: Batch Select Papers
  const handleBatchSelectPapers = async (isSelected: boolean) => {
    try {
      const allIds = papers.map((p) => p.id);
      await paperService.updatePaperSelection(allIds, isSelected);
      setPapers((prev) => prev.map((p) => ({ ...p, is_selected: isSelected })));
      addToast('info', isSelected ? 'Đã chọn tất cả bài báo' : 'Đã bỏ chọn tất cả bài báo');
    } catch (err: any) {
      addToast('error', `Cập nhật danh sách thất bại: ${err.message}`);
    }
  };

  // Handler: Analyze Paper with Reading Agent
  const handleAnalyzePaper = async (paperId: string) => {
    try {
      const analyzed = await paperService.analyzePaper(paperId);
      setPapers((prev) => prev.map((p) => (p.id === paperId ? analyzed : p)));
      addToast('success', 'Reading Agent đã hoàn tất trích xuất cấu trúc bài báo.');
    } catch (err: any) {
      addToast('error', `Phân tích bài báo thất bại: ${err.message}`);
    }
  };

  // Handler: Translate Single Paper
  const handleTranslatePaper = async (paperId: string) => {
    try {
      const translated = await paperService.translatePaper(paperId);
      setPapers((prev) => prev.map((p) => (p.id === paperId ? translated : p)));
      addToast('success', 'Đã dịch tiêu đề và tóm tắt bài báo sang Tiếng Việt!');
    } catch (err: any) {
      addToast('error', `Dịch bài báo thất bại: ${err.message}`);
    }
  };

  // Handler: Translate All Papers
  const handleTranslateAllPapers = async () => {
    if (!activeSession) return;
    try {
      const translatedList = await paperService.translateAllPapers(activeSession.id);
      setPapers(translatedList);
      addToast('success', `Đã dịch toàn bộ ${translatedList.length} bài báo sang Tiếng Việt!`);
    } catch (err: any) {
      addToast('error', `Dịch danh sách thất bại: ${err.message}`);
    }
  };

  // Handler: Export Report
  const handleExportReport = async (format: 'markdown' | 'docx' | 'pdf') => {
    if (!report) return;

    try {
      const blob = await reportService.exportReport(report.id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const extension = format === 'markdown' ? 'md' : format;
      a.download = `Literature_Review_${report.id.substring(0, 8)}.${extension}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      addToast('success', `Đã tải về file ${format.toUpperCase()} thành công.`);
    } catch (err: any) {
      addToast('error', `Xuất file thất bại: ${err.message}`);
    }
  };

  // Handler: Save Config
  const handleSaveConfig = async (update: SystemConfigUpdate) => {
    try {
      const updated = await configService.updateConfig(update);
      setConfig(updated);
      addToast('success', 'Đã lưu cài đặt hệ thống.');
    } catch (err: any) {
      addToast('error', `Lưu cài đặt thất bại: ${err.message}`);
    }
  };

  return (
    <div className="pf-app min-h-screen bg-gray-950 text-gray-100 flex flex-col font-sans">
      {showWelcome && <Welcome signedIn={!!user} onAuth={() => setIsAuthOpen(true)} onSettings={() => setIsSettingsModalOpen(true)} onWorkspace={() => setShowWelcome(false)} onStart={() => { setShowWelcome(false); setIsCreateModalOpen(true); }} />}
      {!showWelcome && <>
      {/* Top Navigation Header */}
      <Header
        currentSession={activeSession}
        config={config}
        backendHealthy={backendHealthy}
        onOpenCreateSession={() => setIsCreateModalOpen(true)}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        onOpenAuth={() => setIsAuthOpen(true)}
        onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
      />

      {/* Main Workspace Layout */}
      <div className="pf-workspace flex-1 flex w-full mx-auto">
        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSession?.id || null}
          isOpen={isSidebarOpen}
          onSelectSession={(s) => setActiveSession(s)}
          onCreateSession={() => setIsCreateModalOpen(true)}
          onDeleteSession={handleDeleteSession}
          onCloseMobile={() => setIsSidebarOpen(false)}
        />

        {/* Content Area */}
        <main className="pf-content min-w-0 flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          <button className="pf-workspace-home" onClick={() => setShowWelcome(true)}>← PaperFlow / {language === 'vi' ? 'Trang giới thiệu' : 'Home'}</button>
          {activeSession ? (
            <div className="space-y-6 max-w-5xl mx-auto">
              {/* Tab Navigation */}
              <div className="pf-tabs flex items-center gap-2 p-1 rounded-2xl bg-gray-900/80 border border-gray-800 w-fit">
                <button
                  onClick={() => setActiveTab('workflow')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                    activeTab === 'workflow'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{t.tabWorkflow}</span>
                </button>

                <button
                  onClick={() => setActiveTab('papers')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                    activeTab === 'papers'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>{t.tabPapers} ({papers.length})</span>
                </button>

                <button
                  onClick={() => setActiveTab('report')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                    activeTab === 'report'
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>{t.tabReport}</span>
                </button>
              </div>

              {/* Tab 1: Workflow */}
              {activeTab === 'workflow' && (
                <WorkflowDashboard
                  session={activeSession}
                  workflowStatus={workflowStatus}
                  isRunning={isWorkflowRunning}
                  onStartWorkflow={handleStartWorkflow}
                  onRefreshStatus={() => {
                    if (activeSession) loadSessionDetails(activeSession);
                  }}
                />
              )}

              {/* Tab 2: Papers */}
              {activeTab === 'papers' && (
                <PaperDiscovery
                  session={activeSession}
                  papers={papers}
                  isLoading={isLoading}
                  onSearchPapers={handleSearchPapers}
                  onUploadPaper={handleUploadPaper}
                  onToggleSelectPaper={handleToggleSelectPaper}
                  onBatchSelectPapers={handleBatchSelectPapers}
                  onAnalyzePaper={handleAnalyzePaper}
                  onTranslatePaper={handleTranslatePaper}
                  onTranslateAllPapers={handleTranslateAllPapers}
                />
              )}

              {/* Tab 3: Report */}
              {activeTab === 'report' && (
                <ReportView
                  session={activeSession}
                  report={report}
                  citations={citations}
                  onExport={handleExportReport}
                  onTriggerWorkflow={() => setActiveTab('workflow')}
                />
              )}
            </div>
          ) : (
            /* Empty State: No Session */
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center shadow-xl shadow-indigo-500/10">
                <FolderPlus className="w-8 h-8" />
              </div>
              <div className="space-y-1 max-w-md">
                <h3 className="text-xl font-bold text-white">{t.emptyTitle}</h3>
                <p className="text-xs text-gray-400 leading-relaxed">
                  {t.emptyDesc}
                </p>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-bold shadow-xl shadow-indigo-600/30 transition-all hover:scale-105 active:scale-95"
              >
                <Sparkles className="w-4 h-4" />
                <span>{t.emptyBtn}</span>
              </button>
            </div>
          )}
        </main>
      </div>
      </>}

      {/* Global Modals */}
      <CreateSessionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateSession}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        config={config}
        onSave={handleSaveConfig}
        onTestLlm={() => configService.testLlm()}
      />

      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
      />

      {/* Toast Notifications Container */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}

export default App;
