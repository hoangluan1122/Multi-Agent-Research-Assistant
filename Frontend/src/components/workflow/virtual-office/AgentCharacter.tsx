// @trace: REQ-VO-002, REQ-VO-003
import React from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
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
  // Render distinct 2D model per Agent
  const renderUniqueCharacter = () => {
    switch (agentName) {
      // =========================================================================
      // MODEL 1: SEARCH AGENT (Nhân vật Thám Hiểm với Mũ Safari & Kính Lúp)
      // =========================================================================
      case 'SearchAgent':
        return (
          <svg width="76" height="76" viewBox="0 0 76 76" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-lg">
            {/* Swivel Chair */}
            <rect x="22" y="34" width="32" height="28" rx="8" fill="#1e293b" stroke="#0284c7" strokeWidth="1.5" />
            <circle cx="38" cy="64" r="3" fill="#0f172a" />
            <path d="M30 67 L46 67 M38 62 L38 67" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

            {/* Explorer Outfit (Safari Vest) */}
            <rect x="25" y="26" width="26" height="26" rx="8" fill="#0369a1" stroke="#38bdf8" strokeWidth="1.5" />
            <rect x="29" y="32" width="6" height="7" rx="1.5" fill="#0284c7" stroke="#bae6fd" strokeWidth="0.8" />
            <rect x="41" y="32" width="6" height="7" rx="1.5" fill="#0284c7" stroke="#bae6fd" strokeWidth="0.8" />

            {/* Head */}
            <circle cx="38" cy="22" r="13" fill="#f8fafc" stroke="#0f172a" strokeWidth="1.5" />

            {/* Safari Explorer Pith Hat */}
            <ellipse cx="38" cy="12" rx="16" ry="4" fill="#0284c7" stroke="#38bdf8" strokeWidth="1.5" />
            <path d="M26 12 C26 4 50 4 50 12 Z" fill="#0369a1" stroke="#38bdf8" strokeWidth="1.5" />
            <rect x="36" y="6" width="4" height="4" rx="1" fill="#fbbf24" />

            {/* Eyes */}
            {status === 'idle' ? (
              <path d="M32 23 Q35 25 38 23 M40 23 Q43 25 46 23" stroke="#64748b" strokeWidth="1.5" strokeLinecap="round" />
            ) : status === 'running' ? (
              <>
                <circle cx="34" cy="22" r="2.5" fill="#0284c7" />
                <circle cx="42" cy="22" r="2.5" fill="#0284c7" />
                <circle cx="35" cy="21" r="0.8" fill="#ffffff" />
                <circle cx="43" cy="21" r="0.8" fill="#ffffff" />
              </>
            ) : (
              <path d="M32 24 L35 21 L38 24 M40 24 L43 21 L46 24" stroke="#059669" strokeWidth="2" strokeLinecap="round" />
            )}

            {/* Scout Magnifying Glass in Hand */}
            <g transform="translate(48, 20)" className={status === 'running' ? 'anim-typing' : ''}>
              <circle cx="8" cy="8" r="7" fill="#38bdf8" fillOpacity="0.3" stroke="#38bdf8" strokeWidth="2" />
              <line x1="13" y1="13" x2="20" y2="20" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" />
              <circle cx="8" cy="8" r="3" fill="#ffffff" fillOpacity="0.6" />
            </g>
          </svg>
        );

      // =========================================================================
      // MODEL 2: READING AGENT (Nhân vật Giáo Sư Đeo Kính & Mũ Cử Nhân Tiến Sĩ)
      // =========================================================================
      case 'ReadingAgent':
        return (
          <svg width="76" height="76" viewBox="0 0 76 76" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-lg">
            {/* Swivel Chair */}
            <rect x="22" y="34" width="32" height="28" rx="8" fill="#1e293b" stroke="#059669" strokeWidth="1.5" />
            <circle cx="38" cy="64" r="3" fill="#0f172a" />
            <path d="M30 67 L46 67 M38 62 L38 67" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

            {/* Academic Scholar Robe */}
            <rect x="25" y="26" width="26" height="26" rx="8" fill="#064e3b" stroke="#34d399" strokeWidth="1.5" />
            <path d="M34 26 L38 34 L42 26" stroke="#fbbf24" strokeWidth="2" fill="none" />

            {/* Head */}
            <circle cx="38" cy="22" r="13" fill="#f8fafc" stroke="#0f172a" strokeWidth="1.5" />

            {/* Mortarboard Graduate Cap */}
            <path d="M38 4 L56 12 L38 20 L20 12 Z" fill="#0f172a" stroke="#34d399" strokeWidth="1.5" />
            <rect x="30" y="16" width="16" height="6" fill="#0f172a" stroke="#059669" strokeWidth="1" />
            <circle cx="38" cy="12" r="2" fill="#fbbf24" />
            <path d="M38 12 Q48 14 50 24" stroke="#fbbf24" strokeWidth="1.5" strokeLinecap="round" />
            <circle cx="50" cy="25" r="2" fill="#fbbf24" />

            {/* Scholar Big Round Glasses */}
            <circle cx="33" cy="22" r="4.5" stroke="#059669" strokeWidth="1.5" fill="none" />
            <circle cx="43" cy="22" r="4.5" stroke="#059669" strokeWidth="1.5" fill="none" />
            <line x1="37.5" y1="22" x2="38.5" y2="22" stroke="#059669" strokeWidth="1.5" />

            {/* Eyes behind glasses */}
            {status === 'idle' ? (
              <line x1="31" y1="22" x2="35" y2="22" stroke="#64748b" strokeWidth="1.5" />
            ) : (
              <>
                <circle cx="33" cy="22" r="2" fill="#059669" />
                <circle cx="43" cy="22" r="2" fill="#059669" />
              </>
            )}

            {/* Open Book / PDF Dossier at Side */}
            <g transform="translate(10, 30)" className={status === 'running' ? 'anim-typing' : ''}>
              <rect x="0" y="0" width="12" height="15" rx="2" fill="#34d399" stroke="#059669" strokeWidth="1" />
              <line x1="3" y1="4" x2="9" y2="4" stroke="#ffffff" strokeWidth="1" />
              <line x1="3" y1="7" x2="9" y2="7" stroke="#ffffff" strokeWidth="1" />
              <line x1="3" y1="10" x2="7" y2="10" stroke="#ffffff" strokeWidth="1" />
            </g>
          </svg>
        );

      // =========================================================================
      // MODEL 3: SUMMARIZATION AGENT (Chuyên Gia Dữ Liệu Đeo Tai Nghe & Hologram)
      // =========================================================================
      case 'SummarizationAgent':
        return (
          <svg width="76" height="76" viewBox="0 0 76 76" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-lg">
            {/* Swivel Chair */}
            <rect x="22" y="34" width="32" height="28" rx="8" fill="#1e293b" stroke="#d97706" strokeWidth="1.5" />
            <circle cx="38" cy="64" r="3" fill="#0f172a" />
            <path d="M30 67 L46 67 M38 62 L38 67" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

            {/* Tech Hoodie Outfit */}
            <rect x="25" y="26" width="26" height="26" rx="8" fill="#78350f" stroke="#fbbf24" strokeWidth="1.5" />
            <circle cx="38" cy="36" r="3" fill="#fbbf24" />

            {/* Head */}
            <circle cx="38" cy="22" r="13" fill="#f8fafc" stroke="#0f172a" strokeWidth="1.5" />

            {/* DJ / Data Tech Headset */}
            <path d="M22 22 C22 10 54 10 54 22" stroke="#f59e0b" strokeWidth="3" fill="none" />
            <rect x="20" y="18" width="5" height="9" rx="2" fill="#d97706" />
            <rect x="51" y="18" width="5" height="9" rx="2" fill="#d97706" />
            <path d="M25 24 Q32 29 35 27" stroke="#f59e0b" strokeWidth="1.5" fill="none" />
            <circle cx="36" cy="27" r="1.5" fill="#ef4444" />

            {/* Futuristic Matrix Hologram Visor */}
            <rect x="29" y="19" width="18" height="6" rx="2" fill="#fbbf24" fillOpacity="0.85" />
            <line x1="31" y1="22" x2="45" y2="22" stroke="#78350f" strokeWidth="1" strokeDasharray="2 1" />

            {/* Floating Hologram Chart Bars */}
            <g transform="translate(52, 10)">
              <rect x="0" y="8" width="3" height="8" rx="1" fill="#fbbf24" className="anim-typing" />
              <rect x="5" y="4" width="3" height="12" rx="1" fill="#f59e0b" className="anim-typing" style={{ animationDelay: '0.15s' }} />
              <rect x="10" y="0" width="3" height="16" rx="1" fill="#d97706" className="anim-typing" style={{ animationDelay: '0.3s' }} />
            </g>
          </svg>
        );

      // =========================================================================
      // MODEL 4: WRITING AGENT (Nhà Văn Đội Mũ Beret & Cầm Bút Lông Vũ)
      // =========================================================================
      case 'WritingAgent':
        return (
          <svg width="76" height="76" viewBox="0 0 76 76" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-lg">
            {/* Swivel Chair */}
            <rect x="22" y="34" width="32" height="28" rx="8" fill="#1e293b" stroke="#6366f1" strokeWidth="1.5" />
            <circle cx="38" cy="64" r="3" fill="#0f172a" />
            <path d="M30 67 L46 67 M38 62 L38 67" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

            {/* Novelist Outfit (Turtleneck & Scarf) */}
            <rect x="25" y="26" width="26" height="26" rx="8" fill="#312e81" stroke="#818cf8" strokeWidth="1.5" />
            <path d="M30 26 L46 26 L42 34 L34 34 Z" fill="#6366f1" />

            {/* Head */}
            <circle cx="38" cy="22" r="13" fill="#f8fafc" stroke="#0f172a" strokeWidth="1.5" />

            {/* Artist French Beret Hat */}
            <ellipse cx="40" cy="11" rx="15" ry="6" fill="#4338ca" stroke="#818cf8" strokeWidth="1.5" />
            <path d="M38 5 L38 3" stroke="#a5b4fc" strokeWidth="2" strokeLinecap="round" />

            {/* Focused Creative Eyes */}
            {status === 'idle' ? (
              <path d="M32 23 Q35 25 38 23 M40 23 Q43 25 46 23" stroke="#64748b" strokeWidth="1.5" strokeLinecap="round" />
            ) : (
              <>
                <circle cx="34" cy="22" r="2.5" fill="#6366f1" />
                <circle cx="42" cy="22" r="2.5" fill="#6366f1" />
                <circle cx="35" cy="21" r="0.8" fill="#ffffff" />
                <circle cx="43" cy="21" r="0.8" fill="#ffffff" />
              </>
            )}

            {/* Magic Feather Quill Pen in Hand */}
            <g transform="translate(50, 16)" className={status === 'running' ? 'anim-typing' : ''}>
              <path d="M4 18 L16 2 C14 8 18 10 14 16 L4 18 Z" fill="#818cf8" stroke="#c7d2fe" strokeWidth="1" />
              <line x1="4" y1="18" x2="0" y2="24" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" />
              <circle cx="0" cy="24" r="1.5" fill="#6366f1" />
            </g>
          </svg>
        );

      // =========================================================================
      // MODEL 5: REVIEW AGENT (Quan Tòa / Trọng Tài Phản Biện Cầm Búa Thẩm Định)
      // =========================================================================
      case 'ReviewAgent':
        return (
          <svg width="76" height="76" viewBox="0 0 76 76" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-lg">
            {/* Swivel Chair */}
            <rect x="22" y="34" width="32" height="28" rx="8" fill="#1e293b" stroke="#e11d48" strokeWidth="1.5" />
            <circle cx="38" cy="64" r="3" fill="#0f172a" />
            <path d="M30 67 L46 67 M38 62 L38 67" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

            {/* Suit & Red Power Tie */}
            <rect x="25" y="26" width="26" height="26" rx="8" fill="#111827" stroke="#f43f5e" strokeWidth="1.5" />
            <polygon points="34,26 42,26 38,32" fill="#ffffff" />
            <polygon points="37,30 39,30 40,39 38,42 36,39" fill="#e11d48" />

            {/* Head */}
            <circle cx="38" cy="22" r="13" fill="#f8fafc" stroke="#0f172a" strokeWidth="1.5" />

            {/* Inspector Badge / Judge Wig Crest */}
            <path d="M38 4 L44 9 L42 16 L34 16 L32 9 Z" fill="#fbbf24" stroke="#d97706" strokeWidth="1" />
            <circle cx="38" cy="10" r="1.5" fill="#e11d48" />

            {/* Sharp Inspector Glasses */}
            <rect x="29" y="19" width="8" height="5" rx="1.5" stroke="#e11d48" strokeWidth="1.5" fill="none" />
            <rect x="39" y="19" width="8" height="5" rx="1.5" stroke="#e11d48" strokeWidth="1.5" fill="none" />
            <line x1="37" y1="21" x2="39" y2="21" stroke="#e11d48" strokeWidth="1.5" />

            {/* Eyes */}
            {status === 'idle' ? (
              <line x1="31" y1="21" x2="35" y2="21" stroke="#64748b" strokeWidth="1.5" />
            ) : (
              <>
                <circle cx="33" cy="21" r="2" fill="#e11d48" />
                <circle cx="43" cy="21" r="2" fill="#e11d48" />
              </>
            )}

            {/* Judge Gavel in Hand */}
            <g transform="translate(48, 22)" className={status === 'running' ? 'anim-typing' : ''}>
              <rect x="8" y="2" width="10" height="6" rx="1.5" fill="#78350f" stroke="#fbbf24" strokeWidth="1" />
              <line x1="13" y1="8" x2="13" y2="20" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" />
            </g>
          </svg>
        );

      // =========================================================================
      // MODEL 6: CITATION AGENT (Thủ Thư Hoàng Gia với Con Dấu Chuẩn Hóa IEEE/APA)
      // =========================================================================
      case 'CitationAgent':
        return (
          <svg width="76" height="76" viewBox="0 0 76 76" fill="none" xmlns="http://www.w3.org/2000/svg" className="drop-shadow-lg">
            {/* Swivel Chair */}
            <rect x="22" y="34" width="32" height="28" rx="8" fill="#1e293b" stroke="#9333ea" strokeWidth="1.5" />
            <circle cx="38" cy="64" r="3" fill="#0f172a" />
            <path d="M30 67 L46 67 M38 62 L38 67" stroke="#334155" strokeWidth="2" strokeLinecap="round" />

            {/* Royal Librarian Robe & Gold Trim */}
            <rect x="25" y="26" width="26" height="26" rx="8" fill="#3b0764" stroke="#c084fc" strokeWidth="1.5" />
            <line x1="38" y1="26" x2="38" y2="52" stroke="#fbbf24" strokeWidth="2" />

            {/* Head */}
            <circle cx="38" cy="22" r="13" fill="#f8fafc" stroke="#0f172a" strokeWidth="1.5" />

            {/* Librarian Reading Monocle with Gold Chain */}
            <circle cx="34" cy="22" r="5" stroke="#fbbf24" strokeWidth="1.5" fill="none" />
            <path d="M34 27 Q30 34 26 38" stroke="#fbbf24" strokeWidth="1" strokeDasharray="1 1" fill="none" />
            <circle cx="43" cy="22" r="2.5" fill="#a855f7" />
            <circle cx="34" cy="22" r="2.5" fill="#a855f7" />

            {/* Official Certification Stamp / Seal in Hand */}
            <g transform="translate(48, 18)" className={status === 'running' ? 'anim-typing' : ''}>
              <path d="M12 4 C8 4 6 8 6 12 L18 12 C18 8 16 4 12 4 Z" fill="#9333ea" stroke="#c084fc" strokeWidth="1" />
              <rect x="4" y="12" width="16" height="4" rx="1" fill="#fbbf24" stroke="#d97706" strokeWidth="1" />
              <circle cx="12" cy="18" r="4" fill="#ef4444" />
              <text x="10" y="20" fontSize="5" fill="#ffffff" fontWeight="bold">✓</text>
            </g>
          </svg>
        );

      default:
        return null;
    }
  };

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

      {/* 2. Render Distinct 2D Character Mascot */}
      <div className={`relative transition-transform duration-300 ${status === 'running' ? 'anim-head-bob' : ''} ${status === 'completed' ? 'anim-celebrate' : ''}`}>
        {renderUniqueCharacter()}
      </div>
    </div>
  );
};
