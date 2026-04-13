"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { getHistory } from "@/lib/api";
import { HistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (session?.user?.email) {
      getHistory(100, session.user.email)
        .then((data) => setHistory(data.history))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [session]);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  };

  return (
    <div style={{ maxWidth: 1100 }}>
      <div className="page-header">
        <h1>Analysis History</h1>
        <p>Browse all previous security analyses and their results.</p>
      </div>

      {loading ? (
        <div className="glass-card" style={{ padding: "2rem" }}>
          {[1, 2, 3].map((i) => (
            <div key={i} style={{ marginBottom: "1rem" }}>
              <div className="skeleton" style={{ height: 20, width: `${80 - i * 15}%`, marginBottom: "0.5rem" }} />
              <div className="skeleton" style={{ height: 16, width: `${60 - i * 10}%` }} />
            </div>
          ))}
        </div>
      ) : history.length === 0 ? (
        <div className="glass-card empty-state">
          <h3>No analysis history</h3>
          <p>Upload your first log file to start building your security analysis history.</p>
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
                <th>Top Severity</th>
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
                    <br />
                    <span style={{ fontSize: "0.75rem", color: "var(--text-dim)", fontFamily: "'JetBrains Mono', monospace" }}>
                      {item.file_hash.substring(0, 12)}...
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
                  <td>{item.incident_count ?? "—"}</td>
                  <td>
                    {item.top_severity ? (
                      <span className={`badge badge-${item.top_severity.toLowerCase()}`}>
                        {item.top_severity}
                      </span>
                    ) : "—"}
                  </td>
                  <td style={{ fontSize: "0.8125rem", color: "var(--text-dim)" }}>
                    {formatDate(item.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
