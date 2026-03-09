const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

export interface ClassificationBreakdown {
  category: string;
  count: number;
}

export interface StatusBreakdown {
  status: string;
  count: number;
}

export interface ReplyTimeline {
  thread_id: number;
  recipient: string;
  subject: string;
  reply_time_hours: number;
  sent_at: string;
}

export interface MeetingIntent {
  thread_id: number;
  recipient: string;
  recipient_email: string;
  subject: string;
  reply_snippet: string;
  classified_at: string | null;
}

export interface RoutingAssignment {
  thread_id: number;
  recipient: string;
  recipient_email: string;
  subject: string;
  category: string;
  assigned_to: string;
  team: string;
  reply_snippet: string;
  has_meeting_intent: boolean;
}

export interface RoutingRule {
  category: string;
  assignee: string;
  label: string;
}

export const api = {
  getStats: () => fetchAPI<import("@/types").DashboardStats>("/api/dashboard/stats"),

  getThreads: (params?: { status?: string; category?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.category) searchParams.set("category", params.category);
    const qs = searchParams.toString();
    return fetchAPI<import("@/types").ThreadSummary[]>(`/api/threads/${qs ? `?${qs}` : ""}`);
  },

  getThread: (id: number) => fetchAPI<import("@/types").Thread>(`/api/threads/${id}`),

  followUpAction: (threadId: number, followUpId: number, action: {
    action: string;
    edited_subject?: string;
    edited_body?: string;
  }) =>
    fetchAPI<import("@/types").FollowUp>(`/api/threads/${threadId}/follow-ups/${followUpId}/action`, {
      method: "POST",
      body: JSON.stringify(action),
    }),

  sendFollowUp: (threadId: number, followUpId: number) =>
    fetchAPI<import("@/types").FollowUp>(`/api/threads/${threadId}/follow-ups/${followUpId}/send`, {
      method: "POST",
    }),

  syncEmails: () => fetchAPI<{ created: number; updated: number }>("/api/sync", { method: "POST" }),

  runPipeline: () =>
    fetchAPI<{
      classification: { classified: number };
      paused: { cancelled: number };
      sequencing: { scheduled: number };
      drafting: { drafted: number };
      auto_replies: { auto_replies_drafted: number };
    }>("/api/pipeline/run", { method: "POST" }),

  // Analytics
  getClassificationBreakdown: () => fetchAPI<ClassificationBreakdown[]>("/api/analytics/classification-breakdown"),
  getStatusBreakdown: () => fetchAPI<StatusBreakdown[]>("/api/analytics/status-breakdown"),
  getReplyTimeline: () => fetchAPI<ReplyTimeline[]>("/api/analytics/reply-timeline"),
  getMeetingIntents: () => fetchAPI<MeetingIntent[]>("/api/analytics/meeting-intents"),

  // Routing
  getRoutingRules: () => fetchAPI<RoutingRule[]>("/api/routing/rules"),
  getRoutingAssignments: () => fetchAPI<RoutingAssignment[]>("/api/routing/assignments"),
};
