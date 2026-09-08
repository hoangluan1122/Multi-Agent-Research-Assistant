/**
 * Component Thẻ hiển thị Bài báo Khoa học (Paper Card):
 * - Hiển thị tiêu đề, tác giả, năm, nơi xuất bản, nguồn tài liệu (arXiv, Semantic Scholar, Upload).
 * - Hiển thị tóm tắt abstract thu gọn.
 * - Nút chọn lọc (Checkbox toggle) để đưa bài báo vào quy trình phân tích và viết báo cáo.
 * - Nút xem chi tiết cấu trúc (View Analysis) nếu đã qua xử lý bởi ReadingAgent.
 */

import React, { useState } from 'react';
import {
  CheckSquare,
  Square,
  ExternalLink,
  BookOpen,
  Sparkles,
  Languages,
  Loader2,
} from 'lucide-react';
import type { Paper } from '../../types';
import { Badge } from '../common/Badge';
import { useI18n } from '../../i18n/context';

interface PaperCardProps {
  paper: Paper;
  onToggleSelect: (paper: Paper) => void;
  onViewAnalysis: (paper: Paper) => void;
  onRunAnalysis?: (paper: Paper) => void;
  onTranslate?: (paperId: string) => Promise<void>;
}

export const PaperCard: React.FC<PaperCardProps> = ({
  paper,
  onToggleSelect,
  onViewAnalysis,
  onTranslate,
}) => {
  const { t } = useI18n();
  const [isTranslating, setIsTranslating] = useState(false);

  const handleTranslate = async () => {
    if (!onTranslate) return;
    setIsTranslating(true);
    try {
      await onTranslate(paper.id);
    } finally {
      setIsTranslating(false);
    }
  };

  const getSourceBadge = (source: string) => {
    switch (source.toLowerCase()) {
      case 'arxiv':
        return <Badge variant="primary">arXiv</Badge>;
      case 'semantic_scholar':
        return <Badge variant="info">Semantic Scholar</Badge>;
      case 'upload':
        return <Badge variant="success">{t.uploadedPdfBadge}</Badge>;
      default:
        return <Badge variant="neutral">{source}</Badge>;
    }
  };

  return (
    <div
      className={`relative p-5 rounded-2xl border transition-all flex flex-col justify-between gap-4 ${
        paper.is_selected
          ? 'bg-gray-900/90 border-indigo-500/60 shadow-lg shadow-indigo-950/30'
          : 'bg-gray-900/40 border-gray-800 hover:border-gray-700'
      }`}
    >
      {/* Top Header */}
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            {getSourceBadge(paper.source)}
            {paper.year && (
              <span className="text-[11px] font-medium text-gray-400 px-2 py-0.5 rounded bg-gray-800 border border-gray-700/60">
                {paper.year}
              </span>
            )}
            <Badge variant="neutral">
              {t.relevanceLabel} {(paper.relevance_score * 100).toFixed(0)}%
            </Badge>
          </div>

          {/* Select Checkbox */}
          <button
            onClick={() => onToggleSelect(paper)}
            className="text-gray-400 hover:text-white transition-colors"
            title={paper.is_selected ? t.deselectAllBtn : t.selectAllBtn}
          >
            {paper.is_selected ? (
              <CheckSquare className="w-5 h-5 text-indigo-400" />
            ) : (
              <Square className="w-5 h-5 text-gray-600 hover:text-gray-400" />
            )}
          </button>
        </div>

        {/* Title */}
        <h4 className="text-sm font-bold text-gray-100 line-clamp-2 leading-snug">
          {paper.title}
        </h4>

        {/* Authors & Venue */}
        <p className="text-[11px] text-gray-400 line-clamp-1">
          <span className="font-semibold text-gray-300">{t.authorsLabel}</span>{' '}
          {paper.authors.length > 0 ? paper.authors.join(', ') : 'N/A'}
        </p>

        {/* Abstract snippet */}
        {paper.abstract && (
          <p className="text-xs text-gray-400 line-clamp-3 leading-relaxed mt-2 bg-gray-950/40 p-2.5 rounded-xl border border-gray-800/80">
            {paper.abstract}
          </p>
        )}
      </div>

      {/* Footer Actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-gray-800/80 text-xs">
        {/* Analysis Status */}
        <div>
          {paper.analysis ? (
            <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
              <Sparkles className="w-3 h-3" /> {t.analyzedBadge}
            </span>
          ) : (
            <span className="text-[11px] text-gray-500">{t.pendingAnalysisBadge}</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onTranslate && (
            <button
              onClick={handleTranslate}
              disabled={isTranslating}
              className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-indigo-300 border border-gray-700/60 font-medium text-xs transition-colors disabled:opacity-50"
              title="Dịch tiêu đề và tóm tắt sang Tiếng Việt"
            >
              {isTranslating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
              ) : (
                <Languages className="w-3.5 h-3.5" />
              )}
              <span>{isTranslating ? t.translatingCardBtn : t.translateCardBtn}</span>
            </button>
          )}

          <button
            onClick={() => onViewAnalysis(paper)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-indigo-300 hover:text-white border border-gray-700/60 font-medium text-xs transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>{t.viewAnalysisBtn}</span>
          </button>

          {paper.url && (
            <a
              href={paper.url}
              target="_blank"
              rel="noreferrer"
              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
              title={t.openOriginalLink}
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
