"use client";

import { useEffect, useState } from "react";
import { api, RoutingAssignment, RoutingRule } from "@/lib/api";

const teamColors: Record<string, string> = {
  "Partnerships Team": "bg-emerald-100 text-emerald-700 border-emerald-200",
  "Product Team": "bg-blue-100 text-blue-700 border-blue-200",
  "Outreach Team": "bg-amber-100 text-amber-700 border-amber-200",
  "Compliance Team": "bg-red-100 text-red-700 border-red-200",
};

const categoryLabels: Record<string, string> = {
  positive: "Positive",
  negative: "Negative",
  more_info: "More Info",
  out_of_office: "Out of Office",
  wrong_person: "Wrong Person",
  unsubscribe: "Unsubscribe",
};

export default function Routing() {
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [assignments, setAssignments] = useState<RoutingAssignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [r, a] = await Promise.all([
          api.getRoutingRules(),
          api.getRoutingAssignments(),
        ]);
        setRules(r);
        setAssignments(a);
      } catch (err) {
        console.error("Failed to load routing:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-400">Loading routing data...</div>;
  }

  const grouped = assignments.reduce<Record<string, RoutingAssignment[]>>((acc, a) => {
    if (!acc[a.team]) acc[a.team] = [];
    acc[a.team].push(a);
    return acc;
  }, {});

  const noData = assignments.length === 0;

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {noData && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
          Run the AI Pipeline first to classify replies and see routing assignments.
        </div>
      )}

      {/* Routing Rules */}
      <div className="bg-white rounded-lg border p-5">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Routing Rules
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {rules.map((r) => (
            <div key={r.category} className="border rounded-lg p-3 bg-gray-50">
              <p className="text-xs text-gray-500">{categoryLabels[r.category] || r.category}</p>
              <p className="text-sm font-medium mt-0.5">{r.label}</p>
              <p className="text-xs text-gray-400">{r.assignee}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Assignments by Team */}
      {Object.entries(grouped).map(([team, items]) => (
        <div key={team} className="bg-white rounded-lg border p-5">
          <div className="flex items-center gap-2 mb-4">
            <span className={`text-xs px-2 py-1 rounded-full border ${teamColors[team] || "bg-gray-100 text-gray-700"}`}>
              {team}
            </span>
            <span className="text-xs text-gray-400">{items.length} thread{items.length !== 1 ? "s" : ""}</span>
          </div>

          <div className="space-y-2">
            {items.map((a) => (
              <div key={a.thread_id} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium truncate">{a.recipient}</p>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-gray-200 text-gray-600">
                      {categoryLabels[a.category] || a.category}
                    </span>
                    {a.has_meeting_intent && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">
                        Meeting
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 truncate">{a.subject}</p>
                  {a.reply_snippet && (
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">{a.reply_snippet}</p>
                  )}
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap">{a.assigned_to}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
