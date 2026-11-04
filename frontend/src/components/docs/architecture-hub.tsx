"use client";

import { useState } from "react";
import { SubsystemExplorer } from "./subsystem-explorer";
import { LifecycleVisualizer } from "./lifecycle-visualizer";
import { SafetyBrowser } from "./safety-browser";
import { ApiConsole } from "./api-console";

export type HubTab = "topology" | "lifecycle" | "safety" | "api";

export function ArchitectureHub({ defaultTab = "topology" }: { defaultTab?: HubTab }) {
  const [activeTab, setActiveTab] = useState<HubTab>(defaultTab);

  return (
    <div className="architecture-hub">
      <div className="hub-nav-bar" role="tablist" aria-label="Architecture exploration modules">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "topology"}
          onClick={() => setActiveTab("topology")}
          className={`hub-tab-btn ${activeTab === "topology" ? "is-active" : ""}`}
        >
          <span className="hub-tab-num">01</span>
          <span className="hub-tab-label">Subsystem Topology</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "lifecycle"}
          onClick={() => setActiveTab("lifecycle")}
          className={`hub-tab-btn ${activeTab === "lifecycle" ? "is-active" : ""}`}
        >
          <span className="hub-tab-num">02</span>
          <span className="hub-tab-label">Lifecycle State Machine</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "safety"}
          onClick={() => setActiveTab("safety")}
          className={`hub-tab-btn ${activeTab === "safety" ? "is-active" : ""}`}
        >
          <span className="hub-tab-num">03</span>
          <span className="hub-tab-label">Deterministic Invariants</span>
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={activeTab === "api"}
          onClick={() => setActiveTab("api")}
          className={`hub-tab-btn ${activeTab === "api" ? "is-active" : ""}`}
        >
          <span className="hub-tab-num">04</span>
          <span className="hub-tab-label">API Console & Payloads</span>
        </button>
      </div>

      <div className="hub-content-container">
        {activeTab === "topology" && <SubsystemExplorer />}
        {activeTab === "lifecycle" && <LifecycleVisualizer />}
        {activeTab === "safety" && <SafetyBrowser />}
        {activeTab === "api" && <ApiConsole />}
      </div>
    </div>
  );
}

export { SubsystemExplorer } from "./subsystem-explorer";
export { LifecycleVisualizer } from "./lifecycle-visualizer";
export { SafetyBrowser } from "./safety-browser";
export { ApiConsole } from "./api-console";
