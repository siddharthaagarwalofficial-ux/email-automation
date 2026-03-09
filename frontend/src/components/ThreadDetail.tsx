"use client";

import { Thread, FollowUp } from "@/types";
import { api } from "@/lib/api";
import { useState } from "react";

interface Props {
  thread: Thread | null;
  loading: boolean;
  onFollowUpAction: () => void;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function FollowUpCard({ followUp, threadId, onAction }: { followUp: FollowUp; threadId: number; onAction: () => void }) {
  const [acting, setActing] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editSubject, setEditSubject] = useState(followUp.draft_subject || "");
  const [editBody, setEditBody] = useState(followUp.draft_body || "");

  const handleAction = async (action: string) => {
    setActing(true);
    try {
      await api.followUpAction(threadId, followUp.id, { action });
      onAction();
    } finally {
      setActing(false);
    }
  };

  const handleSaveEdit = async () => {
    setActing(true);
    try {
      await api.followUpAction(threadId, followUp.id, {
        action: "edit",
        edited_subject: editSubject,
        edited_body: editBody,
      });
      setEditing(false);
      onAction();
    } finally {
      setActing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditSubject(followUp.draft_subject || "");
    setEditBody(followUp.draft_body || "");
    setEditing(false);
  };

  const statusBadge: Record<string, string> = {
    scheduled: "bg-gray-100 text-gray-600",
    draft_ready: "bg-purple-100 text-purple-700",
    approved: "bg-green-100 text-green-700",
    sent: "bg-blue-100 text-blue-700",
    cancelled: "bg-red-100 text-red-600",
  };

  return (
    <div className="border rounded-lg p-4 bg-orange-50/50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">
          {followUp.sequence_number === 0 ? "Auto-Reply" : `Follow-up #${followUp.sequence_number}`}
        </span>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadge[followUp.status] || ""}`}>
            {followUp.status.replace("_", " ")}
          </span>
          <span className="text-xs text-gray-400">
            Scheduled: {formatDate(followUp.scheduled_for)}
          </span>
        </div>
      </div>

      {/* Read-only view */}
      {followUp.draft_body && !editing && (
        <div className="bg-white rounded border p-3 mt-2 text-sm">
          {followUp.draft_subject && (
            <p className="font-medium text-gray-700 mb-1">Subject: {followUp.draft_subject}</p>
          )}
          <p className="text-gray-600 whitespace-pre-wrap">{followUp.draft_body}</p>
        </div>
      )}

      {/* Inline edit mode */}
      {editing && (
        <div className="bg-white rounded border p-3 mt-2 space-y-2">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Subject</label>
            <input
              type="text"
              value={editSubject}
              onChange={(e) => setEditSubject(e.target.value)}
              className="w-full px-2 py-1.5 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Body</label>
            <textarea
              value={editBody}
              onChange={(e) => setEditBody(e.target.value)}
              rows={8}
              className="w-full px-2 py-1.5 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 resize-y"
            />
          </div>
          <div className="flex gap-2">
            <button
              disabled={acting}
              onClick={handleSaveEdit}
              className="px-3 py-1.5 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {acting ? "Saving..." : "Save Changes"}
            </button>
            <button
              disabled={acting}
              onClick={handleCancelEdit}
              className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-xs font-medium hover:bg-gray-200 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {followUp.status === "draft_ready" && !editing && (
        <div className="flex gap-2 mt-3">
          <button
            disabled={acting}
            onClick={() => handleAction("approve")}
            className="px-3 py-1.5 bg-green-600 text-white rounded text-xs font-medium hover:bg-green-700 disabled:opacity-50"
          >
            Approve & Queue
          </button>
          <button
            disabled={acting}
            onClick={() => {
              setEditSubject(followUp.draft_subject || "");
              setEditBody(followUp.draft_body || "");
              setEditing(true);
            }}
            className="px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded text-xs font-medium hover:bg-indigo-200 disabled:opacity-50"
          >
            Edit Draft
          </button>
          <button
            disabled={acting}
            onClick={() => handleAction("reject")}
            className="px-3 py-1.5 bg-red-100 text-red-700 rounded text-xs font-medium hover:bg-red-200 disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      )}

      {followUp.status === "approved" && (
        <div className="flex gap-2 mt-3">
          <button
            disabled={acting}
            onClick={async () => {
              setActing(true);
              try {
                await api.sendFollowUp(threadId, followUp.id);
                onAction();
              } finally {
                setActing(false);
              }
            }}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            Send Now
          </button>
        </div>
      )}

      {followUp.status === "sent" && followUp.sent_at && (
        <p className="text-xs text-green-600 mt-2">
          Sent on {formatDate(followUp.sent_at)}
        </p>
      )}
    </div>
  );
}

export default function ThreadDetail({ thread, loading, onFollowUpAction }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        Loading...
      </div>
    );
  }

  if (!thread) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        Select a thread to view details
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">{thread.subject}</h2>
        <p className="text-sm text-gray-500">
          To: {thread.recipient_name || thread.recipient_email} ({thread.recipient_email})
        </p>
      </div>

      {thread.classification && (
        <div className="mb-6 p-4 rounded-lg bg-blue-50 border border-blue-100">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium">Classification:</span>
            <span className="text-sm font-semibold capitalize">
              {thread.classification.category.replace("_", " ")}
            </span>
            <span className="text-xs text-gray-500">
              ({Math.round(thread.classification.confidence * 100)}% confidence)
            </span>
            {thread.classification.has_meeting_intent && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
                Meeting Intent Detected
              </span>
            )}
          </div>
          {thread.classification.reasoning && (
            <p className="text-xs text-gray-500 mt-1">{thread.classification.reasoning}</p>
          )}
        </div>
      )}

      <div className="space-y-4 mb-6">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Conversation</h3>
        {thread.emails.map((email) => (
          <div
            key={email.id}
            className={`rounded-lg border p-4 ${
              email.direction === "outbound"
                ? "bg-white border-gray-200"
                : "bg-green-50 border-green-200"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">
                {email.direction === "outbound" ? "You" : thread.recipient_name || thread.recipient_email}
              </span>
              <span className="text-xs text-gray-400">{formatDate(email.sent_at)}</span>
            </div>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{email.body}</p>
          </div>
        ))}
      </div>

      {thread.follow_ups.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Follow-ups</h3>
          {thread.follow_ups.map((fu) => (
            <FollowUpCard
              key={fu.id}
              followUp={fu}
              threadId={thread.id}
              onAction={onFollowUpAction}
            />
          ))}
        </div>
      )}
    </div>
  );
}
