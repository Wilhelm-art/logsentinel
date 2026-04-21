"use client";

import { useCallback, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { uploadLogFile } from "@/lib/api";
import styles from "./FileUpload.module.css";

const ALLOWED_EXTENSIONS = [".log", ".txt", ".jsonl", ".json"];
const MAX_SIZE_MB = 10;

const validateFile = (file: File): string | null => {
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `Invalid file type "${ext}". Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`;
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `File too large. Maximum size is ${MAX_SIZE_MB}MB.`;
  }
  if (file.size === 0) {
    return "File is empty.";
  }
  return null;
};

export default function FileUpload() {
  const { data: session } = useSession();
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback((file: File) => {
    setError(null);
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    setSelectedFile(file);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);

    try {
      const response = await uploadLogFile(
        selectedFile,
        session?.user?.email || undefined
      );
      router.push(`/analysis/${response.task_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(msg);
      setUploading(false);
    }
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => setDragOver(false);

  const handleClick = () => fileInputRef.current?.click();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className={styles.wrapper}>
      <div
        className={`upload-zone ${dragOver ? "dragover" : ""} ${styles.zone}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".log,.txt,.jsonl,.json"
          onChange={handleInputChange}
          className={styles.hiddenInput}
        />

        {!selectedFile ? (
          <>
            <div className={styles.uploadIcon}>
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <h3>Drop your log file here</h3>
            <p>or click to browse. Supports .log, .txt, .jsonl, .json (max {MAX_SIZE_MB}MB)</p>
          </>
        ) : (
          <div className={styles.selectedFile}>
            <div className={styles.fileIcon}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </div>
            <div className={styles.fileDetails}>
              <span className={styles.fileName}>{selectedFile.name}</span>
              <span className={styles.fileSize}>{formatSize(selectedFile.size)}</span>
            </div>
            <button
              className={styles.clearBtn}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                setError(null);
                if (fileInputRef.current) {
                  fileInputRef.current.value = "";
                }
              }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className={styles.error}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
          {error}
        </div>
      )}

      {selectedFile && (
        <button
          className={`btn btn-primary btn-lg ${styles.analyzeBtn}`}
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading ? (
            <>
              <span className="spinner" />
              Uploading & Analyzing...
            </>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              Analyze Log File
            </>
          )}
        </button>
      )}
    </div>
  );
}
