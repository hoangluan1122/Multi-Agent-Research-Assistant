/**
 * Component Modal Khởi Tạo Phiên Nghiên Cứu Mới (Create Session Modal - UC001):
 * - Form nhập chủ đề nghiên cứu (topic), câu hỏi nghiên cứu (research_question).
 * - Cấu hình khoảng năm xuất bản (year_start -> year_end), số lượng bài báo tối đa.
 * - Chọn các nguồn tìm kiếm (arXiv, Semantic Scholar) và chuẩn định dạng trích dẫn (IEEE / APA).
 */

import React, { useState } from 'react';
import { Sparkles, Calendar, Layers, CheckSquare, Square, Loader2 } from 'lucide-react';
import { Modal } from '../common/Modal';
import type { SessionCreate } from '../../types';
import { useI18n } from '../../i18n/context';

interface CreateSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: SessionCreate) => Promise<void>;
}

export const CreateSessionModal: React.FC<CreateSessionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const { t } = useI18n();
  const [topic, setTopic] = useState('');
  const [researchQuestion, setResearchQuestion] = useState('');
  const [yearStart, setYearStart] = useState<number>(2020);
  const [yearEnd, setYearEnd] = useState<number>(new Date().getFullYear());
  const [maxPapers, setMaxPapers] = useState<number>(5);
  const [sources, setSources] = useState<string[]>(['arxiv', 'semantic_scholar']);
  const [citationStyle, setCitationStyle] = useState<string>('IEEE');
  const [loading, setLoading] = useState(false);

  const toggleSource = (source: string) => {
    if (sources.includes(source)) {
      if (sources.length > 1) {
        setSources(sources.filter((s) => s !== source));
      }
    } else {
      setSources([...sources, source]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    try {
      await onSubmit({
        topic: topic.trim(),
        research_question: researchQuestion.trim() || undefined,
        year_start: Number(yearStart) || undefined,
        year_end: Number(yearEnd) || undefined,
        max_papers: Number(maxPapers) || 5,
        sources,
        citation_style: citationStyle,
      });
      // reset
      setTopic('');
      setResearchQuestion('');
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t.createSessionModalTitle}
      subtitle={t.createSessionModalSubtitle}
      maxWidth="2xl"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Topic */}
        <div>
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
            {t.topicLabel} <span className="text-rose-400">*</span>
          </label>
          <input
            type="text"
            required
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder={t.topicPlaceholder}
            className="w-full bg-gray-800/80 text-sm text-gray-100 px-3.5 py-2.5 rounded-xl border border-gray-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none placeholder-gray-500 transition-all"
          />
        </div>

        {/* Research Question */}
        <div>
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
            {t.questionLabel} {t.questionOptional}
          </label>
          <textarea
            rows={2}
            value={researchQuestion}
            onChange={(e) => setResearchQuestion(e.target.value)}
            placeholder={t.questionPlaceholder}
            className="w-full bg-gray-800/80 text-sm text-gray-100 px-3.5 py-2.5 rounded-xl border border-gray-700 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none placeholder-gray-500 transition-all resize-none"
          />
        </div>

        {/* Filters grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Year Range */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              {t.yearFromPlaceholder}
            </label>
            <input
              type="number"
              min={1990}
              max={2030}
              value={yearStart}
              onChange={(e) => setYearStart(Number(e.target.value))}
              className="w-full bg-gray-800/80 text-xs text-gray-100 px-3 py-2 rounded-lg border border-gray-700 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1 flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
              {t.yearToPlaceholder}
            </label>
            <input
              type="number"
              min={1990}
              max={2030}
              value={yearEnd}
              onChange={(e) => setYearEnd(Number(e.target.value))}
              className="w-full bg-gray-800/80 text-xs text-gray-100 px-3 py-2 rounded-lg border border-gray-700 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          {/* Max Papers */}
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              {t.maxPapersLabel}
            </label>
            <input
              type="number"
              min={1}
              max={30}
              value={maxPapers}
              onChange={(e) => setMaxPapers(Number(e.target.value))}
              className="w-full bg-gray-800/80 text-xs text-gray-100 px-3 py-2 rounded-lg border border-gray-700 focus:border-indigo-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Academic Sources & Citation Style */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          {/* Sources */}
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
              {t.sourcesSelectionLabel}
            </label>
            <div className="flex flex-col gap-2">
              {[
                { id: 'arxiv', label: 'arXiv API (Computer Science / AI / Physics)' },
                { id: 'semantic_scholar', label: 'Semantic Scholar API (All Domains)' },
              ].map((src) => {
                const isChecked = sources.includes(src.id);
                return (
                  <div
                    key={src.id}
                    onClick={() => toggleSource(src.id)}
                    className={`flex items-center gap-2.5 p-2 rounded-lg border cursor-pointer select-none transition-all ${
                      isChecked
                        ? 'bg-indigo-950/40 border-indigo-500/40 text-indigo-200'
                        : 'bg-gray-800/40 border-gray-700/50 text-gray-400 hover:border-gray-600'
                    }`}
                  >
                    {isChecked ? (
                      <CheckSquare className="w-4 h-4 text-indigo-400 shrink-0" />
                    ) : (
                      <Square className="w-4 h-4 text-gray-500 shrink-0" />
                    )}
                    <span className="text-xs font-medium">{src.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Citation Style */}
          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">
              {t.citationStyleLabel}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {['IEEE', 'APA', 'ACM', 'Harvard'].map((style) => (
                <button
                  type="button"
                  key={style}
                  onClick={() => setCitationStyle(style)}
                  className={`p-2.5 rounded-lg border text-xs font-semibold text-center transition-all ${
                    citationStyle === style
                      ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                      : 'bg-gray-800/40 border-gray-700/50 text-gray-300 hover:bg-gray-800 hover:border-gray-600'
                  }`}
                >
                  {style}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            {t.cancelBtn}
          </button>
          <button
            type="submit"
            disabled={loading || !topic.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t.workflowRunning}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>{t.submitCreateSessionBtn}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
