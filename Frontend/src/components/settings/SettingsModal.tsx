// @trace: REQ-011, REQ-012
import React, { useState, useEffect } from 'react';
import { Modal } from '../common/Modal';
import type { SystemConfig, SystemConfigUpdate } from '../../types';
import { Cpu, Key, Server, CheckCircle2, AlertCircle, Loader2, Sparkles, Languages, Globe, ShieldCheck } from 'lucide-react';
import { Badge } from '../common/Badge';
import { useI18n } from '../../i18n/context';

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
  const { language, setLanguage, t } = useI18n();

  // @trace: REQ-012: Chế độ API ('system' = API Web có sẵn, 'custom' = API cá nhân)
  const [apiMode, setApiMode] = useState<'system' | 'custom'>('system');
  const [provider, setProvider] = useState<string>('gemini');
  const [model, setModel] = useState<string>('gemini-3.7-flash');
  const [geminiKey, setGeminiKey] = useState<string>('');
  const [openaiKey, setOpenaiKey] = useState<string>('');
  const [openaiBaseUrl, setOpenaiBaseUrl] = useState<string>('');
  const [semanticScholarKey, setSemanticScholarKey] = useState<string>('');
  const [openAlexKey, setOpenAlexKey] = useState<string>('');
  const [maxSearch, setMaxSearch] = useState<number>(10);
  const [maxRetries, setMaxRetries] = useState<number>(2);

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ status: string; message: string; response?: string } | null>(null);

  useEffect(() => {
    if (config) {
      // Xác định chế độ đang dùng từ backend hoặc localStorage
      const savedMode = localStorage.getItem('paperflow_api_mode');
      if (config.use_system_key === false || savedMode === 'custom') {
        setApiMode('custom');
      } else {
        setApiMode('system');
      }

      setProvider(config.llm_provider || 'gemini');
      setModel(config.default_model || 'gemini-3.7-flash');
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

  // @trace: REQ-011, REQ-012
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (apiMode === 'system') {
        // Lưu cấu hình sử dụng API mặc định của Web
        await onSave({
          use_system_default: true,
          llm_provider: provider,
          default_model: model,
          semantic_scholar_api_key: semanticScholarKey.trim() || undefined,
          openalex_api_key: openAlexKey.trim() || undefined,
          max_search_papers: Number(maxSearch),
          max_review_retries: Number(maxRetries),
        });
        localStorage.setItem('paperflow_api_mode', 'system');
      } else {
        // Lưu cấu hình sử dụng API cá nhân của người dùng
        await onSave({
          use_system_default: false,
          llm_provider: provider,
          default_model: model,
          gemini_api_key: provider === 'gemini' ? (geminiKey.trim() || undefined) : undefined,
          openai_api_key: provider !== 'gemini' ? (openaiKey.trim() || undefined) : undefined,
          openai_base_url: (provider === 'groq' || provider === 'openrouter') ? (openaiBaseUrl.trim() || undefined) : undefined,
          semantic_scholar_api_key: semanticScholarKey.trim() || undefined,
          openalex_api_key: openAlexKey.trim() || undefined,
          max_search_papers: Number(maxSearch),
          max_review_retries: Number(maxRetries),
        });
        localStorage.setItem('paperflow_api_mode', 'custom');
      }
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t.settingsModalTitle}
      subtitle={t.settingsModalSubtitle}
      maxWidth="2xl"
    >
      <form onSubmit={handleSave} className="space-y-4 text-xs">
        {/* Language Selection */}
        <div>
          <label className="block font-semibold text-gray-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Languages className="w-3.5 h-3.5 text-indigo-400" /> {t.languageSettingLabel}
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setLanguage('vi')}
              className={`p-2.5 rounded-xl border font-semibold text-center transition-all flex items-center justify-center gap-2 ${
                language === 'vi'
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-gray-800/40 border-gray-700/60 text-gray-300 hover:bg-gray-800'
              }`}
            >
              <span>🇻🇳 Tiếng Việt</span>
            </button>
            <button
              type="button"
              onClick={() => setLanguage('en')}
              className={`p-2.5 rounded-xl border font-semibold text-center transition-all flex items-center justify-center gap-2 ${
                language === 'en'
                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-gray-800/40 border-gray-700/60 text-gray-300 hover:bg-gray-800'
              }`}
            >
              <span>🇬🇧 English</span>
            </button>
          </div>
        </div>

        {/* @trace: REQ-012: Chọn Chế độ Nguồn API (Web Default vs Custom API) */}
        <div>
          <label className="block font-semibold text-gray-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> {t.apiSourceModeLabel}
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Chế độ 1: API Mặc định của Web */}
            <div
              onClick={() => {
                setApiMode('system');
                setProvider('gemini');
                setModel('gemini-3.7-flash');
              }}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                apiMode === 'system'
                  ? 'bg-indigo-950/40 border-indigo-500 text-white ring-1 ring-indigo-500/50 shadow-lg shadow-indigo-900/20'
                  : 'bg-gray-800/30 border-gray-700/60 text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-[13px] flex items-center gap-1.5 text-indigo-200">
                    <Globe className="w-4 h-4 text-indigo-400" /> {t.apiModeSystem}
                  </span>
                  <Badge variant="success">Miễn phí</Badge>
                </div>
                <p className="text-[11px] text-gray-300 leading-relaxed">
                  {t.apiModeSystemDesc}
                </p>
              </div>
              <div className="mt-2.5 pt-2 border-t border-gray-700/50 flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
                <ShieldCheck className="w-3 h-3" />
                <span>Không cần cấu hình khóa API riêng</span>
              </div>
            </div>

            {/* Chế độ 2: API Cá nhân tự cấu hình */}
            <div
              onClick={() => {
                setApiMode('custom');
              }}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                apiMode === 'custom'
                  ? 'bg-indigo-950/40 border-indigo-500 text-white ring-1 ring-indigo-500/50 shadow-lg shadow-indigo-900/20'
                  : 'bg-gray-800/30 border-gray-700/60 text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-[13px] flex items-center gap-1.5 text-indigo-200">
                    <Key className="w-4 h-4 text-indigo-400" /> {t.apiModeCustom}
                  </span>
                  <Badge variant="info">Tùy biến</Badge>
                </div>
                <p className="text-[11px] text-gray-300 leading-relaxed">
                  {t.apiModeCustomDesc}
                </p>
              </div>
              <div className="mt-2.5 pt-2 border-t border-gray-700/50 flex items-center gap-1 text-[10px] text-indigo-400 font-medium">
                <Cpu className="w-3 h-3" />
                <span>Hỗ trợ Gemini, OpenAI, Groq, OpenRouter</span>
              </div>
            </div>
          </div>
        </div>

        {/* Nội dung cấu hình theo Chế độ được chọn */}
        {apiMode === 'system' ? (
          /* Chế độ API Mặc định của Web */
          <div className="p-3.5 rounded-xl bg-gradient-to-br from-indigo-950/30 via-gray-800/40 to-gray-900/50 border border-indigo-500/30 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                Mô hình AI máy chủ phục vụ
              </span>
              <Badge variant="success">Hệ thống kích hoạt sẵn</Badge>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
              {/* @trace: REQ-038 */}
              {[
                { id: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', tag: 'Mặc định - Mới nhất & Thông minh' },
                { id: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash', tag: 'Bản ổn định - Cực nhanh' },
                { id: 'gpt-4o-mini', label: 'GPT-4o Mini', tag: 'OpenAI Fallback' },
              ].map((m) => (

                <button
                  type="button"
                  key={m.id}
                  onClick={() => {
                    setModel(m.id);
                    if (m.id.startsWith('gemini')) setProvider('gemini');
                    else setProvider('openai');
                  }}
                  className={`p-2 rounded-lg border text-left transition-all ${
                    model === m.id
                      ? 'bg-indigo-600/40 border-indigo-400 text-white shadow-sm'
                      : 'bg-gray-800/60 border-gray-700/60 text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  <div className="font-semibold text-[11px] text-white">{m.label}</div>
                  <div className="text-[10px] text-indigo-300">{m.tag}</div>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Chế độ API Cá nhân */
          <div className="space-y-3 p-3.5 rounded-xl bg-gray-900/60 border border-gray-700/60">
            {/* Provider Selection */}
            <div>
              <label className="block font-semibold text-gray-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" /> {t.providerLabel}
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
                {t.defaultModelLabel}
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="Ví dụ: gemini-2.0-flash, gemini-1.5-flash, gpt-4o, llama-3.3-70b-versatile"
                className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
              />
            </div>

            {/* API Keys */}
            <div className="space-y-3 pt-1">
              {provider === 'gemini' ? (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="font-semibold text-gray-300 flex items-center gap-1.5">
                      <Key className="w-3.5 h-3.5 text-indigo-400" /> {t.geminiKeyLabel}
                    </label>
                    <div className="flex items-center gap-2">
                      <a
                        href="https://aistudio.google.com/app/apikey"
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-indigo-400 hover:text-indigo-300 underline"
                      >
                        Lấy API Key miễn phí ↗
                      </a>
                      {config?.has_gemini_key && (
                        <Badge variant="success">{t.keyConfiguredEnv}</Badge>
                      )}
                    </div>
                  </div>
                  <input
                    type="password"
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    placeholder={t.geminiKeyPlaceholder}
                    className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
                  />
                </div>
              ) : (
                <div className="space-y-2">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="font-semibold text-gray-300 flex items-center gap-1.5">
                        <Key className="w-3.5 h-3.5 text-indigo-400" /> {t.apiKeyLabel} ({provider.toUpperCase()})
                      </label>
                      {config?.has_openai_key && (
                        <Badge variant="success">{t.keyConfigured}</Badge>
                      )}
                    </div>
                    <input
                      type="password"
                      value={openaiKey}
                      onChange={(e) => setOpenaiKey(e.target.value)}
                      placeholder={t.apiKeyPlaceholder}
                      className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
                    />
                  </div>

                  {(provider === 'groq' || provider === 'openrouter') && (
                    <div>
                      <label className="font-semibold text-gray-400 mb-1 block">
                        {t.customBaseUrl}
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
          </div>
        )}

        <div className="space-y-2 p-3.5 rounded-xl bg-gray-900/60 border border-gray-700/60">
          <div className="flex items-center justify-between gap-2">
            <label className="font-semibold text-gray-300 flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-indigo-400" /> Semantic Scholar API Key
            </label>
            {config?.has_semantic_scholar_key && (
              <Badge variant="success">{t.keyConfigured}</Badge>
            )}
          </div>
          <input
            type="password"
            value={semanticScholarKey}
            onChange={(e) => setSemanticScholarKey(e.target.value)}
            placeholder="Optional, helps avoid Semantic Scholar 429 rate limits"
            className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
          />
        </div>

        <div className="space-y-2 p-3.5 rounded-xl bg-gray-900/60 border border-gray-700/60">
          <div className="flex items-center justify-between gap-2">
            <label className="font-semibold text-gray-300 flex items-center gap-1.5">
              <Key className="w-3.5 h-3.5 text-indigo-400" /> OpenAlex API Key
            </label>
            {config?.has_openalex_key && (
              <Badge variant="success">{t.keyConfigured}</Badge>
            )}
          </div>
          <input
            type="password"
            value={openAlexKey}
            onChange={(e) => setOpenAlexKey(e.target.value)}
            placeholder="Optional OpenAlex API key"
            className="w-full bg-gray-800/80 text-gray-100 px-3.5 py-2 rounded-xl border border-gray-700 focus:border-indigo-500 focus:outline-none font-mono"
          />
        </div>

        {/* Vector DB Status */}
        <div className="p-3 rounded-xl bg-gray-800/40 border border-gray-700/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-indigo-400" />
            <span className="text-gray-300 font-medium">{t.vectorStoreLabel}</span>
          </div>
          <Badge variant={config?.qdrant_use_memory ? 'info' : 'success'}>
            {config?.qdrant_use_memory ? t.inMemoryBadge : t.qdrantHostBadge}
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
                <span>{t.testingConnectionBtn}</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>{t.testConnectionBtn}</span>
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
                  {t.aiResponseLabel} "{testResult.response}"
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
            {t.closeBtn}
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{t.savingSettingsBtn}</span>
              </>
            ) : (
              <span>{t.saveSettingsBtn}</span>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
