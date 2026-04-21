"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import { getReport, getTaskStatus } from "@/lib/api";
import { ReportResponse, TaskStatus } from "@/lib/types";
import StatusPoller from "@/components/StatusPoller";
import styles from "./page.module.css";

export default function AnalysisPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const { data: session } = useSession();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [status, setStatus] = useState<TaskStatus>("pending");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const email = session?.user?.email || undefined;

      // Check status first
      const statusData = await getTaskStatus(taskId, email);
      setStatus(statusData.status);

      if (statusData.status === "completed") {
        const reportData = await getReport(taskId, email);
        setReport(reportData);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [session?.user?.email, taskId]);

  useEffect(() => {
    if (session) fetchData();
  }, [session, fetchData]);

  const handleComplete = useCallback(() => {
    fetchData();
  }, [fetchData]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ width: 40, height: 40 }} />
        <p style={{ marginTop: "1rem", color: "var(--text-muted)" }}>Loading analysis...</p>
      </div>
    );
  }

  // Show poller for in-progress tasks
  if (status !== "completed" && status !== "failed") {
    return (
      <div style={{ maxWidth: 800, margin: "0 auto" }}>
        <div className="page-header" style={{ textAlign: "center" }}>
          <h1>Analyzing Log File</h1>
          <p>Your log file is being processed through the security analysis pipeline.</p>
        </div>
        <StatusPoller taskId={taskId} onComplete={handleComplete} />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="empty-state">
        <h3>Error Loading Report</h3>
        <p>{error || "Report not found."}</p>
      </div>
    );
  }

  const { report: securityReport } = report;
  const criticalCount = securityReport.incidents.filter((i) => i.severity === "CRITICAL").length;
  const highCount = securityReport.incidents.filter((i) => i.severity === "HIGH").length;
  const mediumCount = securityReport.incidents.filter((i) => i.severity === "MEDIUM").length;
  const lowCount = securityReport.incidents.filter((i) => i.severity === "LOW").length;

  return (
    <div className={styles.reportPage}>
      {/* Header */}
      <div className={styles.reportHeader}>
        <div>
          <h1>Security Analysis Report</h1>
          <div className={styles.meta}>
            <span>📄 {report.original_filename}</span>
            <span>•</span>
            <span>{report.log_format?.toUpperCase() || "Unknown"} format</span>
            <span>•</span>
            <span>{report.line_count?.toLocaleString() || "?"} lines</span>
            {report.sampled && (
              <>
                <span>•</span>
                <span className="badge badge-processing">Sampled: {report.sampled.toLocaleString()}</span>
              </>
            )}
          </div>
          <div className={styles.meta} style={{ marginTop: "0.25rem" }}>
            <span>🤖 {report.llm_provider?.toUpperCase()} ({report.llm_model})</span>
            <span>•</span>
            <span>⏱ {report.processing_time_seconds}s</span>
            <span>•</span>
            <span>🔒 {report.file_hash.substring(0, 16)}...</span>
          </div>
        </div>
      </div>

      {/* Severity Stats */}
      <div className={`grid-stats stagger ${styles.severityGrid}`}>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Critical</span>
          <span className="stat-value" style={{ color: "var(--severity-critical)", WebkitTextFillColor: "var(--severity-critical)" }}>
            {criticalCount}
          </span>
        </div>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">High</span>
          <span className="stat-value" style={{ color: "var(--severity-high)", WebkitTextFillColor: "var(--severity-high)" }}>
            {highCount}
          </span>
        </div>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Medium</span>
          <span className="stat-value" style={{ color: "var(--severity-medium)", WebkitTextFillColor: "var(--severity-medium)" }}>
            {mediumCount}
          </span>
        </div>
        <div className="glass-card stat-card animate-in">
          <span className="stat-label">Low</span>
          <span className="stat-value" style={{ color: "var(--severity-low)", WebkitTextFillColor: "var(--severity-low)" }}>
            {lowCount}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className={`glass-card ${styles.summaryCard}`}>
        <h2>Executive Summary</h2>
        <div className={styles.summaryContent}>
          {securityReport.summary.split("\n").map((paragraph, i) => (
            <p key={i}>{paragraph}</p>
          ))}
        </div>
      </div>

      {/* Incidents */}
      <div className={styles.incidentsSection}>
        <h2>Detected Incidents ({securityReport.incidents.length})</h2>

        {securityReport.incidents.length === 0 ? (
          <div className="glass-card empty-state" style={{ padding: "2rem" }}>
            <h3 style={{ color: "var(--status-success)" }}>✅ No Threats Detected</h3>
            <p>The AI analysis found no security incidents in the log file.</p>
          </div>
        ) : (
          <div className={styles.incidentsList}>
            {securityReport.incidents.map((incident, i) => (
              <div
                key={i}
                className={`glass-card ${styles.incidentCard} animate-in`}
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className={styles.incidentHeader}>
                  <span className={`badge badge-${incident.severity.toLowerCase()}`}>
                    {incident.severity}
                  </span>
                  <span className={styles.attackType}>{incident.attack_type}</span>
                </div>

                <div className={styles.incidentMeta}>
                  <div>
                    <span className={styles.metaLabel}>Target</span>
                    <code className={styles.endpoint}>{incident.target_endpoint}</code>
                  </div>
                  <div>
                    <span className={styles.metaLabel}>Actor</span>
                    <code
                      className={styles.actorHash}
                      onClick={() => copyToClipboard(incident.actor_hash)}
                      title="Click to copy"
                    >
                      {incident.actor_hash}
                    </code>
                  </div>
                </div>

                <p className={styles.incidentDesc}>{incident.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* WAF Suggestions */}
      {securityReport.waf_rule_suggestions.length > 0 && (
        <div className={styles.wafSection}>
          <h2>WAF Rule Suggestions</h2>
          <div className={styles.wafList}>
            {securityReport.waf_rule_suggestions.map((rule, i) => (
              <div key={i} className="code-block">
                <button
                  className="copy-btn"
                  onClick={() => copyToClipboard(rule)}
                >
                  Copy
                </button>
                <pre>{rule}</pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
