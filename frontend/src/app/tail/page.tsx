"use client";

import { useEffect, useState, useRef } from "react";
import { useSession } from "next-auth/react";

export default function TailPage() {
  const { data: session } = useSession();
  const [lines, setLines] = useState<string[]>([
    "LogSentinel Live Tail — Connecting...",
  ]);
  const [connected, setConnected] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const [filter, setFilter] = useState("");
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!session?.user?.email) return;

    const apiBase = process.env.NEXT_PUBLIC_API_URL || "";
    const eventSource = new EventSource(
      `${apiBase}/api/v1/logs/tail`,
      { withCredentials: true }
    );

    eventSource.onopen = () => {
      setConnected(true);
      setLines((prev) => [...prev, "✅ Connected to SSE stream"]);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "heartbeat") return;
        if (data.type === "connected") {
          setLines((prev) => [...prev, `✅ ${data.message}`]);
          return;
        }
        setLines((prev) => [...prev, event.data]);
      } catch {
        setLines((prev) => [...prev, event.data]);
      }
    };

    eventSource.onerror = () => {
      setConnected(false);
      setLines((prev) => [...prev, "❌ Connection lost. Reconnecting..."]);
    };

    return () => eventSource.close();
  }, [session]);

  useEffect(() => {
    if (autoScroll && bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [lines, autoScroll]);

  const filteredLines = filter
    ? lines.filter((l) => l.toLowerCase().includes(filter.toLowerCase()))
    : lines;

  return (
    <div style={{ maxWidth: 1100 }}>
      <div className="page-header">
        <h1>
          Live Tail{" "}
          <span
            className={`badge ${connected ? "badge-success" : "badge-critical"}`}
            style={{ fontSize: "0.625rem", verticalAlign: "middle" }}
          >
            {connected ? "CONNECTED" : "DISCONNECTED"}
          </span>
        </h1>
        <p>Real-time log stream — bypasses AI analysis for raw visibility.</p>
      </div>

      {/* Controls */}
      <div className="flex gap-md items-center" style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          className="input"
          placeholder="Filter logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{ maxWidth: 300 }}
        />
        <label className="flex items-center gap-sm" style={{ fontSize: "0.875rem", color: "var(--text-muted)", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
          />
          Auto-scroll
        </label>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => setLines([])}
        >
          Clear
        </button>
      </div>

      {/* Terminal */}
      <div className="terminal">
        <div className="terminal-header">
          <div className="terminal-dot" style={{ background: connected ? "#22c55e" : "#ef4444" }} />
          <div className="terminal-dot" style={{ background: "#eab308" }} />
          <div className="terminal-dot" style={{ background: "#64748b" }} />
          <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem", color: "var(--text-dim)" }}>
            logsentinel — live tail
          </span>
        </div>
        <div className="terminal-body" ref={bodyRef} style={{ maxHeight: "65vh", overflow: "auto" }}>
          {filteredLines.map((line, i) => (
            <pre key={i} className="terminal-line">
              <span style={{ color: "var(--text-dim)", marginRight: "1rem" }}>
                {String(i + 1).padStart(4, " ")}
              </span>
              {line}
            </pre>
          ))}
          {filteredLines.length === 0 && (
            <pre className="terminal-line" style={{ color: "var(--text-dim)" }}>
              {filter ? "No matching lines." : "Waiting for log data..."}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
