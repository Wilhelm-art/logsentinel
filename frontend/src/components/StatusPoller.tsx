"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { getTaskStatus } from "@/lib/api";
import { TaskStatus } from "@/lib/types";

const PIPELINE_STAGES = [
  { key: "pending", label: "Queued" },
  { key: "parsing", label: "Parsing" },
  { key: "sanitizing", label: "Sanitizing" },
  { key: "enriching", label: "Enriching" },
  { key: "llm_analysis", label: "AI Analysis" },
  { key: "completed", label: "Complete" },
];

interface StatusPollerProps {
  taskId: string;
  onComplete?: () => void;
}

export default function StatusPoller({ taskId, onComplete }: StatusPollerProps) {
  const { data: session } = useSession();
  const router = useRouter();
  const [status, setStatus] = useState<TaskStatus>("pending");
  const [stage, setStage] = useState("QUEUED");
  const [error, setError] = useState<string | null>(null);

  const pollStatus = useCallback(async () => {
    try {
      const data = await getTaskStatus(taskId, session?.user?.email || undefined);
      setStatus(data.status);
      setStage(data.progress_stage);

      if (data.status === "completed") {
        onComplete?.();
        return true;
      }
      if (data.status === "failed") {
        setError(data.error_message || "Analysis failed.");
        return true;
      }
      return false;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
      return true;
    }
  }, [taskId, session?.user?.email, onComplete]);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const startPolling = async () => {
      const done = await pollStatus();
      if (!done) {
        interval = setInterval(async () => {
          const finished = await pollStatus();
          if (finished) clearInterval(interval);
        }, 2000);
      }
    };

    startPolling();
    return () => clearInterval(interval);
  }, [pollStatus]);

  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.key === status);

  return (
    <div className="glass-card" style={{ padding: "2rem" }}>
      <h3 style={{ marginBottom: "1.5rem", textAlign: "center" }}>
        {status === "completed"
          ? "✅ Analysis Complete"
          : status === "failed"
          ? "❌ Analysis Failed"
          : "🔄 Analysis in Progress"}
      </h3>

      {/* Pipeline visualization */}
      <div className="pipeline">
        {PIPELINE_STAGES.map((s, i) => {
          const isActive = s.key === status;
          const isCompleted = i < currentIndex;
          const isFailed = status === "failed" && s.key === status;

          return (
            <div key={s.key} style={{ display: "contents" }}>
              {i > 0 && (
                <div
                  className={`pipeline-connector ${
                    isCompleted || isActive ? "completed" : ""
                  }`}
                />
              )}
              <div
                className={`pipeline-step ${
                  isActive ? "active" : ""
                } ${isCompleted ? "completed" : ""} ${
                  isFailed ? "failed" : ""
                }`}
              >
                <div className="step-dot">
                  {isCompleted ? "✓" : isFailed ? "✕" : i + 1}
                </div>
                <span className="step-label">{s.label}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Status details */}
      <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
        {status === "completed" ? (
          <p style={{ color: "var(--status-success)", fontSize: "0.9375rem" }}>
            Your security analysis report is ready.
          </p>
        ) : status === "failed" ? (
          <p style={{ color: "var(--severity-critical)", fontSize: "0.875rem" }}>
            {error}
          </p>
        ) : (
          <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
            Stage: <span style={{ color: "var(--accent-primary-light)" }}>{stage}</span>
            {" · "}Polling every 2 seconds...
          </p>
        )}
      </div>
    </div>
  );
}
