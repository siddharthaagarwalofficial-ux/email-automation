export type ThreadStatus =
  | "sent"
  | "awaiting_reply"
  | "replied"
  | "follow_up_1"
  | "follow_up_2"
  | "follow_up_3"
  | "closed"
  | "paused";

export type ReplyCategory =
  | "positive"
  | "negative"
  | "more_info"
  | "out_of_office"
  | "wrong_person"
  | "unsubscribe";

export type FollowUpStatus =
  | "scheduled"
  | "draft_ready"
  | "approved"
  | "sent"
  | "cancelled";

export interface ThreadSummary {
  id: number;
  recipient_email: string;
  recipient_name: string | null;
  subject: string;
  status: ThreadStatus;
  category: ReplyCategory | null;
  has_meeting_intent: boolean;
  pending_follow_ups: number;
  last_activity: string;
  created_at: string;
}

export interface Email {
  id: number;
  thread_id: number;
  direction: "outbound" | "inbound";
  email_type: string;
  sender: string;
  recipient: string;
  subject: string;
  body: string;
  sent_at: string;
}

export interface Classification {
  id: number;
  thread_id: number;
  category: ReplyCategory;
  confidence: number;
  reasoning: string | null;
  has_meeting_intent: boolean;
  classified_at: string;
}

export interface FollowUp {
  id: number;
  thread_id: number;
  sequence_number: number;
  scheduled_for: string;
  draft_subject: string | null;
  draft_body: string | null;
  status: FollowUpStatus;
  created_at: string;
  sent_at: string | null;
}

export interface Thread {
  id: number;
  gmail_thread_id: string | null;
  recipient_email: string;
  recipient_name: string | null;
  subject: string;
  status: ThreadStatus;
  created_at: string;
  updated_at: string;
  emails: Email[];
  classification: Classification | null;
  follow_ups: FollowUp[];
}

export interface DashboardStats {
  total_threads: number;
  awaiting_reply: number;
  replied: number;
  positive_replies: number;
  negative_replies: number;
  pending_follow_ups: number;
  drafts_for_review: number;
  reply_rate: number;
  avg_reply_time_hours: number | null;
}
