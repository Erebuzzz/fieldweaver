"use client";

import { useState } from "react";

interface MetricData {
  mean: number;
  median: number;
  sample_stddev: number;
  sample_count?: number;
}

interface ControllerMetrics {
  metrics: Record<string, MetricData>;
  sample_count: number;
  success_count: number;
  success_rate: number;
}

interface MetricRowDef {
  key: string;
  label: string;
  unit: string;
}

interface Props {
  quadratic: ControllerMetrics;
  baseline: ControllerMetrics;
  metricRows: readonly MetricRowDef[];
}

type ViewMode = "side-by-side" | "quadratic" | "baseline" | "delta";

function formatVal(value: number, unit: string): string {
  const precision = unit === "count" ? 0 : 3;
  return `${value.toFixed(precision)}${unit === "count" ? "" : ` ${unit}`}`;
}

export function EvaluationControllerView({ quadratic, baseline, metricRows }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>("side-by-side");

  return (
    <div className="evaluation-controller-view">
      <div className="eval-view-controls">
        <div className="eval-mode-tabs" role="tablist" aria-label="Controller comparison view modes">
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "side-by-side"}
            onClick={() => setViewMode("side-by-side")}
            className={`eval-tab ${viewMode === "side-by-side" ? "is-active" : ""}`}
          >
            Side-by-Side Comparison
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "quadratic"}
            onClick={() => setViewMode("quadratic")}
            className={`eval-tab ${viewMode === "quadratic" ? "is-active" : ""}`}
          >
            Quadratic Estimator
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "baseline"}
            onClick={() => setViewMode("baseline")}
            className={`eval-tab ${viewMode === "baseline" ? "is-active" : ""}`}
          >
            Weighted-Centroid Baseline
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={viewMode === "delta"}
            onClick={() => setViewMode("delta")}
            className={`eval-tab ${viewMode === "delta" ? "is-active" : ""}`}
          >
            Paired Delta (Δ)
          </button>
        </div>

        <span className="eval-mode-status">
          VIEW: {viewMode.toUpperCase().replace("-", " ")}
        </span>
      </div>

      <div className="evaluation-table-scroll" role="region" aria-label="Trajectory metric table" tabIndex={0}>
        <table className="evaluation-table metric-table">
          <thead>
            {viewMode === "side-by-side" && (
              <tr>
                <th scope="col">Trajectory Metric</th>
                <th scope="col">Quadratic Mean ± SD</th>
                <th scope="col">Median</th>
                <th scope="col">Baseline Mean ± SD</th>
                <th scope="col">Median</th>
              </tr>
            )}

            {viewMode === "quadratic" && (
              <tr>
                <th scope="col">Trajectory Metric</th>
                <th scope="col">Quadratic Mean</th>
                <th scope="col">Sample SD</th>
                <th scope="col">Median</th>
                <th scope="col">Evaluated Samples</th>
              </tr>
            )}

            {viewMode === "baseline" && (
              <tr>
                <th scope="col">Trajectory Metric</th>
                <th scope="col">Baseline Mean</th>
                <th scope="col">Sample SD</th>
                <th scope="col">Median</th>
                <th scope="col">Evaluated Samples</th>
              </tr>
            )}

            {viewMode === "delta" && (
              <tr>
                <th scope="col">Trajectory Metric</th>
                <th scope="col">Quadratic Mean</th>
                <th scope="col">Baseline Mean</th>
                <th scope="col">Absolute Delta (Q - B)</th>
                <th scope="col">Relative Delta</th>
              </tr>
            )}
          </thead>
          <tbody>
            {metricRows.map((metric) => {
              const qm = quadratic.metrics[metric.key];
              const bm = baseline.metrics[metric.key];
              if (!qm || !bm) return null;

              if (viewMode === "side-by-side") {
                return (
                  <tr key={metric.key}>
                    <th scope="row">
                      {metric.label}
                      {metric.unit === "count" ? "" : ` (${metric.unit})`}
                    </th>
                    <td className="mono-num">
                      {formatVal(qm.mean, metric.unit)} ± {formatVal(qm.sample_stddev, metric.unit)}
                    </td>
                    <td className="mono-num">{formatVal(qm.median, metric.unit)}</td>
                    <td className="mono-num">
                      {formatVal(bm.mean, metric.unit)} ± {formatVal(bm.sample_stddev, metric.unit)}
                    </td>
                    <td className="mono-num">{formatVal(bm.median, metric.unit)}</td>
                  </tr>
                );
              }

              if (viewMode === "quadratic") {
                return (
                  <tr key={metric.key}>
                    <th scope="row">
                      {metric.label}
                      {metric.unit === "count" ? "" : ` (${metric.unit})`}
                    </th>
                    <td className="mono-num">{formatVal(qm.mean, metric.unit)}</td>
                    <td className="mono-num">{formatVal(qm.sample_stddev, metric.unit)}</td>
                    <td className="mono-num">{formatVal(qm.median, metric.unit)}</td>
                    <td className="mono-num">{qm.sample_count ?? quadratic.sample_count} runs</td>
                  </tr>
                );
              }

              if (viewMode === "baseline") {
                return (
                  <tr key={metric.key}>
                    <th scope="row">
                      {metric.label}
                      {metric.unit === "count" ? "" : ` (${metric.unit})`}
                    </th>
                    <td className="mono-num">{formatVal(bm.mean, metric.unit)}</td>
                    <td className="mono-num">{formatVal(bm.sample_stddev, metric.unit)}</td>
                    <td className="mono-num">{formatVal(bm.median, metric.unit)}</td>
                    <td className="mono-num">{bm.sample_count ?? baseline.sample_count} runs</td>
                  </tr>
                );
              }

              // Delta mode
              const delta = qm.mean - bm.mean;
              const pct = bm.mean !== 0 ? ((delta / Math.abs(bm.mean)) * 100).toFixed(1) : "0.0";
              const isPositive = delta > 0;
              return (
                <tr key={metric.key}>
                  <th scope="row">
                    {metric.label}
                    {metric.unit === "count" ? "" : ` (${metric.unit})`}
                  </th>
                  <td className="mono-num">{formatVal(qm.mean, metric.unit)}</td>
                  <td className="mono-num">{formatVal(bm.mean, metric.unit)}</td>
                  <td className={`mono-num ${isPositive ? "delta-pos" : "delta-neg"}`}>
                    {delta > 0 ? "+" : ""}
                    {formatVal(delta, metric.unit)}
                  </td>
                  <td className={`mono-num ${isPositive ? "delta-pos" : "delta-neg"}`}>
                    {delta > 0 ? "+" : ""}
                    {pct}%
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
