/**
 * Component Hiển thị Báo cáo Tổng quan Tài liệu (Literature Review Report View - UC009, UC010, UC012):
 * - Render nội dung báo cáo bằng Markdown sinh động qua ReactMarkdown và remark-gfm.
 * - Điều hướng giữa 3 chế độ xem: Toàn văn báo cáo (Content), Ma trận so sánh đối chiếu (Matrix), Thẻ điểm đánh giá (Peer Review).
 * - Các nút xuất bản báo cáo tải về dưới dạng Markdown (.md), Word (.docx), PDF (.pdf).
 * - Mở danh mục trích dẫn đã xác thực qua Modal.
 */

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Download,
  FileText,
  Quote,
  Sparkles,
  Award,
  Loader2,
  Table as TableIcon,
  Edit3,
  Send,
} from 'lucide-react';
import type { Session, Report, Citation } from '../../types';
import { ReviewScorecard } from './ReviewScorecard';
import { CitationListModal } from './CitationListModal';
import { Badge } from '../common/Badge';
import { useI18n } from '../../i18n/context';

interface ReportViewProps {
  session?: Session;
  report: Report | null;
  citations: Citation[];
  onExport: (format: 'markdown' | 'docx' | 'pdf') => Promise<void>;
  onTriggerWorkflow: () => void;
  onRevise?: (feedback: string) => Promise<void>;
}

