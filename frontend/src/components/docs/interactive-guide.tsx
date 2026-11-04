"use client";

import Link from "next/link";
import { useState } from "react";

import { apiRequest } from "@/lib/api";
import type { Health } from "@/lib/types";

const setupSteps = [
  { title: "Install prerequisites", body: "Install Python 3.11 or newer and Node.js 20.9 or newer with npm. Open PowerShell at the repository root.", command: "py -3 --version\nnode --version\nnpm --version" },
  { title: "Install the backend", body: "Create the virtual environment and install the backend. Run these commands from the repository root.", command: 'py -3 -m venv backend/.venv\n.\\backend\\.venv\\Scripts\\python.exe -m pip install -e "backend[dev]"' },
  { title: "Install the frontend", body: "Install the dependencies recorded in the lockfile.", command: "npm ci --prefix frontend" },
  { title: "Start the backend", body: "Run this in its own terminal and leave it open. Offline mode needs no API key.", command: ".\\backend\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000" },
  { title: "Start the frontend", body: "Open a second terminal at the repository root, run this command, and leave it open.", command: "npm --prefix frontend run dev -- --hostname 127.0.0.1" },
  { title: "Check the connection", body: "Open the workbench at http://127.0.0.1:3000. Check the backend below before starting your first mission.", command: null },
] as const;

const walkthrough = [
  { title: "Choose an arena and swarm", body: "Open Mission, choose Open field and the Balanced ring preset. Keep seed 42 for a repeatable run." },
  { title: "Choose offline mode", body: "Open Advanced settings. Select Offline mock for the mission compiler and Off for agent decisions. This walkthrough makes no model requests." },
  { title: "Compile and review", body: "Select Compile mission. Check the six-robot ring, assumptions and safety limits. Resolve any clarification questions before approving." },
  { title: "Approve and run", body: "Select the approval checkbox and Run approved mission. The Arena opens with the recorded trajectory." },
  { title: "Inspect results", body: "Open Run results to examine the outcome, trajectory metrics and safety events. A stopped run is a reported result, not an automatic success." },
] as const;

export function InteractiveGuide() {
  const [setupIndex, setSetupIndex] = useState(0);
  const [walkIndex, setWalkIndex] = useState(0);
  const [status, setStatus] = useState("Not checked yet.");
  const [copied, setCopied] = useState("");
  const step = setupSteps[setupIndex];
  const walk = walkthrough[walkIndex];

  async function copyCommand(command: string) {
    try {
      await navigator.clipboard.writeText(command);
      setCopied("Copied to clipboard.");
    } catch {
      setCopied("Copy unavailable. Select the command text and copy it manually.");
    }
  }

  async function checkBackend() {
    setStatus("Checking backend...");
    try {
      const health = await apiRequest<Health>("/api/health");
      setStatus(`Backend connected. Server default: ${health.provider.configured ? "Baseten configured" : "offline mock"}. This check did not call a model.`);
    } catch {
      setStatus("Backend unavailable. Confirm it is running and that this page can reach the configured API URL.");
    }
  }

  return (
    <div className="guide-interactive">
      <div className="guide-panel">
        <p className="guide-counter">SETUP · {setupIndex + 1} / {setupSteps.length}</p>
        <h3>{step.title}</h3>
        <p>{step.body}</p>
        {step.command ? <><pre className="code-block"><code>{step.command}</code></pre><button type="button" className="guide-button" onClick={() => copyCommand(step.command!)}>Copy commands</button><span className="guide-status" role="status">{copied}</span></> : <><button type="button" className="guide-button" onClick={checkBackend}>Check backend</button><p className="guide-status" role="status">{status}</p></>}
        <div className="guide-actions">
          <button type="button" className="guide-button" disabled={setupIndex === 0} onClick={() => { setSetupIndex(setupIndex - 1); setCopied(""); }}>Previous</button>
          <button type="button" className="guide-button guide-primary" disabled={setupIndex === setupSteps.length - 1} onClick={() => { setSetupIndex(setupIndex + 1); setCopied(""); }}>Next step</button>
        </div>
      </div>
      <div className="guide-panel">
        <p className="guide-counter">FIRST RUN · {walkIndex + 1} / {walkthrough.length}</p>
        <h3>{walk.title}</h3>
        <p>{walk.body}</p>
        <div className="guide-actions">
          <button type="button" className="guide-button" disabled={walkIndex === 0} onClick={() => setWalkIndex(walkIndex - 1)}>Previous</button>
          {walkIndex < walkthrough.length - 1 ? <button type="button" className="guide-button guide-primary" onClick={() => setWalkIndex(walkIndex + 1)}>Next step</button> : <Link className="guide-button guide-primary" href="/">Open workbench</Link>}
        </div>
      </div>
    </div>
  );
}
