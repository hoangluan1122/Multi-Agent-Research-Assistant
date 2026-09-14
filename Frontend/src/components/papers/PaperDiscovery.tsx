/**
 * Component Khám phá & Quản lý Tài liệu Nghiên cứu (Paper Discovery Tab - UC002, UC003):
 * - Thanh tìm kiếm tài liệu từ các nguồn học thuật (arXiv, Semantic Scholar) với bộ lọc số lượng.
 * - Nút mở Modal tải lên tài liệu PDF trực tiếp.
 * - Các công cụ chọn hàng loạt (Select All / Deselect All).
 * - Lưới danh sách các thẻ bài báo (PaperCard Grid) và Modal hiển thị phân tích cấu trúc.
 */

import React, { useState } from 'react';
import {
  Search,
  UploadCloud,
  CheckSquare,
  Square,
  Filter,
  Loader2,
  FileText,
} from 'lucide-react';
import type { Session, Paper } from '../../types';
import { PaperCard } from './PaperCard';
import { PaperAnalysisModal } from './PaperAnalysisModal';
import { PdfUploadModal } from './PdfUploadModal';
import { useI18n } from '../../i18n/context';

interface PaperDiscoveryProps {
  session: Session;
  papers: Paper[];
  isLoading?: boolean;
  onSearchPapers: (
    query: string,
    maxResults: number,
    sources: string[],
    yearStart?: number,
    yearEnd?: number
  ) => Promise<void>;
  onUploadPaper: (file: File) => Promise<void>;
  onToggleSelectPaper: (paper: Paper) => Promise<void>;
  onBatchSelectPapers: (isSelected: boolean) => Promise<void>;
  onAnalyzePaper: (paperId: string) => Promise<void>;
  onTranslatePaper?: (paperId: string) => Promise<void>;
  onTranslateAllPapers?: () => Promise<void>;
}

