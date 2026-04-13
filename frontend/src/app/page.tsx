"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getHistory } from "@/lib/api";
import { HistoryItem } from "@/lib/types";
import styles from "./page.module.css";

export default function DashboardPage() {
  const { data: session, status: authStatus } = useSession();
  const router = useRouter();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authStatus === "unauthenticated") {
      router.push("/auth/signin");
      return;
    }

    if (session?.user?.email) {
      getHistory(10, session.user.email)
        .then((data) => setHistory(data.history))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [session, authStatus, router]);

  if (authStatus === "loading" || authStatus === "unauthenticated") {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ width: 40, height: 40 }} />
      </div>
    );
  }

  const stats = {
    total: history.length,
    threats: history.reduce((acc, h) => acc + (h.incident_count || 0), 0),
    critical: history.filter((h) => h.top_severity === "CRITICAL").length,
    completed: history.filter((h) => h.status === "completed").length,
  };

  const severityBadge = (severity?: string) => {
    if (!severity) return null;
    const cls = `badge badge-${severity.toLowerCase()}`;
    return <span className={cls}>{severity}</span>;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  };

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <div className="page-header">
        <h1>
          Welcome back, <span className="text-gradient">{session?.user?.name || "Analyst"}</span>
        </h1>
        <p>Monitor your security posture and recent analysis results.</p>
      </div>

      {/* Stats Grid */}
      <div className={`grid-stats stagger ${styles.statsGrid}`}>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Total Scans</span>
          <span className="stat-value">{stats.total}</span>
          <span className="stat-detail">All-time analyses</span>
        </div>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Threats Found</span>
          <span className="stat-value" style={{ background: "linear-gradient(135deg, var(--severity-high), var(--severity-critical))", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {stats.threats}
          </span>
          <span className="stat-detail">Total incidents detected</span>
        </div>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Critical Alerts</span>
          <span className="stat-value" style={{ background: "linear-gradient(135deg, var(--severity-critical), #dc2626)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            {stats.critical}
          </span>
          <span className="stat-detail">Require immediate action</span>
        </div>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Success Rate</span>
          <span className="stat-value">
            {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 100}%
          </span>
          <span className="stat-detail">Completed analyses</span>
        </div>
      </div>

      {/* Quick Actions */}
      <div className={styles.quickActions}>
        <Link href="/upload" className={`btn btn-primary btn-lg ${styles.uploadBtn}`}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload New Log File
        </Link>
        <Link href="/tail" className={`btn btn-secondary btn-lg`}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          Live Tail
        </Link>
      </div>

      {/* Recent Analyses */}
      <div className={styles.recentSection}>
        <div className={styles.sectionHeader}>
          <h2>Recent Analyses</h2>
          {history.length > 0 && (
            <Link href="/history" className="btn btn-ghost btn-sm">
              View All →
            </Link>
          )}
        </div>

        {loading ? (
          <div className="glass-card" style={{ padding: "2rem" }}>
            <div className="skeleton" style={{ height: 20, width: "60%", marginBottom: "1rem" }} />
            <div className="skeleton" style={{ height: 16, width: "80%", marginBottom: "0.5rem" }} />
            <div className="skeleton" style={{ height: 16, width: "40%" }} />
          </div>
        ) : history.length === 0 ? (
          <div className="glass-card empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: 0.3, marginBottom: "1rem" }}>
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <h3>No analyses yet</h3>
            <p>Upload your first log file to get started with AI-powered security analysis.</p>
          </div>
        ) : (
          <div className="glass-card" style={{ overflow: "hidden" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Status</th>
                  <th>Format</th>
                  <th>Lines</th>
                  <th>Incidents</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr
                    key={item.task_id}
                    onClick={() => {
                      if (item.status === "completed") {
                        router.push(`/analysis/${item.task_id}`);
                      }
                    }}
                    style={{ cursor: item.status === "completed" ? "pointer" : "default" }}
                  >
                    <td>
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                        {item.original_filename}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${
                        item.status === "completed" ? "badge-success" :
                        item.status === "failed" ? "badge-critical" : "badge-processing"
                      }`}>
                        {item.status}
                      </span>
                    </td>
                    <td>{item.log_format?.toUpperCase() || "—"}</td>
                    <td>{item.line_count?.toLocaleString() || "—"}</td>
                    <td>
                      {item.incident_count != null ? (
                        <span className="flex items-center gap-sm">
                          {item.incident_count}
                          {severityBadge(item.top_severity)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td style={{ color: "var(--text-dim)", fontSize: "0.8125rem" }}>
                      {formatDate(item.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
