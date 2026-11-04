"use client";

import { useState } from "react";
import { API_BASE, apiRequest } from "@/lib/api";

const endpoints = [
  { path: "/api/health", description: "Backend status and the server default provider." },
  { path: "/api/scenarios", description: "Built-in arenas and their public geometry." },
] as const;

export function ApiConsole() {
  const [selected, setSelected] = useState(0);
  const [output, setOutput] = useState("Run a read-only request to see the actual response.");
  const [busy, setBusy] = useState(false);

  async function runRequest() {
    setBusy(true);
    try {
      const result = await apiRequest<unknown>(endpoints[selected].path);
      setOutput(JSON.stringify(result, null, 2));
    } catch (error) {
      setOutput(error instanceof Error ? error.message : "The backend could not be reached.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="guide-panel">
      <label className="field-group" htmlFor="guide-endpoint">
        <span className="field-label">Read-only endpoint</span>
        <select id="guide-endpoint" value={selected} onChange={(event) => { setSelected(Number(event.target.value)); setOutput("Run a read-only request to see the actual response."); }}>
          {endpoints.map((endpoint, index) => <option value={index} key={endpoint.path}>GET {endpoint.path}</option>)}
        </select>
      </label>
      <p>{endpoints[selected].description} No model call is made.</p>
      <button type="button" className="guide-button guide-primary" onClick={runRequest} disabled={busy}>{busy ? "Checking..." : "Send request"}</button>
      <pre className="code-block" aria-live="polite"><code>{output}</code></pre>
      <p>For compile and run contracts, open the <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">backend API reference</a>.</p>
    </div>
  );
}
