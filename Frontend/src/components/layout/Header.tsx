import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Settings as SettingsIcon,
  Plus,
  Server,
  Cpu,
  Menu,
  Languages,
  LogOut,
  ChevronDown,
  LogIn,
} from 'lucide-react';
import type { Session, SystemConfig } from '../../types';
import { useI18n } from '../../i18n/context';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  currentSession: Session | null;
  config: SystemConfig | null;
  backendHealthy: boolean;
  onOpenCreateSession: () => void;
  onOpenSettings: () => void;
  onOpenAuth: () => void;
  onToggleSidebar: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentSession,
  config,
  backendHealthy,
  onOpenCreateSession,
  onOpenSettings,
  onOpenAuth,
  onToggleSidebar,
}) => {
  const { language, setLanguage, t } = useI18n();
  const { user, isAuthenticated, logout } = useAuth();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-md border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand & Sidebar toggle */}
        <div className="flex items-center gap-3">
          <button
            onClick={onToggleSidebar}
            className="lg:hidden p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
            title="Toggle Sessions Sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-lg bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
                  PaperFlow
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {t.brandSubtitle}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Center: Current Session Topic */}
        <div className="hidden md:flex items-center max-w-md truncate px-3 py-1.5 rounded-lg bg-gray-800/40 border border-gray-800">
          <span className="text-xs text-gray-400 mr-2 shrink-0">{t.currentTopic}:</span>
          {currentSession ? (
            <span className="text-xs font-medium text-gray-200 truncate">
              {currentSession.topic}
            </span>
          ) : (
            <span className="text-xs text-gray-500 italic">{t.noSessionSelected}</span>
          )}
        </div>

        {/* Right: Status & Actions */}
        <div className="flex items-center gap-2.5">
          {/* Backend Status indicator */}
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-800/60 border border-gray-800 text-xs">
            <Server className="w-3.5 h-3.5 text-gray-400" />
            <span
              className={`w-2 h-2 rounded-full ${
                backendHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-gray-300 text-[11px]">
              {backendHealthy ? t.apiOnline : t.apiOffline}
            </span>
          </div>

          {/* Model indicator */}
          {config && (
            <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-800/60 border border-gray-800 text-xs">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-gray-300 font-mono text-[11px]">
                {config.llm_provider}: {config.default_model}
              </span>
            </div>
          )}

          {/* Language Switcher Toggle */}
          <button
            onClick={() => setLanguage(language === 'vi' ? 'en' : 'vi')}
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-xl bg-gray-800/80 hover:bg-gray-750 text-indigo-300 hover:text-white border border-gray-700 transition-all shadow-sm"
            title={language === 'vi' ? 'Switch to English' : 'Chuyển sang Tiếng Việt'}
          >
            <Languages className="w-3.5 h-3.5" />
            <span>{language === 'vi' ? 'VI' : 'EN'}</span>
          </button>

          {/* Settings button */}
          <button
            onClick={onOpenSettings}
            className="p-2 text-gray-300 hover:text-white rounded-xl bg-gray-800/60 hover:bg-gray-800 border border-gray-800 transition-colors"
            title={t.settingsTooltip}
          >
            <SettingsIcon className="w-4 h-4" />
          </button>

          {/* User Account / Login Button */}
          {isAuthenticated && user ? (
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-gray-800/80 hover:bg-gray-750 border border-gray-700 text-xs font-medium text-gray-200 transition-all"
              >
                <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-[10px] font-bold text-white uppercase">
                  {user.full_name ? user.full_name.charAt(0) : 'U'}
                </div>
                <span className="hidden sm:inline max-w-[100px] truncate">{user.full_name}</span>
                <ChevronDown className="w-3 h-3 text-gray-400" />
              </button>

              {/* Dropdown Menu */}
              {isUserMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-gray-900 border border-gray-800 shadow-2xl shadow-purple-950/40 p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  <div className="px-3 py-2 border-b border-gray-800/80 mb-1">
                    <p className="text-xs font-semibold text-gray-200 truncate">{user.full_name}</p>
                    <p className="text-[11px] text-gray-400 truncate">{user.email}</p>
                  </div>

                  <button
                    onClick={() => {
                      logout();
                      setIsUserMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 rounded-xl transition-colors"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>{t.logoutBtn}</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gray-800 hover:bg-gray-750 text-indigo-300 hover:text-white border border-indigo-500/40 text-xs font-semibold transition-all shadow-sm"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>{t.loginBtn}</span>
            </button>
          )}

          {/* Create session button */}
          <button
            onClick={onOpenCreateSession}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span>{t.newSessionBtn}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