export const PaperDiscovery: React.FC<PaperDiscoveryProps> = ({
  session,
  papers,
  onSearchPapers,
  onUploadPaper,
  onToggleSelectPaper,
  onBatchSelectPapers,
  onAnalyzePaper,
  onTranslatePaper,
  onTranslateAllPapers,
}) => {
  const { t } = useI18n();
  const [query, setQuery] = useState(session.topic);
  const [maxResults, setMaxResults] = useState(5);
  const [sources, setSources] = useState<string[]>(['arxiv', 'semantic_scholar']);
  const [yearStart, setYearStart] = useState<string>('');
  const [yearEnd, setYearEnd] = useState<string>('');
  const [isSearching, setIsSearching] = useState(false);
  const [isTranslatingAll, setIsTranslatingAll] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedAnalysisPaper, setSelectedAnalysisPaper] = useState<Paper | null>(null);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);

  const toggleSource = (s: string) => {
    if (sources.includes(s)) {
      if (sources.length > 1) setSources(sources.filter((x) => x !== s));
    } else {
      setSources([...sources, s]);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    try {
      await onSearchPapers(
        query.trim(),
        maxResults,
        sources,
        yearStart ? parseInt(yearStart, 10) : undefined,
        yearEnd ? parseInt(yearEnd, 10) : undefined
      );
    } finally {
      setIsSearching(false);
    }
  };

  const handleOpenAnalysis = async (paper: Paper) => {
    if (!paper.analysis) {
      try {
        await onAnalyzePaper(paper.id);
      } catch (err) {
        console.error(err);
      }
    }
    setSelectedAnalysisPaper(paper);
    setIsAnalysisOpen(true);
  };

  const selectedCount = papers.filter((p) => p.is_selected).length;

  return (
    <div className="space-y-6">
      {/* Search & Actions Bar */}
      <div className="p-6 rounded-2xl bg-gray-900/70 border border-gray-800 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Search className="w-4 h-4 text-indigo-400" />
              {t.discoveryTitle}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {t.discoveryDesc}
            </p>
          </div>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-indigo-300 hover:text-white border border-gray-700 text-xs font-semibold transition-all shadow-sm shrink-0"
          >
            <UploadCloud className="w-4 h-4" />
            <span>{t.uploadPdfBtn}</span>
          </button>
        </div>

        {/* Search Input & Options Form */}
        <form onSubmit={handleSearch} className="space-y-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t.searchPlaceholder}
                className="w-full bg-gray-800/80 text-sm text-gray-100 pl-10 pr-4 py-2.5 rounded-xl border border-gray-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none placeholder-gray-500 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 shrink-0"
            >
              {isSearching ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t.searchingBtn}</span>
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  <span>{t.searchBtn}</span>
                </>
              )}
            </button>
          </div>

          {/* Sources & Limit Filters */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs">
            <div className="flex flex-wrap items-center gap-4">
              <span className="text-gray-400 font-medium flex items-center gap-1">
                <Filter className="w-3.5 h-3.5 text-indigo-400" /> {t.sourcesLabel}
              </span>

              {[
                { id: 'arxiv', label: 'arXiv' },
                { id: 'semantic_scholar', label: 'Semantic Scholar' },
              ].map((src) => {
                const isChecked = sources.includes(src.id);
                return (
                  <button
                    type="button"
                    key={src.id}
                    onClick={() => toggleSource(src.id)}
                    className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium transition-all ${
                      isChecked
                        ? 'bg-indigo-950/50 border-indigo-500/50 text-indigo-300'
                        : 'bg-gray-800/40 border-gray-700/50 text-gray-500 hover:border-gray-600'
                    }`}
                  >
                    {isChecked ? (
                      <CheckSquare className="w-3.5 h-3.5 text-indigo-400" />
                    ) : (
                      <Square className="w-3.5 h-3.5 text-gray-500" />
                    )}
                    <span>{src.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Year Filters */}
            <div className="flex items-center gap-1.5">
              <span className="text-gray-400">{t.yearLabel}</span>
              <input
                type="number"
                value={yearStart}
                onChange={(e) => setYearStart(e.target.value)}
                placeholder={t.yearFromPlaceholder}
                className="w-16 bg-gray-800 text-xs text-gray-200 px-2 py-1 rounded-lg border border-gray-700 focus:border-indigo-500 focus:outline-none placeholder-gray-500"
              />
              <span className="text-gray-500">-</span>
              <input
                type="number"
                value={yearEnd}
                onChange={(e) => setYearEnd(e.target.value)}
                placeholder={t.yearToPlaceholder}
                className="w-16 bg-gray-800 text-xs text-gray-200 px-2 py-1 rounded-lg border border-gray-700 focus:border-indigo-500 focus:outline-none placeholder-gray-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-gray-400">{t.maxResultsLabel}</span>
              <select
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
                className="bg-gray-800 text-xs text-gray-200 px-2.5 py-1 rounded-lg border border-gray-700 focus:border-indigo-500 focus:outline-none"
              >
                <option value={3}>3 {t.papersCountUnit}</option>
                <option value={5}>5 {t.papersCountUnit}</option>
                <option value={10}>10 {t.papersCountUnit}</option>
                <option value={15}>15 {t.papersCountUnit}</option>
              </select>
            </div>
          </div>
        </form>
      </div>

      {/* Papers Header & Batch Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">
            {t.papersInSession} ({papers.length})
          </h3>
          <span className="text-xs text-indigo-400 font-medium">
            ({t.selectedCount}: {selectedCount}/{papers.length})
          </span>
        </div>

        {papers.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {onTranslateAllPapers && (
              <button
                onClick={async () => {
                  setIsTranslatingAll(true);
                  try {
                    await onTranslateAllPapers();
                  } finally {
                    setIsTranslatingAll(false);
                  }
                }}
                disabled={isTranslatingAll}
                className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-900/60 hover:bg-indigo-800 text-indigo-200 hover:text-white border border-indigo-500/50 font-medium transition-all shadow-sm disabled:opacity-50"
              >
                {isTranslatingAll ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>{t.translatingAllBtn}</span>
                  </>
                ) : (
                  <span>{t.translateAllBtn}</span>
                )}
              </button>
            )}
            <button
              onClick={() => onBatchSelectPapers(true)}
              className="px-3 py-1 rounded-lg bg-gray-800 hover:bg-gray-750 text-gray-300 hover:text-white border border-gray-700 transition-colors"
            >
              {t.selectAllBtn}
            </button>
            <button
              onClick={() => onBatchSelectPapers(false)}
              className="px-3 py-1 rounded-lg bg-gray-800 hover:bg-gray-750 text-gray-300 hover:text-white border border-gray-700 transition-colors"
            >
              {t.deselectAllBtn}
            </button>
          </div>
        )}
      </div>

      {/* Papers Grid */}
      {papers.length === 0 ? (
        <div className="p-12 rounded-2xl bg-gray-900/30 border border-gray-800 text-center space-y-3">
          <FileText className="w-10 h-10 text-gray-600 mx-auto" />
          <div className="space-y-1">
            <p className="text-sm font-semibold text-gray-300">
              {t.noPapersInSession}
            </p>
            <p className="text-xs text-gray-500 max-w-md mx-auto">
              {t.noPapersInSessionDesc}
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {papers.map((paper) => (
            <PaperCard
              key={paper.id}
              paper={paper}
              onToggleSelect={onToggleSelectPaper}
              onViewAnalysis={handleOpenAnalysis}
              onTranslate={onTranslatePaper}
            />
          ))}
        </div>
      )}

      {/* Upload Modal */}
      <PdfUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={onUploadPaper}
      />

      {/* Analysis Modal */}
      <PaperAnalysisModal
        paper={selectedAnalysisPaper}
        isOpen={isAnalysisOpen}
        onClose={() => setIsAnalysisOpen(false)}
      />
    </div>
  );
};
