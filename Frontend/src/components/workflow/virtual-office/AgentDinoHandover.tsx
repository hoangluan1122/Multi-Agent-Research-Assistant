// @trace: REQ-DINO-HANDOVER-001, REQ-DINO-HANDOVER-002, REQ-DINO-HANDOVER-003
import React, { useEffect, useState } from 'react';
import { Sparkles, FileText } from 'lucide-react';
import './officeTheme.css';

export interface HandoverInfo {
  fromIndex: number;
  toIndex: number;
  senderAgent: string;
  receiverAgent: string;
  senderSkin: 'doux' | 'vita' | 'tard' | 'mort';
  senderAccessory: string;
  senderFilter?: string;
  message: string;
}

interface AgentDinoHandoverProps {
  handover: HandoverInfo | null;
  onHandoverComplete?: () => void;
}

export const AgentDinoHandover: React.FC<AgentDinoHandoverProps> = ({
  handover,
  onHandoverComplete,
}) => {
  // Desk center coordinates in the 3x2 grid (% of container)
  const DESK_POSITIONS = [
    { x: 17, y: 38 }, // Desk 0: Search
    { x: 50, y: 38 }, // Desk 1: Reading
    { x: 83, y: 38 }, // Desk 2: Summarization
    { x: 17, y: 86 }, // Desk 3: Writing
    { x: 50, y: 86 }, // Desk 4: Review
    { x: 83, y: 86 }, // Desk 5: Citation
  ];

  const [currentPos, setCurrentPos] = useState({ x: 17, y: 38 });
  const [isWalking, setIsWalking] = useState(false);
  const [facingRight, setFacingRight] = useState(true);
  const [isDelivering, setIsDelivering] = useState(false);

  useEffect(() => {
    if (!handover) {
      setIsWalking(false);
      setIsDelivering(false);
      return;
    }

    const start = DESK_POSITIONS[handover.fromIndex] || DESK_POSITIONS[0];
    const end = DESK_POSITIONS[handover.toIndex] || DESK_POSITIONS[1];

    // Set initial position at the sender desk
    setCurrentPos(start);
    setIsWalking(false);
    setIsDelivering(false);
    setFacingRight(end.x >= start.x);

    // Start running after a tiny pause
    const startTimer = setTimeout(() => {
      setIsWalking(true);
      setCurrentPos(end);
    }, 50);

    // Arrival at target desk
    const arriveTimer = setTimeout(() => {
      setIsWalking(false);
      setIsDelivering(true);
    }, 1250);

    // Complete handover
    const finishTimer = setTimeout(() => {
      setIsDelivering(false);
      if (onHandoverComplete) {
        onHandoverComplete();
      }
    }, 2200);

    return () => {
      clearTimeout(startTimer);
      clearTimeout(arriveTimer);
      clearTimeout(finishTimer);
    };
  }, [handover]);

  if (!handover) return null;

  return (
    <div
      className="absolute pointer-events-none z-40 transition-all duration-1000 ease-in-out"
      style={{
        left: `${currentPos.x}%`,
        top: `${currentPos.y}%`,
        transform: 'translate(-50%, -100%)',
      }}
    >
      {/* 1. Speech Dialog Bubble above Runner */}
      <div className="absolute -top-12 left-1/2 -translate-x-1/2 z-50 whitespace-nowrap px-3 py-1.5 rounded-xl bg-slate-900/95 border border-amber-400/80 shadow-xl shadow-amber-500/25 flex items-center gap-1.5 text-xs text-amber-200 font-bold backdrop-blur-md">
        <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
        <span>{handover.message}</span>
        {isDelivering && <Sparkles className="w-4 h-4 text-yellow-300 animate-spin" />}
      </div>

      {/* 2. Dino on the Move Carrying Dossier */}
      <div
        className={`relative flex flex-col items-center ${
          isDelivering ? 'anim-celebrate' : isWalking ? 'anim-stickman-bob' : ''
        }`}
      >
        {/* Floating Glowing Folder / Dossier */}
        <div
          className={`absolute -top-4 ${facingRight ? '-right-2' : '-left-2'} z-50 bg-gradient-to-tr from-amber-500 to-yellow-300 px-1.5 py-0.5 rounded-md shadow-lg shadow-amber-500/60 border border-yellow-100 text-slate-950 flex items-center gap-1 ${
            isDelivering ? 'anim-handover-glow scale-125' : 'animate-bounce'
          }`}
        >
          <FileText className="w-3.5 h-3.5 text-slate-900 stroke-[2.5]" />
          <span className="text-[9px] font-black tracking-tighter">BÀN GIAO</span>
        </div>

        {/* Dino Sprite Image with accessory */}
        <div
          className="relative transition-transform duration-300"
          style={{
            transform: `scaleX(${facingRight ? 1 : -1})`,
            filter: handover.senderFilter || 'none',
          }}
        >
          {/* Accessory badge on running dino */}
          <div className="absolute -top-2 -right-1 z-40 text-xs drop-shadow-md">
            {handover.senderAccessory}
          </div>

          <img
            src={`/dino/gifs/DinoSprites_${handover.senderSkin}.gif`}
            alt="Handover Dino"
            className="w-16 h-16 object-contain drop-shadow-[0_10px_20px_rgba(0,0,0,0.8)]"
            style={{
              imageRendering: 'pixelated',
            }}
          />
        </div>

        {/* Dynamic Running Shadow */}
        <div className="w-12 h-2.5 bg-black/60 rounded-full blur-[2px] -mt-2" />
      </div>
    </div>
  );
};
