// @trace: REQ-STICKMAN-001, REQ-STICKMAN-002, REQ-STICKMAN-003
import React, { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';
import './officeTheme.css';

export interface DeskPosition {
  deskIndex: number;
  agentName: string;
  xPercent: number; // 0 - 100% of container width
  yPercent: number; // 0 - 100% of container height
}

interface StickmanCourierProps {
  currentActiveAgent?: string;
  isRunning?: boolean;
  totalCompleted: number;
  customTargetIndex?: number | null;
}

export const StickmanCourier: React.FC<StickmanCourierProps> = ({
  currentActiveAgent,
  totalCompleted,
  customTargetIndex,
}) => {
  // 6 Desk coordinates placed neatly in the walkway aisle beside each desk
  const DESK_COORDINATES: DeskPosition[] = [
    { deskIndex: 0, agentName: 'SearchAgent', xPercent: 28, yPercent: 48 },
    { deskIndex: 1, agentName: 'ReadingAgent', xPercent: 61, yPercent: 48 },
    { deskIndex: 2, agentName: 'SummarizationAgent', xPercent: 94, yPercent: 48 },
    { deskIndex: 3, agentName: 'WritingAgent', xPercent: 28, yPercent: 95 },
    { deskIndex: 4, agentName: 'ReviewAgent', xPercent: 61, yPercent: 95 },
    { deskIndex: 5, agentName: 'CitationAgent', xPercent: 94, yPercent: 95 },
  ];

  // Starting idle position: Pantry Breakroom Area
  const PANTRY_POS = { xPercent: 50, yPercent: 6 };

  const [currentPos, setCurrentPos] = useState(PANTRY_POS);
  const [isWalking, setIsWalking] = useState(false);
  const [facingRight, setFacingRight] = useState(true);
  const [speechText, setSpeechText] = useState('Sẵn sàng điều phối tài liệu...');
  const [isHandingOver, setIsHandingOver] = useState(false);

  // Determine destination based on active agent or custom demo index
  useEffect(() => {
    let targetIndex = -1;

    if (customTargetIndex !== undefined && customTargetIndex !== null && customTargetIndex >= 0) {
      targetIndex = customTargetIndex;
    } else if (currentActiveAgent) {
      targetIndex = DESK_COORDINATES.findIndex((d) => d.agentName === currentActiveAgent);
    } else if (totalCompleted === 6) {
      targetIndex = 6; // Center
    }

    if (targetIndex >= 0 && targetIndex < 6) {
      const target = DESK_COORDINATES[targetIndex];
      // Face towards target
      if (target.xPercent > currentPos.xPercent) {
        setFacingRight(true);
      } else if (target.xPercent < currentPos.xPercent) {
        setFacingRight(false);
      }

      setIsWalking(true);
      setIsHandingOver(false);

      // Dynamic task message
      const taskMessages = [
        '🔍 Giao yêu cầu tìm kiếm bài báo tới Search Agent',
        '📖 Bàn giao PDF và bóc tách dữ liệu sang Reading Agent',
        '📊 Chuyển dữ liệu bóc tách sang Summarization Agent',
        '✍️ Mang ma trận so sánh sang Writing Agent soạn thảo',
        '⚖️ Chuyển bản thảo sang Review Agent thẩm định',
        '📑 Chuyển báo cáo sang Citation Agent đóng dấu chuẩn',
      ];
      setSpeechText(taskMessages[targetIndex] || 'Đang giao tài liệu...');

      // Move stickman
      setCurrentPos({ xPercent: target.xPercent, yPercent: target.yPercent });

      // After walking duration (1.2s), trigger handover animation
      const walkTimer = setTimeout(() => {
        setIsWalking(false);
        setIsHandingOver(true);
      }, 1200);

      return () => clearTimeout(walkTimer);
    } else if (targetIndex === 6) {
      // Completed all
      setCurrentPos({ xPercent: 50, yPercent: 6 });
      setSpeechText('🏆 Hoàn tất 100% chu trình nghiên cứu khoa học!');
      setIsWalking(true);
      setTimeout(() => {
        setIsWalking(false);
        setIsHandingOver(true);
      }, 1200);
    } else {
      // Idle at pantry
      setCurrentPos(PANTRY_POS);
      setSpeechText('☕ Đang ở quầy Pantry, chờ lệnh mới...');
      setIsWalking(false);
      setIsHandingOver(false);
    }
  }, [currentActiveAgent, customTargetIndex, totalCompleted]);

  return (
    <div
      className="absolute pointer-events-none z-30 transition-all duration-1000 ease-out"
      style={{
        left: `${currentPos.xPercent}%`,
        top: `${currentPos.yPercent}%`,
        transform: `translate(-50%, -100%) scaleX(${facingRight ? 1 : -1})`,
      }}
    >
      {/* 1. Speech Dialog Bubble (Rendered with safe positioning) */}
      <div
        className="absolute -top-10 left-1/2 -translate-x-1/2 z-40 whitespace-nowrap px-3 py-1 rounded-xl bg-slate-900 border border-amber-400/70 shadow-lg shadow-amber-500/20 flex items-center gap-1.5 text-[10px] text-amber-200 font-semibold"
        style={{ transform: `translateX(-50%) scaleX(${facingRight ? 1 : -1})` }}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
        <span className="truncate max-w-[220px]">{speechText}</span>
        {isHandingOver && <Sparkles className="w-3 h-3 text-amber-400 animate-spin" />}
      </div>

      {/* 2. 2D Stickman Character Model (Articulated SVG) */}
      <div className={`relative ${isWalking ? 'anim-stickman-bob' : ''}`}>
        <svg
          width="54"
          height="72"
          viewBox="0 0 54 72"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="drop-shadow-[0_4px_10px_rgba(0,0,0,0.6)]"
        >
          {/* Shadow on Floor */}
          <ellipse cx="27" cy="68" rx="14" ry="4" fill="rgba(0,0,0,0.4)" />

          {/* Stickman Head */}
          <circle cx="27" cy="14" r="8" fill="#f8fafc" stroke="#0f172a" strokeWidth="2.5" />

          {/* Cute VR Headset / Visor */}
          <rect x="23" y="11" width="10" height="4" rx="2" fill="#6366f1" />
          <circle cx="30" cy="13" r="1" fill="#38bdf8" />

          {/* Stickman Torso (Spine) */}
          <line x1="27" y1="22" x2="27" y2="44" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />

          {/* Left Leg */}
          <g className={isWalking ? 'anim-stickman-leg-1' : ''}>
            <line x1="27" y1="44" x2="20" y2="56" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
            <line x1="20" y1="56" x2="16" y2="67" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
            <line x1="16" y1="67" x2="22" y2="67" stroke="#38bdf8" strokeWidth="3.5" strokeLinecap="round" />
          </g>

          {/* Right Leg */}
          <g className={isWalking ? 'anim-stickman-leg-2' : ''}>
            <line x1="27" y1="44" x2="34" y2="56" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
            <line x1="34" y1="56" x2="38" y2="67" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
            <line x1="38" y1="67" x2="44" y2="67" stroke="#38bdf8" strokeWidth="3.5" strokeLinecap="round" />
          </g>

          {/* Left Arm (Holding Document Folder) */}
          <g className={isWalking ? 'anim-stickman-arm-1' : ''}>
            <line x1="27" y1="26" x2="18" y2="34" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
            <line x1="18" y1="34" x2="32" y2="34" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
          </g>

          {/* Right Arm (Forward handover posture) */}
          <g className={isWalking ? 'anim-stickman-arm-2' : ''}>
            <line x1="27" y1="26" x2="36" y2="32" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
            <line x1="36" y1="32" x2="42" y2="28" stroke="#f8fafc" strokeWidth="3" strokeLinecap="round" />
          </g>

          {/* Glowing Document Dossier / Folder Handed Over */}
          <g transform="translate(26, 22)" className="anim-handover-glow">
            {/* Folder Body */}
            <rect x="0" y="0" width="16" height="13" rx="2" fill="#fbbf24" stroke="#d97706" strokeWidth="1" />
            <path d="M0 3 L6 3 L8 5 L16 5 L16 13 L0 13 Z" fill="#f59e0b" />
            {/* White Document Paper sticking out */}
            <rect x="2" y="-3" width="10" height="6" rx="1" fill="#ffffff" />
            <line x1="4" y1="-1" x2="10" y2="-1" stroke="#64748b" strokeWidth="0.8" />
            <line x1="4" y1="1" x2="8" y2="1" stroke="#64748b" strokeWidth="0.8" />
          </g>
        </svg>
      </div>
    </div>
  );
};
