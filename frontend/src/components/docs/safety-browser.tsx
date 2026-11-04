"use client";

import { useMemo, useState } from "react";

export type SafetyCategory = "All" | "Motion" | "Separation" | "Arena" | "Formation" | "Agent Budget";

export interface SafetyContract {
  parameter: string;
  category: "Motion" | "Separation" | "Arena" | "Formation" | "Agent Budget";
  enforcedValue: string;
  enforcementLayer: string;
  vetoBehavior: string;
}

export const SAFETY_CONTRACTS: SafetyContract[] = [
  {
    parameter: "maximum_speed",
    category: "Motion",
    enforcedValue: "0.10 to 0.60 m/s (default 0.50 m/s)",
    enforcementLayer: "SafetyFilter & integrate_state",
    vetoBehavior: "Velocity commands scaled down to ceiling; excess speed physically cannot integrate into state."
  },
  {
    parameter: "minimum_robot_separation",
    category: "Separation",
    enforcedValue: "0.25 to 1.20 m (default 0.35 m)",
    enforcementLayer: "SafetyFilter pairwise distance check",
    vetoBehavior: "If distance between rovers < separation, velocities scaled progressively (1.0 -> 0.6 -> 0.3 -> 0.0)."
  },
  {
    parameter: "minimum_obstacle_clearance",
    category: "Arena",
    enforcedValue: "0.05 to 0.80 m (default 0.20 m)",
    enforcementLayer: "Region.clearance() evaluation",
    vetoBehavior: "Clearance violations trigger immediate velocity scaling or emergency stationary hold."
  },
  {
    parameter: "boundary_margin",
    category: "Arena",
    enforcedValue: "0.12 m inside 10.0 x 10.0 m boundary",
    enforcementLayer: "validate_state() geometric boundary check",
    vetoBehavior: "Positions outside boundary margin [0.12, 9.88] m are rejected with arena_boundary intervention."
  },
  {
    parameter: "formation_ring_radius",
    category: "Formation",
    enforcedValue: "0.80 to 2.50 m (default 1.50 m)",
    enforcementLayer: "Pydantic FormationSpec & feasibility validator",
    vetoBehavior: "Specs where separation > 2*R*sin(pi/N)*0.95 are rejected at compile time before execution."
  },
  {
    parameter: "max_replans",
    category: "Agent Budget",
    enforcedValue: "Hard ceiling of 2 replans per run",
    enforcementLayer: "Orchestration runner loop counter",
    vetoBehavior: "Subsequent replan checkpoints ignored; simulator continues under current plan."
  },
  {
    parameter: "max_model_calls",
    category: "Agent Budget",
    enforcedValue: "Ceiling of 4 calls per run, 30s timeout",
    enforcementLayer: "BasetenDecisionProvider call limiter",
    vetoBehavior: "Excess calls blocked to prevent API budget exhaustion or latency stalls."
  }
];

const CATEGORIES: SafetyCategory[] = ["All", "Motion", "Separation", "Arena", "Formation", "Agent Budget"];

export function SafetyBrowser() {
  const [selectedCategory, setSelectedCategory] = useState<SafetyCategory>("All");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredContracts = useMemo(() => {
    return SAFETY_CONTRACTS.filter((item) => {
      const matchesCategory = selectedCategory === "All" || item.category === selectedCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        item.parameter.toLowerCase().includes(q) ||
        item.enforcedValue.toLowerCase().includes(q) ||
        item.enforcementLayer.toLowerCase().includes(q) ||
        item.vetoBehavior.toLowerCase().includes(q);
      return matchesCategory && matchesSearch;
    });
  }, [selectedCategory, searchQuery]);

  return (
    <div className="safety-browser">
      <div className="safety-browser-header">
        <div className="safety-title-row">
          <span className="safety-tag">INVARIANT DIRECTORY</span>
          <span className="safety-count-pill">
            {filteredContracts.length} of {SAFETY_CONTRACTS.length} CONTRACTS ACTIVE
          </span>
        </div>
        <p className="safety-lead">
          Inspect deterministic limits enforced by Pydantic models, geometric validators, and the pre-step safety filter.
        </p>
      </div>

      <div className="safety-controls-bar">
        <div className="safety-category-tabs" role="tablist" aria-label="Safety category filter">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              role="tab"
              aria-selected={selectedCategory === cat}
              onClick={() => setSelectedCategory(cat)}
              className={`cat-tab ${selectedCategory === cat ? "is-active" : ""}`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="safety-search-box">
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search invariants or layers..."
            className="safety-search-input"
            aria-label="Filter safety contracts"
          />
        </div>
      </div>

      <div className="safety-table-wrapper" role="region" aria-label="Deterministic safety contracts" tabIndex={0}>
        <table className="safety-table">
          <thead>
            <tr>
              <th scope="col">Parameter</th>
              <th scope="col">Category</th>
              <th scope="col">Enforced Value</th>
              <th scope="col">Enforcement Layer</th>
              <th scope="col">Deterministic Veto Behavior</th>
            </tr>
          </thead>
          <tbody>
            {filteredContracts.map((c) => (
              <tr key={c.parameter}>
                <th scope="row">
                  <code>{c.parameter}</code>
                </th>
                <td>
                  <span className="table-cat-badge">{c.category}</span>
                </td>
                <td className="value-cell">{c.enforcedValue}</td>
                <td className="layer-cell">
                  <code>{c.enforcementLayer}</code>
                </td>
                <td className="veto-cell">{c.vetoBehavior}</td>
              </tr>
            ))}
            {filteredContracts.length === 0 && (
              <tr>
                <td colSpan={5} className="empty-cell">
                  No safety contracts match your filter query.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
