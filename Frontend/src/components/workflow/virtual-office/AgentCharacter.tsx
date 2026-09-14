// @trace: REQ-DINO-AGENT-001, REQ-DINO-AGENT-002
import React from 'react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import './officeTheme.css';

export type CharacterStatus = 'running' | 'completed' | 'failed' | 'idle';

interface AgentCharacterProps {
  agentName: string;
  status: CharacterStatus;
  currentTask?: string;
  isDelivering?: boolean;
}

export const AgentCharacter: React.FC<AgentCharacterProps> = ({
  agentName,
  status,
  currentTask,
  isDelivering = false,
}) => {
  // Config per agent: Dino skin, accessory overlay, role colors
  const getAgentDinoConfig = () => {
    switch (agentName) {
      case 'SearchAgent':
        return {
          skin: 'doux', // Blue dino
          title: 'Thám hiểm',
          hatColor: '#0284c7',
          hatBorder: '#38bdf8',
          accessory: '🔍',
          badgeText: 'SEARCH',
        };
      case 'ReadingAgent':
        return {
          skin: 'vita', // Green dino
          title: 'Học thuật',
          hatColor: '#059669',
          hatBorder: '#34d399',
          accessory: '📖',
          badgeText: 'READ',
        };
      case 'SummarizationAgent':
        return {
          skin: 'tard', // Yellow dino
          title: 'Dữ liệu',
          hatColor: '#d97706',
          hatBorder: '#fbbf24',
          accessory: '⚡',
          badgeText: 'SUMMARY',
        };
      case 'WritingAgent':
        return {
          skin: 'mort', // Red dino
          title: 'Soạn thảo',
          hatColor: '#6366f1',
          hatBorder: '#a5b4fc',
          accessory: '✍️',
          badgeText: 'WRITE',
        };
      case 'ReviewAgent':
        return {
          skin: 'doux', // Deep Navy / Crimson dino
          title: 'Thẩm định',
          hatColor: '#e11d48',
          hatBorder: '#fda4af',
          accessory: '⚖️',
          badgeText: 'REVIEW',
          filter: 'hue-rotate(140deg) saturate(1.4)',
        };
      case 'CitationAgent':
        return {
          skin: 'vita', // Royal Purple / Gold dino
          title: 'Chứng thực',
          hatColor: '#9333ea',
          hatBorder: '#d8b4fe',
          accessory: '🏛️',
          badgeText: 'CITE',
          filter: 'hue-rotate(200deg) brightness(1.1)',
        };
      default:
        return {
          skin: 'doux',
          title: 'AI Agent',
          hatColor: '#6366f1',
          hatBorder: '#818cf8',
          accessory: '🤖',
          badgeText: 'AGENT',
        };
    }
  };

  const config = getAgentDinoConfig();

  // If this dino is currently delivering to the next desk, hide it at the seat
  if (isDelivering) {
    return (
      <div className="relative flex flex-col items-center opacity-30 select-none">
        <div className="w-14 h-14 flex items-center justify-center border-2 border-dashed border-indigo-400/50 rounded-2xl">
          <span className="text-xs text-indigo-300 font-mono">Đang giao việc...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col items-center select-none">
      {/* 1. Status Bubble / Thinking Dialog Above Dino */}
      {status === 'running' && (
        <div className="absolute -top-11 z-30 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-900/90 border border-indigo-400/60 shadow-lg shadow-indigo-500/30 text-[10px] text-indigo-100 font-medium whitespace-nowrap animate-bounce">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
          <span className="truncate max-w-[120px]">{currentTask || 'Đang làm việc...'}</span>
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
          <span>Xong việc</span>
        </div>
      )}

      {status === 'failed' && (
        <div className="absolute -top-7 z-20 flex items-center gap-1 px-2 py-0.5 rounded-full bg-rose-950/80 border border-rose-500/50 text-[10px] text-rose-300 shadow-md">
          <AlertCircle className="w-3 h-3 text-rose-400" />
          <span>Lỗi</span>
        </div>
      )}

      {/* 2. 2D Dino Pixel Art Mascot Seated at Desk */}
      <div
        className={`relative transition-transform duration-300 flex flex-col items-center ${
          status === 'running' ? 'anim-typing scale-105' : status === 'completed' ? 'anim-celebrate' : ''
        }`}
      >
        {/* Agent Role Accessory Badge floating near head */}
        <div
          className="absolute -top-2 -right-2 z-30 px-1.5 py-0.5 rounded-md text-[10px] shadow-md border flex items-center gap-0.5 font-bold"
          style={{
            backgroundColor: `${config.hatColor}dd`,
            borderColor: config.hatBorder,
            color: '#ffffff',
          }}
        >
          <span>{config.accessory}</span>
        </div>

        {/* Dino Sprite Image */}
        <div
          className="relative"
          style={{
            filter: config.filter || 'none',
          }}
        >
          <img
            src={`/dino/gifs/DinoSprites_${config.skin}.gif`}
            alt={`${agentName} Dino`}
            className="w-16 h-16 object-contain drop-shadow-[0_8px_14px_rgba(0,0,0,0.7)]"
            style={{
              imageRendering: 'pixelated',
            }}
          />
        </div>

        {/* Chair Shadow Under Dino */}
        <div className="w-12 h-2.5 bg-black/50 rounded-full blur-[2px] -mt-2" />
      </div>
    </div>
  );
};

