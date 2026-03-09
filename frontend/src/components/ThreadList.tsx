"use client";

import { ThreadSummary, ThreadStatus, ReplyCategory } from "@/types";

interface Props {
  threads: ThreadSummary[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  statusFilter: string;
  onStatusFilter: (s: string) => void;
}

const statusColors: Record<ThreadStatus, string> = {
  sent: "bg-gray-100 text-gray-700",
  awaiting_reply: "bg-amber-100 text-amber-700",
  replied: "bg-blue-100 text-blue-700",
  follow_up_1: "bg-orange-100 text-orange-700",
  follow_up_2: "bg-orange-200 text-orange-800",
  follow_up_3: "bg-red-100 text-red-700",
  closed: "bg-gray-200 text-gray-600",
  paused: "bg-gray-100 text-gray-500",
};

const categoryColors: Record<ReplyCategory, string> = {
  positive: "bg-emerald-100 text-emerald-700",
  negative: "bg-red-100 text-red-700",
  more_info: "bg-blue-100 text-blue-700",
  out_of_office: "bg-yellow-100 text-yellow-700",
  wrong_person: "bg-purple-100 text-purple-700",
  unsubscribe: "bg-gray-100 text-gray-700",
};

const statusLabels: Record<ThreadStatus, string> = {
  sent: "Sent",
  awaiting_reply: "Awaiting Reply",
  replied: "Replied",
  follow_up_1: "Follow-up 1",
  follow_up_2: "Follow-up 2",
  follow_up_3: "Follow-up 3",
  closed: "Closed",
  paused: "Paused",
};

const filterOptions = [
  { value: "", label: "All" },
  { value: "awaiting_reply", label: "Awaiting Reply" },
  { value: "replied", label: "Replied" },
  { value: "follow_up_1", label: "Follow-up" },
  { value: "closed", label: "Closed" },
];

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function ThreadList({ threads, selectedId, onSelect, statusFilter, onStatusFilter }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-2 p-3 border-b overflow-x-auto">
        {filterOptions.map((f) => (
          <button
            key={f.value}
            onClick={() => onStatusFilter(f.value)}
            className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
              statusFilter === f.value
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {threads.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No threads found</div>
        ) : (
          threads.map((t) => (
            <button
              key={t.id}
              onClick={() => onSelect(t.id)}
              className={`w-full text-left p-4 border-b hover:bg-gray-50 transition-colors ${
                selectedId === t.id ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-sm truncate">
                    {t.recipient_name || t.recipient_email}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{t.subject}</p>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap">
                  {timeAgo(t.last_activity)}
                </span>
              </div>

              <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[t.status]}`}>
                  {statusLabels[t.status]}
                </span>
                {t.category && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${categoryColors[t.category]}`}>
                    {t.category.replace("_", " ")}
                  </span>
                )}
                {t.has_meeting_intent && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                    Meeting
                  </span>
                )}
                {t.pending_follow_ups > 0 && (
                  <span className="text-xs text-orange-600">
                    {t.pending_follow_ups} pending
                  </span>
                )}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
