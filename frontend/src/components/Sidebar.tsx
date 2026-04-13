"use client";

import { useSession, signOut } from "next-auth/react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import styles from "./Sidebar.module.css";

const navItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="9" rx="1" />
        <rect x="14" y="3" width="7" height="5" rx="1" />
        <rect x="14" y="12" width="7" height="9" rx="1" />
        <rect x="3" y="16" width="7" height="5" rx="1" />
      </svg>
    ),
  },
  {
    label: "Upload",
    href: "/upload",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
  {
    label: "Live Tail",
    href: "/tail",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
  {
    label: "History",
    href: "/history",
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const { data: session } = useSession();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  // Don't show sidebar on auth pages
  if (pathname?.startsWith("/auth")) return null;

  return (
    <>
      {/* Mobile overlay */}
      <button
        className={styles.mobileToggle}
        onClick={() => setCollapsed(!collapsed)}
        aria-label="Toggle navigation"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>

      <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ""}`}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoIcon}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          {!collapsed && (
            <div className={styles.logoText}>
              <span className={styles.logoTitle}>LogSentinel</span>
              <span className={styles.logoSub}>AI Security</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className={styles.nav}>
          {navItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.href !== "/" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`${styles.navItem} ${isActive ? styles.active : ""}`}
                title={collapsed ? item.label : undefined}
              >
                <span className={styles.navIcon}>{item.icon}</span>
                {!collapsed && <span className={styles.navLabel}>{item.label}</span>}
                {isActive && <span className={styles.activeIndicator} />}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        {session?.user && (
          <div className={styles.userSection}>
            <div className={styles.userInfo}>
              {session.user.image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={session.user.image}
                  alt="Avatar"
                  className={styles.avatar}
                  width={32}
                  height={32}
                />
              ) : (
                <div className={styles.avatarPlaceholder}>
                  {(session.user.name || session.user.email || "U")[0].toUpperCase()}
                </div>
              )}
              {!collapsed && (
                <div className={styles.userText}>
                  <span className={styles.userName}>
                    {session.user.name || "User"}
                  </span>
                  <span className={styles.userEmail}>
                    {session.user.email}
                  </span>
                </div>
              )}
            </div>
            <button
              onClick={() => signOut()}
              className={styles.signOutBtn}
              title="Sign out"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
