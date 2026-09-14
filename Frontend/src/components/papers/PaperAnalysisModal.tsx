/**
 * Component Modal Hiển thị Kết quả Phân tích Bài báo (Reading Agent Analysis):
 * Trình bày trực quan 5 khía cạnh cốt lõi đã được trích xuất:
 * 1. Phương pháp / Kiến trúc kỹ thuật (Method & Architecture).
 * 2. Bộ dữ liệu huấn luyện & đánh giá (Datasets & Benchmarks).
 * 3. Chỉ số định lượng & Kết quả thực nghiệm (Metrics & Findings).
 * 4. Rào cản & Hạn chế nghiên cứu (Limitations & Bottlenecks).
 * 5. Tóm tắt tổng quan 2-3 câu (Synthesis Summary).
 */

import React from 'react';
import { Modal } from '../common/Modal';
import type { Paper } from '../../types';
import { Badge } from '../common/Badge';
import { BookOpen, Cpu, Database, Award, AlertTriangle, FileText, ExternalLink } from 'lucide-react';
import { useI18n } from '../../i18n/context';

interface PaperAnalysisModalProps {
  paper: Paper | null;
  isOpen: boolean;
  onClose: () => void;
}

export const PaperAnalysisModal: React.FC<PaperAnalysisModalProps> = ({
  paper,
  isOpen,
  onClose,
}) => {
  const { t } = useI18n();
  if (!paper) return null;

  const analysis = paper.analysis;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t.analysisModalTitle}
      subtitle={paper.title}
      maxWidth="4xl"
    >
      <div className="space-y-5 text-xs text-gray-200">
        {/* Metadata Banner */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-gray-800/50 border border-gray-700/60">
          <div className="space-y-1">
            <p className="text-gray-400">
              <span className="font-semibold text-gray-300">{t.authorsLabel}</span>{' '}
              {paper.authors.join(', ') || 'N/A'}
            </p>
            <div className="flex items-center gap-2 text-[11px] text-gray-400">
              {paper.year && <span>{t.yearLabel} {paper.year}</span>}
              {paper.venue && <span>• {t.publishedVenue} {paper.venue}</span>}
              <span>• {t.sourceLabel} {paper.source}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="primary">{t.relevanceLabel} {(paper.relevance_score * 100).toFixed(0)}%</Badge>
            {paper.url && (
              <a
                href={paper.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 font-medium transition-colors"
              >
                <span>{t.viewOriginalPaper}</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>

        {/* Abstract */}
        {paper.abstract && (
          <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800 space-y-1.5">
            <h4 className="font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" /> {t.abstractTitle}
            </h4>
            <p className="text-gray-300 leading-relaxed text-xs">{paper.abstract}</p>
          </div>
        )}

        {/* Analysis Sections (Method, Dataset, Metrics, Limitations) */}
        {analysis ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Method */}
            <div className="p-4 rounded-xl bg-gray-800/40 border border-gray-700/50 space-y-1.5">
              <h4 className="font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" /> {t.methodologyTitle}
              </h4>
              <p className="text-gray-300 leading-relaxed">
                {analysis.method || t.notExtractedYet}
              </p>
            </div>

            {/* Dataset */}
            <div className="p-4 rounded-xl bg-gray-800/40 border border-gray-700/50 space-y-1.5">
              <h4 className="font-semibold text-blue-300 uppercase tracking-wider flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-blue-400" /> {t.datasetTitle}
              </h4>
              <p className="text-gray-300 leading-relaxed">
                {analysis.dataset || t.notExtractedYet}
              </p>
            </div>

            {/* Results & Metrics */}
            <div className="p-4 rounded-xl bg-gray-800/40 border border-gray-700/50 space-y-1.5">
              <h4 className="font-semibold text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-emerald-400" /> {t.metricsTitle}
              </h4>
              <p className="text-gray-300 leading-relaxed">
                {analysis.results || analysis.metrics || t.notExtractedYet}
              </p>
            </div>

            {/* Limitations */}
            <div className="p-4 rounded-xl bg-gray-800/40 border border-gray-700/50 space-y-1.5">
              <h4 className="font-semibold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> {t.limitationsTitle}
              </h4>
              <p className="text-gray-300 leading-relaxed">
                {analysis.limitations || t.notExtractedYet}
              </p>
            </div>
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-gray-800/30 border border-gray-800 text-center space-y-2">
            <BookOpen className="w-8 h-8 text-gray-500 mx-auto" />
            <p className="text-gray-400">
              {t.pendingAnalysisBadge}
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
};
