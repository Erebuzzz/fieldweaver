"use client";

import { useState } from "react";

export function LicenseCopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard fallback
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="copy-btn"
      aria-label="Copy MIT license text to clipboard"
    >
      {copied ? "COPIED" : "COPY LICENSE TEXT"}
    </button>
  );
}
