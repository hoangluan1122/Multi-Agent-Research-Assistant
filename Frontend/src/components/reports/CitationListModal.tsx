import React from 'react';
import { Modal } from '../common/Modal';
import type { Citation } from '../../types';
import { Copy, Check } from 'lucide-react';
import { Badge } from '../common/Badge';
import { useI18n } from '../../i18n/context';

interface CitationListModalProps {
  citations: Citation[];
  isOpen: boolean;
  onClose: () => void;
}

export const CitationListModal: React.FC<CitationListModalProps> = ({
  citations,
  isOpen,
  onClose,
}) => {
  const { t } = useI18n();
  const [copiedId, setCopiedId] = React.useState<string | null>(null);

  const copyCitation = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={t.citationsModalTitle}
      subtitle={`Tổng cộng ${citations.length} ${t.citationsModalSubtitle}`}
      maxWidth="4xl"
    >
      <div className="space-y-3">
        {citations.length === 0 ? (
          <p className="text-xs text-gray-500 py-6 text-center">
            {t.noCitationsFound}
          </p>
        ) : (
          citations.map((c) => (
            <div
              key={c.id}
              className="p-4 rounded-xl bg-gray-800/40 border border-gray-700/60 space-y-2 text-xs"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[11px] font-bold">
                    {c.citation_key || `[${c.style}]`}
                  </span>
                  <Badge variant={c.is_verified ? 'success' : 'warning'}>
                    {c.is_verified ? t.verifiedBadge : t.unverifiedBadge}
                  </Badge>
                </div>

                <button
                  onClick={() => copyCitation(c.citation_text, c.id)}
                  className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-indigo-300 transition-colors"
                >
                  {copiedId === c.id ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                  <span>{copiedId === c.id ? t.copiedBtn : t.copyBtn}</span>
                </button>
              </div>

              {/* Formatted Citation */}
              <p className="text-gray-200 font-medium leading-relaxed pl-2 border-l-2 border-indigo-500/50">
                {c.citation_text}
              </p>

              {/* Claim context */}
              {c.claim_text && (
                <div className="pt-2 border-t border-gray-800/80 text-[11px] text-gray-400">
                  <span className="text-gray-500 font-semibold">{t.claimTextLabel}</span>{' '}
                  <span className="italic">"{c.claim_text}"</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </Modal>
  );
};
