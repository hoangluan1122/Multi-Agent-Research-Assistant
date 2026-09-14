// @trace: REQ-DINO-001, REQ-DINO-002, REQ-DINO-003
import React, { useEffect, useState } from 'react';
import { Sparkles, FileText } from 'lucide-react';
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
  const [speechText, setSpeechText] = useState('🦖 Dino sẵn sàng điều phối tài liệu...');
  const [isHandingOver, setIsHandingOver] = useState(false);
  const [dinoSkin, setDinoSkin] = useState<'doux' | 'mort' | 'tard' | 'vita'>('doux');

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

      // Cycle dino skin depending on step
      const skins: Array<'doux' | 'mort' | 'tard' | 'vita'> = ['doux', 'vita', 'tard', 'mort', 'doux', 'vita'];
      setDinoSkin(skins[targetIndex] || 'doux');

      // Dynamic task message
      const taskMessages = [
        '🔍 Dino chuyển hồ sơ đề tài tới Search Agent',
        '📖 Dino bàn giao bài báo PDF sang Reading Agent',
        '📊 Dino mang trích xuất sang Summarization Agent',
        '✍️ Dino chuyển ma trận đối sánh sang Writing Agent',
        '⚖️ Dino nộp bản thảo sang Review Agent thẩm định',
        '📑 Dino chuyển bài hoàn thiện sang Citation Agent chứng thực',
      ];
      setSpeechText(taskMessages[targetIndex] || '🦖 Dino đang vận chuyển tài liệu...');

      // Move courier
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
      setSpeechText('🏆 Dino hoàn thành 100% chu trình điều phối!');
      setIsWalking(true);
      setTimeout(() => {
        setIsWalking(false);
        setIsHandingOver(true);
      }, 1200);
    } else {
      // Idle at pantry
      setCurrentPos(PANTRY_POS);
      setSpeechText('☕ Dino đang nghỉ ngơi ở quầy Pantry...');
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
        transform: 'translate(-50%, -100%)',
      }}
    >
      {/* 1. Speech Dialog Bubble */}
      <div
        className="absolute -top-10 left-1/2 -translate-x-1/2 z-40 whitespace-nowrap px-3 py-1 rounded-xl bg-slate-900/95 border border-amber-400/80 shadow-lg shadow-amber-500/25 flex items-center gap-1.5 text-[11px] text-amber-200 font-semibold backdrop-blur-sm"
      >
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        <span className="truncate max-w-[240px]">{speechText}</span>
        {isHandingOver && <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-spin" />}
      </div>

      {/* 2. 2D Dino Courier Model from Pixel Art Assets */}
      <div className={`relative flex flex-col items-center ${isHandingOver ? 'anim-celebrate' : isWalking ? 'anim-stickman-bob' : ''}`}>
        
        {/* Glowing Dossier / Document Folder Carried by Dino */}
        <div
          className={`absolute -top-3 ${facingRight ? '-right-1' : '-left-1'} z-40 bg-gradient-to-tr from-amber-500 to-yellow-300 p-1 rounded-md shadow-md shadow-amber-500/50 border border-yellow-100 text-slate-950 flex items-center gap-0.5 ${
            isHandingOver ? 'anim-handover-glow scale-110' : 'animate-bounce'
          }`}
        >
          <FileText className="w-3 h-3 text-slate-900 stroke-[2.5]" />
          <span className="text-[8px] font-black tracking-tighter">DOCS</span>
        </div>

        {/* Dino Sprite (Pixel Art GIF with crisp rendering) */}
        <div
          className="relative transition-transform duration-300"
          style={{
            transform: `scaleX(${facingRight ? 1 : -1})`,
          }}
        >
          <img
            src={`/dino/gifs/DinoSprites_${dinoSkin}.gif`}
            alt="Dino Courier"
            className="w-14 h-14 object-contain drop-shadow-[0_6px_12px_rgba(0,0,0,0.6)]"
            style={{
              imageRendering: 'pixelated',
            }}
          />
        </div>

        {/* Dynamic Shadow on Floor */}
        <div className="w-10 h-2 bg-black/40 rounded-full blur-[2px] -mt-2" />
      </div>
    </div>
  );
};
