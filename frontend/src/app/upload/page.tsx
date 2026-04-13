import FileUpload from "@/components/FileUpload";

export const metadata = {
  title: "Upload Log File — LogSentinel",
  description: "Upload your Nginx, Apache, or JSONL log files for AI-powered security analysis.",
};

export default function UploadPage() {
  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <div className="page-header" style={{ textAlign: "center" }}>
        <h1>Upload Log File</h1>
        <p>
          Upload your web server logs for automated threat detection and security analysis.
          Supports Nginx, Apache, and JSONL formats.
        </p>
      </div>

      <FileUpload />

      {/* Info cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginTop: "3rem",
        }}
        className="stagger"
      >
        <div className="glass-card animate-in" style={{ padding: "1.25rem" }}>
          <div style={{ color: "var(--accent-secondary)", marginBottom: "0.5rem" }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <h4 style={{ fontSize: "0.9375rem", marginBottom: "0.25rem" }}>PII Sanitization</h4>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            IPs are hashed, emails & JWTs stripped before AI analysis.
          </p>
        </div>

        <div className="glass-card animate-in" style={{ padding: "1.25rem" }}>
          <div style={{ color: "var(--accent-primary-light)", marginBottom: "0.5rem" }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
          </div>
          <h4 style={{ fontSize: "0.9375rem", marginBottom: "0.25rem" }}>Threat Intelligence</h4>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            IPs cross-referenced with AbuseIPDB for known threats.
          </p>
        </div>

        <div className="glass-card animate-in" style={{ padding: "1.25rem" }}>
          <div style={{ color: "var(--severity-high)", marginBottom: "0.5rem" }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </div>
          <h4 style={{ fontSize: "0.9375rem", marginBottom: "0.25rem" }}>WAF Suggestions</h4>
          <p style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}>
            Get actionable Nginx/WAF rules to block detected attacks.
          </p>
        </div>
      </div>
    </div>
  );
}
