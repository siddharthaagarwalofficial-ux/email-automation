"use client";

import { DashboardStats } from "@/types";

interface Props {
  stats: DashboardStats | null;
}

const cards = [
  { key: "total_threads", label: "Total Threads", color: "bg-slate-50 border-slate-200" },
  { key: "awaiting_reply", label: "Awaiting Reply", color: "bg-amber-50 border-amber-200" },
  { key: "replied", label: "Replied", color: "bg-blue-50 border-blue-200" },
  { key: "positive_replies", label: "Positive", color: "bg-emerald-50 border-emerald-200" },
  { key: "negative_replies", label: "Negative", color: "bg-red-50 border-red-200" },
  { key: "drafts_for_review", label: "Drafts to Review", color: "bg-purple-50 border-purple-200" },
] as const;

export default function StatsCards({ stats }: Props) {
  if (!stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map((c) => (
          <div key={c.key} className="h-24 rounded-lg border bg-gray-50 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((c) => (
        <div key={c.key} className={`rounded-lg border p-4 ${c.color}`}>
          <p className="text-sm text-gray-600">{c.label}</p>
          <p className="text-2xl font-bold mt-1">
            {stats[c.key as keyof DashboardStats] ?? 0}
          </p>
        </div>
      ))}
      <div className="col-span-2 md:col-span-3 lg:col-span-6 flex gap-6 text-sm text-gray-500 px-1">
        <span>Reply Rate: <strong>{stats.reply_rate}%</strong></span>
        {stats.avg_reply_time_hours !== null && (
          <span>Avg Reply Time: <strong>{stats.avg_reply_time_hours}h</strong></span>
        )}
        <span>Pending Follow-ups: <strong>{stats.pending_follow_ups}</strong></span>
      </div>
    </div>
  );
}
