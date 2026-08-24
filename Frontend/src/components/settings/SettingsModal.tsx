/**
 * Component Modal Cài Đặt Hệ Thống & LLM (Settings Modal - UC013):
 * - Chọn nhà cung cấp mô hình (Gemini / OpenAI).
 * - Nhập mã mô hình LLM, khóa API bí mật (API Key) và Base URL.
 * - Cấu hình tham số vận hành: Số lượng bài báo tối đa khi tìm kiếm, Số lần retry phản biện.
 * - Nút kiểm tra kết nối trực tiếp (Test Connection) với nhà cung cấp LLM.
 */

import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import type { SystemConfig, SystemConfigUpdate } from '../../types';
import { Cpu, Key, Server, CheckCircle2, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { Badge } from '../common/Badge';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: SystemConfig | null;
  onSave: (update: SystemConfigUpdate) => Promise<void>;
  onTestLlm: () => Promise<{ status: string; message: string; response?: string }>;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  config,
  onSave,
  onTestLlm,
}) => {
  const [provider, setProvider] = useState<string>('gemini');
  const [model, setModel] = useState<string>('gemini-2.5-flash');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [openaiKey, setOpenaiKey] = useState<string>('');
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState<string>('');
  const [maxSearch, setMaxSearch] = useState<number>(10);
  const [maxRetries, setMaxRetries] = useState<number>(2);

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ status: string; message: string; response?: string } | null>(null);

  useEffect(() => {
    if (config) {
      setProvider(config.llm_provider || 'gemini');
      setModel(config.default_model || 'gemini-2.5-flash');
      setMaxSearch(config.max_search_papers || 10);
      setMaxRetries(config.max_review_retries || 2);
    }
  }, [config]);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await onTestLlm();
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        status: 'error',
        message: err.message || 'Kiểm tra kết nối thất bại',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({
        llm_provider: provider,
        default_model: model,
        gemini_api_key: geminiKey.trim() || undefined,
        openai_api_key: openaiKey.trim() || undefined,
        openai_base_url: openaiBaseUrl.trim() || undefined,
        max_search_papers: Number(maxSearch),
        max_review_retries: Number(maxRetries),
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Cài Đặt Hệ Thống & Mô Hình AI"
      subtitle="Quản lý LLM Provider, API Keys và các tham số điều phối Multi-Agent"
      maxWidth="2xl"
    >
      <form onSubmit={handleSave} className="space-y-4 text-xs">
        {/* Provider Selection */}
        <div>
          <label className="block font-semibold text-gray-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" /> Nhà cung cấp LLM (Provider)
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { id: 'gemini', label: 'Google Gemini' },
              { id: 'openai', label: 'OpenAI' },
              { id: 'groq', label: 'Groq Cloud' },
              { id: 'openrouter', label: 'OpenRouter' },
            ].map((p) => (
              <button
                type="button"
                key={p.id}
                onClick={() => {
                  setProvider(p.id);
                  if (p.id === 'gemini') setModel('gemini-2.5-flash');
                  if (p.id === 'openai') setModel('gpt-4o-mini');
                  if (p.id === 'groq') setModel('llama-3.3-70b-versatile');
                  if (p.id === 'openrouter') setModel('deepseek/deepseek-chat');
                }}
                className={`p-2.5 rounded-xl border font-semibold text-center transition-all ${
                  provider === p.id
                    ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                    : 'bg-gray-800/40 border-gray-700/60 text-gray-300 hover:bg-gray-800'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Model Name */}
        <div>
          <label className="block font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
            Tên Mô Hình Mặc Định
          </label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="Ví dụ: gemini-2.5-flash hoặc gpt-4o-mini"
            className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
          />
        </div>

        {/* API Keys */}
        <div className="space-y-3 pt-1">
          {provider === 'gemini' ? (
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="font-semibold text-gray-300 flex items-center gap-1.5">
                  <Key className="w-3.5 h-3.5 text-indigo-400" /> Gemini API Key
                </label>
                {config?.has_gemini_key && (
                  <Badge variant="success">Key đã được cấu hình trong .env</Badge>
                )}
              </div>
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="Nhập Gemini API Key mới (để trống nếu dùng key hiện tại)..."
                className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
              />
            </div>
          ) : (
            <div className="space-y-2">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-semibold text-gray-300 flex items-center gap-1.5">
                    <Key className="w-3.5 h-3.5 text-indigo-400" /> API Key ({provider.toUpperCase()})
                  </label>
                  {config?.has_openai_key && (
                    <Badge variant="success">Key đã được cấu hình</Badge>
                  )}
                </div>
                <input
                  type="password"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder={`Nhập ${provider.toUpperCase()} API Key...`}
                  className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
                />
              </div>

              {(provider === 'groq' || provider === 'openrouter') && (
                <div>
                  <label className="font-semibold text-gray-400 mb-1 block">
                    Custom Base URL (Tùy chọn)
                  </label>
                  <input
                    type="text"
                    value={openaiBaseUrl}
                    onChange={(e) => setOpenaiBaseUrl(e.target.value)}
                    placeholder={
                      provider === 'groq'
                        ? 'https://api.groq.com/openai/v1'
                        : 'https://openrouter.ai/api/v1'
                    }
                    className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono text-[11px]"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Vector DB Status */}
        <div className="p-3 rounded-xl bg-gray-800/40 border border-gray-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-indigo-400" />
            <span className="text-gray-300 font-medium">Vector Store (Qdrant)</span>
          </div>
          <Badge variant={config?.qdrant_use_memory ? 'info' : 'success'}>
            {config?.qdrant_use_memory ? 'In-Memory (RAM)' : 'Qdrant Host'}
          </Badge>
        </div>

        {/* Test Connection Button & Result */}
        <div className="space-y-2 pt-2">
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testing}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-indigo-300 hover:text-white border border-gray-700 text-xs font-semibold transition-all"
          >
            {testing ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Đang gửi truy vấn kiểm tra...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Kiểm tra kết nối LLM</span>
              </>
            )}
          </button>

          {testResult && (
            <div
              className={`p-3 rounded-xl border text-xs ${
                testResult.status === 'ok'
                  ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-200'
                  : 'bg-rose-950/40 border-rose-500/40 text-rose-200'
              }`}
            >
              <div className="flex items-center gap-1.5 font-semibold">
                {testResult.status === 'ok' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400" />
                )}
                <span>{testResult.message}</span>
              </div>
              {testResult.response && (
                <p className="mt-1 text-[11px] font-mono text-gray-300">
                  Phản hồi từ AI: "{testResult.response}"
                </p>
              )}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-medium text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            Đóng
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Đang lưu...</span>
              </>
            ) : (
              <span>Lưu Cài Đặt</span>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
