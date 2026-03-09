"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { DashboardStats, ThreadSummary, Thread } from "@/types";
import StatsCards from "@/components/StatsCards";
import ThreadList from "@/components/ThreadList";
import ThreadDetail from "@/components/ThreadDetail";
import Analytics from "@/components/Analytics";
import Routing from "@/components/Routing";

type Tab = "threads" | "analytics" | "routing";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("threads");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [runningPipeline, setRunningPipeline] = useState(false);
  const [pipelineResult, setPipelineResult] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        api.getStats(),
        api.getThreads(statusFilter ? { status: statusFilter } : undefined),
      ]);
      setStats(s);
      setThreads(t);
    } catch (err) {
      console.error("Failed to load data:", err);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSelectThread = async (id: number) => {
    setSelectedId(id);
    setLoadingDetail(true);
    try {
      const thread = await api.getThread(id);
      setSelectedThread(thread);
    } catch (err) {
      console.error("Failed to load thread:", err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await api.syncEmails();
      await loadData();
    } finally {
      setSyncing(false);
    }
  };

  const handleRunPipeline = async () => {
    setRunningPipeline(true);
    setPipelineResult(null);
    try {
      const result = await api.runPipeline();
      const parts = [];
      if (result.classification.classified > 0) parts.push(`${result.classification.classified} classified`);
      if (result.sequencing.scheduled > 0) parts.push(`${result.sequencing.scheduled} follow-ups scheduled`);
      if (result.drafting.drafted > 0) parts.push(`${result.drafting.drafted} drafts generated`);
      if (result.auto_replies.auto_replies_drafted > 0) parts.push(`${result.auto_replies.auto_replies_drafted} auto-replies drafted`);
      if (result.paused.cancelled > 0) parts.push(`${result.paused.cancelled} follow-ups paused`);
      setPipelineResult(parts.length > 0 ? parts.join(", ") : "No new actions needed");

      await loadData();
      if (selectedId) {
        const thread = await api.getThread(selectedId);
        setSelectedThread(thread);
      }
    } catch (err) {
      setPipelineResult("Pipeline failed — check API key");
      console.error("Pipeline error:", err);
    } finally {
      setRunningPipeline(false);
    }
  };

  const handleFollowUpAction = async () => {
    if (selectedId) {
      const thread = await api.getThread(selectedId);
      setSelectedThread(thread);
    }
    loadData();
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "threads", label: "Threads" },
    { key: "analytics", label: "Analytics" },
    { key: "routing", label: "Routing" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-white px-6 py-4 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Email Follow-Up Agent</h1>
              <p className="text-sm text-gray-500">AI-powered outreach automation</p>
            </div>
            <nav className="flex gap-1">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === tab.key
                      ? "bg-gray-100 text-gray-900"
                      : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {pipelineResult && (
              <span className="text-xs text-gray-500 max-w-md truncate">{pipelineResult}</span>
            )}
            <button
              onClick={handleRunPipeline}
              disabled={runningPipeline}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {runningPipeline ? "Running AI Pipeline..." : "Run AI Pipeline"}
            </button>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 disabled:opacity-50 transition-colors"
            >
              {syncing ? "Syncing..." : "Sync Emails"}
            </button>
          </div>
        </div>
      </header>

      {/* Stats — always visible */}
      <div className="px-6 py-4 flex-shrink-0">
        <StatsCards stats={stats} />
      </div>

      {/* Tab content */}
      <div className="flex-1 px-6 pb-6 min-h-0">
        {activeTab === "threads" && (
          <div className="flex gap-4 h-full" style={{ height: "calc(100vh - 240px)" }}>
            <div className="w-[400px] flex-shrink-0 bg-white rounded-lg border overflow-hidden">
              <ThreadList
                threads={threads}
                selectedId={selectedId}
                onSelect={handleSelectThread}
                statusFilter={statusFilter}
                onStatusFilter={setStatusFilter}
              />
            </div>
            <div className="flex-1 bg-white rounded-lg border overflow-hidden">
              <ThreadDetail
                thread={selectedThread}
                loading={loadingDetail}
                onFollowUpAction={handleFollowUpAction}
              />
            </div>
          </div>
        )}

        {activeTab === "analytics" && (
          <div className="bg-white rounded-lg border overflow-hidden" style={{ height: "calc(100vh - 240px)" }}>
            <Analytics />
          </div>
        )}

        {activeTab === "routing" && (
          <div className="bg-white rounded-lg border overflow-hidden" style={{ height: "calc(100vh - 240px)" }}>
            <Routing />
          </div>
        )}
      </div>
    </div>
  );
}
