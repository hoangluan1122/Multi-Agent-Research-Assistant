// @trace: REQ-VO-002, REQ-VO-003
import React from 'react';
import { Sparkles, AlertCircle, CheckCircle2, Search, BookOpen, FileSpreadsheet, PenTool, Award, Quote } from 'lucide-react';
import './officeTheme.css';

export type CharacterStatus = 'running' | 'completed' | 'failed' | 'idle';

interface AgentCharacterProps {
  agentName: string;
  status: CharacterStatus;
  currentTask?: string;
}

export const AgentCharacter: React.FC<AgentCharacterProps> = ({
  agentName,
  status,
  currentTask,
}) => {
  // Mascot scarf / accessory color per agent role
  const getTheme = () => {
    switch (agentName) {
      case 'SearchAgent':
        return {
          scarf: '#38bdf8', // Sky blue
          badgeIcon: <Search className="w-2.5 h-2.5 text-sky-300" />,
          title: 'Searcher',
          roleColor: 'bg-sky-500',
        };
      case 'ReadingAgent':
        return {
          scarf: '#34d399', // Emerald green
          badgeIcon: <BookOpen className="w-2.5 h-2.5 text-emerald-300" />,
          title: 'Reader',
          roleColor: 'bg-emerald-500',
        };
      case 'SummarizationAgent':
        return {
          scarf: '#fbbf24', // Amber gold
          badgeIcon: <FileSpreadsheet className="w-2.5 h-2.5 text-amber-300" />,
          title: 'Summarizer',
          roleColor: 'bg-amber-500',
        };
      case 'WritingAgent':
        return {
          scarf: '#818cf8', // Indigo
          badgeIcon: <PenTool className="w-2.5 h-2.5 text-indigo-300" />,
          title: 'Writer',
          roleColor: 'bg-indigo-500',
        };
      case 'ReviewAgent':
        return {
          scarf: '#f43f5e', // Rose red
          badgeIcon: <Award className="w-2.5 h-2.5 text-rose-300" />,
          title: 'Reviewer',
          roleColor: 'bg-rose-500',
        };
      case 'CitationAgent':
        return {
          scarf: '#a855f7', // Purple
          badgeIcon: <Quote className="w-2.5 h-2.5 text-purple-300" />,
          title: 'Citator',
          roleColor: 'bg-purple-500',
        };
      default:
        return {
          scarf: '#6366f1',
          badgeIcon: <Sparkles className="w-2.5 h-2.5 text-indigo-300" />,
          title: 'Agent',
          roleColor: 'bg-indigo-500',
        };
    }
  };

  const theme = getTheme();

  return (
    <div className="relative flex flex-col items-center select-none">
      {/* 1. Status Bubble / Thinking Dialog Above Character */}
      {status === 'running' && (
        <div className="absolute -top-11 z-30 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-900/90 border border-indigo-400/60 shadow-lg shadow-indigo-500/30 text-[10px] text-indigo-100 font-medium whitespace-nowrap animate-bounce">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          <span className="truncate max-w-[120px]">{currentTask || 'Đang xử lý...'}</span>
        </div>
      )}

      {status === 'idle' && (
        <div className="absolute -top-7 right-0 z-20 pointer-events-none">
          <span className="absolute text-gray-400 font-bold text-xs anim-zzz-1">z</span>
          <span className="absolute text-gray-400 font-bold text-sm anim-zzz-2">Z</span>
          <span className="absolute text-indigo-300 font-bold text-base anim-zzz-3">Z</span>
        </div>
      )}

      {status === 'completed' && (
        <div className="absolute -top-7 z-20 flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-500/50 text-[10px] text-emerald-300 shadow-md">
          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
          <span>Xong</span>
        </div>
      )}

      {status === 'failed' && (
        <div className="absolute -top-7 z-20 flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-950/80 border border-rose-500/50 text-[10px] text-rose-300 shadow-md">
          <AlertCircle className="w-3 h-3 text-rose-400" />
          <span>Lỗi</span>
        </div>
      )}

      {/* 2. Character SVG Mascot (Cute tech mascot inspired by Marvis Office) */}
      <div className={`relative transition-transform duration-300 ${status === 'running' ? 'anim-head-bob' : ''} ${status === 'completed' ? 'anim-celebrate' : ''}`}>
        <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-md">
          {/* Swivel Chair Back */}
          <rect x="20" y="32" width="32" height="28" rx="8" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
          <circle cx="36" cy="62" r="3" fill="#0f172a" />
          <path d="M30 65 L42 65 M36 60 L36 65" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

          {/* Character Body (Dark Fur/Suit) */}
          <rect x="23" y="24" width="26" height="26" rx="8" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />

          {/* Character Head */}
          <circle cx="36" cy="20" r="14" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />

          {/* Mascot Ears */}
          <path d="M24 12 L28 18 L22 18 Z" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />
          <path d="M48 12 L44 18 L50 18 Z" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />
          <path d="M25 14 L27 17 L24 17 Z" fill="#334155" />
          <path d="M47 14 L45 17 L48 17 Z" fill="#334155" />

          {/* Mascot Eyes depending on status */}
          {status === 'idle' ? (
            /* Sleeping / Closed eyes */
            <>
              <path d="M29 19 Q32 22 35 19" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" fill="none" />
              <path d="M37 19 Q40 22 43 19" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round" fill="none" />
            </>
          ) : status === 'running' ? (
            /* Focused Glowing Eyes */
            <>
              <ellipse cx="32" cy="19" rx="2.5" ry="3" fill="#38bdf8" />
              <ellipse cx="40" cy="19" rx="2.5" ry="3" fill="#38bdf8" />
              <circle cx="33" cy="18" r="0.8" fill="#ffffff" />
              <circle cx="41" cy="18" r="0.8" fill="#ffffff" />
            </>
          ) : status === 'completed' ? (
            /* Happy Happy ^ ^ Eyes */
            <>
              <path d="M30 20 L32 17 L34 20" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
              <path d="M38 20 L40 17 L42 20" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
            </>
          ) : (
            /* Failed / Sad X Eyes */
            <>
              <path d="M30 17 L34 21 M34 17 L30 21" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M38 17 L42 21 M42 17 L38 21" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round" />
            </>
          )}

          {/* Cute Nose / Snout */}
          <ellipse cx="36" cy="23" rx="2" ry="1.2" fill="#334155" />

          {/* Mascot Scarf / Bandana */}
          <path d="M26 27 C30 30 42 30 46 27 L44 32 C38 35 34 35 28 32 Z" fill={theme.scarf} />
          <circle cx="36" cy="30" r="2" fill="#ffffff" />

          {/* Hands Typing on Keyboard or Holding Coffee */}
          {status === 'running' ? (
            /* Typing Hands */
            <>
              <circle cx="28" cy="42" r="3" fill="#0f172a" stroke="#334155" strokeWidth="1" className="anim-typing" />
              <circle cx="44" cy="42" r="3" fill="#0f172a" stroke="#334155" strokeWidth="1" className="anim-typing" style={{ animationDelay: '0.15s' }} />
            </>
          ) : status === 'completed' ? (
            /* Hands up celebrating */
            <>
              <circle cx="22" cy="28" r="3" fill="#0f172a" stroke="#34d399" strokeWidth="1" />
              <circle cx="50" cy="28" r="3" fill="#0f172a" stroke="#34d399" strokeWidth="1" />
            </>
          ) : (
            /* Resting Hands */
            <>
              <circle cx="29" cy="44" r="3" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />
              <circle cx="43" cy="44" r="3" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />
            </>
          )}
        </svg>
      </div>
    </div>
  );
};
