"use client";

import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import styles from "./page.module.css";

function SignInContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");

  return (
    <div className={styles.container}>
      {/* Background animated elements */}
      <div className={styles.bgOrb1} />
      <div className={styles.bgOrb2} />
      <div className={styles.gridOverlay} />

      <div className={styles.card}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoIcon}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <h1 className={styles.logoTitle}>LogSentinel</h1>
          <p className={styles.logoSub}>AI-Powered Security Log Analyzer</p>
        </div>

        {error && (
          <div className={styles.error}>
            {error === "AccessDenied" ? (
              <>
                <strong>Access Denied</strong>
                <p>Your email is not in the allowed users list. Contact your administrator.</p>
              </>
            ) : error === "Configuration" ? (
              <>
                <strong>Server Configuration Error</strong>
                <p>Authentication providers (Google/GitHub) are missing from the server environment setup. Please configure API keys.</p>
              </>
            ) : (
              <>
                <strong>Authentication Error</strong>
                <p>An error occurred during sign in. Please try again.</p>
              </>
            )}
          </div>
        )}

        {/* Auth buttons */}
        <div className={styles.authButtons}>


          <button
            onClick={() => signIn("github", { callbackUrl: "/" })}
            className={styles.authBtn}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            Continue with GitHub
          </button>
        </div>

        <p className={styles.disclaimer}>
          Access restricted to authorized personnel only.
        </p>
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={
      <div className={styles.container}>
        <div className={styles.card}>
          <div className="spinner" style={{ width: 40, height: 40, margin: "2rem auto" }} />
        </div>
      </div>
    }>
      <SignInContent />
    </Suspense>
  );
}
