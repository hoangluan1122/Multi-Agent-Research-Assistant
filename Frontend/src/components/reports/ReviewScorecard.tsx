/**
 * Component Thẻ Điểm Đánh Giá Phản Biện (Peer Review Scorecard - UC010):
 * - Trình bày điểm số tổng kết thang 0-10 (hoặc 0-100) và trạng thái PASS/FAIL.
 * - Hiển thị tỷ lệ bao phủ trích dẫn trong văn bản (% Citation Coverage).
 * - Cảnh báo các nguy cơ ảo giác (Hallucination Risks) nếu có.
 * - Hiển thị phản hồi chi tiết từ ReviewAgent để phục vụ chỉnh sửa.
 */

import React from 'react';
import type { Review } from '../../types';
import {
  ShieldAlert,
  Award,
  BookMarked,
  MessageSquare,
} from 'lucide-react';
import { Badge } from '../common/Badge';

interface ReviewScorecardProps {
  review?: Review;
}

export const ReviewScorecard: React.FC<ReviewScorecardProps> = ({ review }) => {
  if (!review) return null;

  const getScoreVariant = (score: number) => {
    if (score >= 8.5) return 'success';
    if (score >= 7.0) return 'info';
    if (score >= 5.0) return 'warning';
    return 'danger';
  };

  return (
    <div className="p-5 rounded-2xl bg-gray-900/80 border border-gray-800 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-800 pb-3">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-indigo-400" />
          <h4 className="text-sm font-bold text-white uppercase tracking-wider">
            Đánh Giá Chất Lượng (Review Agent)
          </h4>
        </div>

        {/* Overall Score Badge */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">Điểm tổng kết:</span>
          <Badge variant={getScoreVariant(review.score)} size="md">
            <span className="font-bold text-sm">{review.score.toFixed(1)}</span> / 10
          </Badge>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {/* Citation Coverage */}
        <div className="p-3 rounded-xl bg-gray-800/40 border border-gray-700/50 space-y-1">
          <div className="flex items-center justify-between text-gray-400">
            <span className="flex items-center gap-1.5 font-medium">
              <BookMarked className="w-3.5 h-3.5 text-indigo-400" /> Độ phủ trích dẫn
            </span>
            <span className="font-bold text-indigo-300">
              {(review.citation_coverage * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full"
              style={{ width: `${review.citation_coverage * 100}%` }}
            />
          </div>
        </div>

        {/* Status */}
        <div className="p-3 rounded-xl bg-gray-800/40 border border-gray-700/50 flex items-center justify-between">
          <span className="text-gray-400 font-medium">Trạng thái phản biện:</span>
          <Badge variant={review.status === 'passed' ? 'success' : 'warning'}>
            {review.status.toUpperCase()}
          </Badge>
        </div>
      </div>

      {/* Hallucination Risks */}
      {review.hallucination_risks && review.hallucination_risks.length > 0 && (
        <div className="p-3.5 rounded-xl bg-rose-950/30 border border-rose-500/30 space-y-2">
          <h5 className="text-xs font-bold text-rose-300 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-400" /> Cảnh báo Rủi ro Hallucination ({review.hallucination_risks.length})
          </h5>
          <div className="space-y-1.5">
            {review.hallucination_risks.map((risk, idx) => (
              <div key={idx} className="text-xs text-rose-200/90 pl-3 border-l-2 border-rose-500/50 py-0.5">
                {risk.claim && <p className="font-semibold text-rose-100">"{risk.claim}"</p>}
                <p className="text-[11px] text-rose-300/80">{risk.reason || risk.risk}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviewer Feedback Comments */}
      {review.feedback && (
        <div className="p-3.5 rounded-xl bg-gray-800/50 border border-gray-700/60 space-y-1.5 text-xs">
          <h5 className="font-semibold text-indigo-300 flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5 text-indigo-400" /> Nhận xét chi tiết của phản biện:
          </h5>
          <p className="text-gray-300 leading-relaxed italic">{review.feedback}</p>
        </div>
      )}
    </div>
  );
};
