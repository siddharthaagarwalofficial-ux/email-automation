"use client";

import { useEffect, useState } from "react";
import {
  api,
  ClassificationBreakdown,
  StatusBreakdown,
  ReplyTimeline,
  MeetingIntent,
} from "@/lib/api";

const categoryColors: Record<string, string> = {
  positive: "bg-emerald-400",
  negative: "bg-red-400",
  more_info: "bg-blue-400",
  out_of_office: "bg-yellow-400",
  wrong_person: "bg-purple-400",
  unsubscribe: "bg-gray-400",
};

const categoryLabels: Record<string, string> = {
  positive: "Positive",
  negative: "Negative",
  more_info: "More Info",
  out_of_office: "Out of Office",
  wrong_person: "Wrong Person",
  unsubscribe: "Unsubscribe",
};

const statusColors: Record<string, string> = {
  sent: "bg-gray-400",
  awaiting_reply: "bg-amber-400",
  replied: "bg-blue-400",
  follow_up_1: "bg-orange-400",
  follow_up_2: "bg-orange-500",
  follow_up_3: "bg-red-400",
  closed: "bg-gray-500",
  paused: "bg-gray-300",
};

const statusLabels: Record<string, string> = {
  sent: "Sent",
  awaiting_reply: "Awaiting Reply",
  replied: "Replied",
  follow_up_1: "Follow-up 1",
  follow_up_2: "Follow-up 2",
  follow_up_3: "Follow-up 3",
  closed: "Closed",
  paused: "Paused",
};

function BarChart({ data, colorMap, labelMap }: {
  data: { key: string; count: number }[];
  colorMap: Record<string, string>;
  labelMap: Record<string, string>;
}) {
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="space-y-2">
      {data.map((d) => (
        <div key={d.key} className="flex items-center gap-3">
          <span className="text-xs text-gray-600 w-24 text-right truncate">
            {labelMap[d.key] || d.key}
          </span>
          <div className="flex-1 bg-gray-100 rounded-full h-6 overflow-hidden">
            <div
              className={`h-full rounded-full ${colorMap[d.key] || "bg-gray-400"} transition-all duration-500`}
              style={{ width: `${(d.count / max) * 100}%` }}
            />
          </div>
          <span className="text-sm font-semibold w-8">{d.count}</span>
        </div>
      ))}
    </div>
  );
}

export default function Analytics() {
  const [classifications, setClassifications] = useState<ClassificationBreakdown[]>([]);
  const [statuses, setStatuses] = useState<StatusBreakdown[]>([]);
  const [timeline, setTimeline] = useState<ReplyTimeline[]>([]);
  const [meetings, setMeetings] = useState<MeetingIntent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [c, s, t, m] = await Promise.all([
          api.getClassificationBreakdown(),
          api.getStatusBreakdown(),
          api.getReplyTimeline(),
          api.getMeetingIntents(),
        ]);
        setClassifications(c);
        setStatuses(s);
        setTimeline(t);
        setMeetings(m);
      } catch (err) {
        console.error("Failed to load analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading analytics...</div>;
  }

  const noData = classifications.length === 0 && statuses.length === 0;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {noData && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
          Run the AI Pipeline first to see classification and reply analytics.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Classification Distribution */}
        <div className="bg-white rounded-lg border p-5">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Reply Classifications
          </h3>
          {classifications.length > 0 ? (
            <BarChart
              data={classifications.map((c) => ({ key: c.category, count: c.count }))}
              colorMap={categoryColors}
              labelMap={categoryLabels}
            />
          ) : (
            <p className="text-sm text-gray-400">No classifications yet</p>
          )}
        </div>

        {/* Status Distribution */}
        <div className="bg-white rounded-lg border p-5">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Thread Status Distribution
          </h3>
          <BarChart
            data={statuses.map((s) => ({ key: s.status, count: s.count }))}
            colorMap={statusColors}
            labelMap={statusLabels}
          />
        </div>
      </div>

      {/* Reply Time Distribution */}
      <div className="bg-white rounded-lg border p-5">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Reply Time Distribution (hours)
        </h3>
        {timeline.length > 0 ? (
          <div className="space-y-2">
            {timeline.map((t) => {
              const maxHours = Math.max(...timeline.map((x) => x.reply_time_hours), 1);
              return (
                <div key={t.thread_id} className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 w-32 text-right truncate" title={t.recipient}>
                    {t.recipient}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-blue-400 transition-all duration-500"
                      style={{ width: `${(t.reply_time_hours / maxHours) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium w-12 text-right">{t.reply_time_hours}h</span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No reply data yet</p>
        )}
      </div>

      {/* Meeting Intents — Action Items */}
      <div className="bg-white rounded-lg border p-5">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Action Items: Meeting Requests
        </h3>
        {meetings.length > 0 ? (
          <div className="space-y-3">
            {meetings.map((m) => (
              <div key={m.thread_id} className="border rounded-lg p-3 bg-indigo-50 border-indigo-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{m.recipient}</p>
                    <p className="text-xs text-gray-500">{m.subject}</p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full bg-indigo-100 text-indigo-700">
                    Schedule Meeting
                  </span>
                </div>
                {m.reply_snippet && (
                  <p className="text-xs text-gray-600 mt-2 italic">&ldquo;{m.reply_snippet.slice(0, 150)}...&rdquo;</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No meeting requests detected yet</p>
        )}
      </div>
    </div>
  );
}
