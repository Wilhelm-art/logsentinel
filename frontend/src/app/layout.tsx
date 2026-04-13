import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "./providers";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "LogSentinel — AI Security Log Analyzer",
  description:
    "AI-powered security log analysis platform. Upload Nginx, Apache, or JSONL logs for automated threat detection, PII sanitization, and actionable WAF rule suggestions.",
  keywords: ["security", "log analysis", "AI", "threat detection", "WAF", "cybersecurity"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <div className="app-layout">
            <Sidebar />
            <main className="main-content">{children}</main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