export const ReportView: React.FC<ReportViewProps> = ({
  report,
  citations,
  onExport,
  onTriggerWorkflow,
  onRevise,
}) => {
  const { t } = useI18n();
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);
  const [isCitationModalOpen, setIsCitationModalOpen] = useState(false);
  // const [activeTab, setActiveTab] = useState<'content' | 'matrix' | 'review' | 'revise'>('content');
  const [activeTab, setActiveTab] = useState<'content' | 'matrix'>('content');
  const [feedbackInput, setFeedbackInput] = useState('');
  const [isRevising, setIsRevising] = useState(false);

  const handleRevise = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedbackInput.trim() || !onRevise) return;
    setIsRevising(true);
    try {
      await onRevise(feedbackInput.trim());
      setFeedbackInput('');
      setActiveTab('content');
    } finally {
      setIsRevising(false);
    }
  };


  const handleExport = async (fmt: 'markdown' | 'docx' | 'pdf') => {
    setExportingFormat(fmt);
    try {
      await onExport(fmt);
    } finally {
      setExportingFormat(null);
    }
  };

  if (!report) {
    return (
      <div className="p-12 rounded-2xl bg-gray-900/40 border border-gray-800 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center mx-auto">
          <FileText className="w-6 h-6" />
        </div>
        <div className="space-y-1 max-w-md mx-auto">
          <h3 className="text-base font-bold text-white">{t.noReportYetTitle}</h3>
          <p className="text-xs text-gray-400">
            {t.noReportYetDesc}
          </p>
        </div>
        <button
          onClick={onTriggerWorkflow}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all"
        >
          <Sparkles className="w-4 h-4" />
          <span>{t.startReviewBtn}</span>
        </button>
      </div>
    );
  }

  const latestReview = report.reviews && report.reviews.length > 0 ? report.reviews[0] : undefined;

  return (
    <div className="space-y-6">
      {/* Top Banner & Export Actions */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-gray-900 via-gray-800/90 to-gray-900 border border-gray-800 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
              {t.reportHeaderTitle}
            </span>
            <span className="text-xs text-gray-500">•</span>
            <Badge variant="success">{t.versionBadge} {report.version}.0</Badge>
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">{report.title}</h2>
        </div>

        {/* Action Buttons: Export & Citations */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Citations List Button */}
          <button
            onClick={() => setIsCitationModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-indigo-300 hover:text-white border border-gray-700 text-xs font-medium transition-colors"
          >
            <Quote className="w-3.5 h-3.5" />
            <span>{t.citationsBtn} ({citations.length})</span>
          </button>

          {/* Export Dropdown / Buttons */}
          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-gray-800/80 border border-gray-700">
            {(['markdown', 'docx', 'pdf'] as const).map((fmt) => (
              <button
                key={fmt}
                disabled={exportingFormat !== null}
                onClick={() => handleExport(fmt)}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-gray-300 hover:text-white hover:bg-gray-700/80 transition-all uppercase disabled:opacity-50"
                title={`${t.exportFormatTooltip} ${fmt.toUpperCase()}`}
              >
                {exportingFormat === fmt ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                <span>{fmt === 'markdown' ? 'MD' : fmt}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('content')}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === 'content'
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>{t.tabReportContent}</span>
        </button>

        {report.comparison_table && (
          <button
            onClick={() => setActiveTab('matrix')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'matrix'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <TableIcon className="w-4 h-4" />
            <span>{t.tabComparisonMatrix}</span>
          </button>
        )}

        {/* {latestReview && (
          <button
            onClick={() => setActiveTab('review')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'review'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <Award className="w-4 h-4" />
            <span>
              {t.tabPeerReview} (
              {latestReview.score <= 10
                ? (latestReview.score * 10).toFixed(0)
                : latestReview.score.toFixed(0)}
              /100)
            </span>
          </button>
        )} */}

        {/* {onRevise && (
          <button
            onClick={() => setActiveTab('revise')}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'revise'
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
            }`}
          >
            <Edit3 className="w-4 h-4" />
            <span>Sửa Theo Góp Ý (Feedback)</span>
          </button>
        )} */}
      </div>

      {/* Tab 1: Full Markdown Content */}
      {activeTab === 'content' && (
        <div className="p-8 rounded-2xl bg-gray-900/90 border border-gray-800 shadow-2xl text-gray-200">
          <article className="prose prose-invert max-w-none prose-headings:text-indigo-200 prose-a:text-indigo-400 prose-pre:bg-gray-950 prose-pre:border prose-pre:border-gray-800">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {report.content}
            </ReactMarkdown>
          </article>
        </div>
      )}

      {/* Tab 2: Comparison Matrix Table */}
      {/* {activeTab === 'matrix' && report.comparison_table && (
        <div className="p-6 rounded-2xl bg-gray-900/90 border border-gray-800 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-indigo-300 uppercase tracking-wider flex items-center gap-2">
            <TableIcon className="w-4 h-4 text-indigo-400" />
            {t.matrixSectionTitle}
          </h4>
          <div className="overflow-x-auto custom-scrollbar">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {report.comparison_table}
            </ReactMarkdown>
          </div>
        </div>
      )} */}

{activeTab === 'matrix' && report.comparison_table && (
  <div className="overflow-hidden rounded-2xl border border-indigo-100 bg-white shadow-sm">
    <div className="flex items-center gap-2 border-b border-indigo-100 bg-indigo-50 px-5 py-4">
      <TableIcon className="h-4 w-4 text-indigo-600" />
      <h4 className="text-sm font-bold uppercase tracking-wide text-indigo-700">
        Bảng đối chiếu ma trận các nghiên cứu
      </h4>
    </div>

    <div className="overflow-x-auto">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => (
            <table className="min-w-[1150px] w-full border-collapse text-left text-xs">
              {children}
            </table>
          ),
          thead: ({ children }) => (
            <thead className="bg-slate-50 text-slate-700">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="border-b border-slate-200 px-4 py-3 font-bold whitespace-nowrap">
              {children}
            </th>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-slate-100 align-top odd:bg-white even:bg-slate-50/60 hover:bg-indigo-50/50">
              {children}
            </tr>
          ),
          td: ({ children }) => (
            <td className="max-w-[250px] break-words px-4 py-3 leading-5 text-slate-600">
              {children}
            </td>
          ),
        }}
      >
        {report.comparison_table}
      </ReactMarkdown>
    </div>
  </div>
)}
      {/* Tab 3: Review Scorecard */}
      {/* {activeTab === 'review' && (
        <ReviewScorecard review={latestReview} />
      )} */}

      {/* Tab 4: Revise with User Feedback */}
      {/* {activeTab === 'revise' && onRevise && (
        <div className="p-6 rounded-2xl bg-gray-900/90 border border-gray-800 shadow-xl space-y-6">
          <div className="space-y-1">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <Edit3 className="w-5 h-5 text-indigo-400" />
              Chỉnh Sửa Báo Cáo Dựa Trên Góp Ý (UC011)
            </h4>
            <p className="text-xs text-gray-400">
              Nhập các yêu cầu chỉnh sửa, chỉ đạo học thuật hoặc bổ sung phân tích. WritingAgent sẽ viết lại báo cáo thành phiên bản mới (v{report.version + 1}) và ReviewAgent sẽ thẩm định lại.
            </p>
          </div>

          {latestReview?.feedback && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-200 space-y-1">
              <span className="font-semibold text-amber-300">Góp ý từ lần phản biện trước:</span>
              <p className="italic text-gray-300">"{latestReview.feedback}"</p>
            </div>
          )}

          <form onSubmit={handleRevise} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1.5">
                Nội dung góp ý / Yêu cầu chỉnh sửa cụ thể:
              </label>
              <textarea
                rows={5}
                required
                value={feedbackInput}
                onChange={(e) => setFeedbackInput(e.target.value)}
                placeholder="Ví dụ: Bổ sung so sánh chi tiết thời gian huấn luyện giữa Transformer và CNN, giải thích thêm về hạn chế của tập dữ liệu Imagenet..."
                className="w-full px-4 py-3 rounded-xl bg-gray-950 border border-gray-800 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-colors resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={isRevising || !feedbackInput.trim()}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
            >
              {isRevising ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>WritingAgent đang chỉnh sửa & ReviewAgent đang thẩm định...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Gửi góp ý & Tạo bản báo cáo mới (v{report.version + 1})</span>
                </>
              )}
            </button>
          </form>
        </div>
      )} */}

      {/* Citation Modal */}
      <CitationListModal
        citations={citations}
        isOpen={isCitationModalOpen}
        onClose={() => setIsCitationModalOpen(false)}
      />
    </div>
  );
};

