"use client";

import React, { useCallback, useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import type { Frame, MissionSpec, RunResult, Scenario } from "@/lib/types";
import { CameraPreset } from "./arena-3d/camera-rig";
import { ArenaCanvas } from "./arena-canvas";
import {
  isMuted,
  playPlumeDetectionPing,
  playSafetyInterventionClick,
  toggleMute,
} from "@/lib/audio";

const Arena3DCanvas = dynamic(
  () => import("./arena-3d-canvas").then((mod) => mod.Arena3DCanvas),
  {
    ssr: false,
    loading: () => (
      <div
        className="arena-3d-loading"
        style={{
          minHeight: "540px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#0b0f17",
          color: "#94a3b8",
          fontFamily: "var(--font-mono, monospace)",
          fontSize: "0.82rem",
          letterSpacing: "0.05em",
        }}
      >
        INITIALIZING 3D TACTICAL DIGITAL TWIN...
      </div>
    ),
  }
);

export type ArenaContainerProps = {
  scenario: Scenario | null;
  mission: MissionSpec | null;
  result: RunResult | null;
  frame: Frame | null;
  frameIndex: number;
  className?: string;
};

export function ArenaContainer({
  scenario,
  mission,
  result,
  frame,
  frameIndex,
  className = "",
}: ArenaContainerProps) {
  const [viewMode, setViewMode] = useState<"3d" | "2d">("3d");
  const [cameraMode, setCameraMode] = useState<CameraPreset>("perspective");
  const [muted, setMutedState] = useState(true);
  const [webglError, setWebglError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const prevStepRef = useRef<number>(-1);
  const prevMinMeasurementRef = useRef<number | null>(null);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => setMutedState(isMuted()), 0);
    return () => window.clearTimeout(timeoutId);
  }, []);

  // Handle acoustic feedback on frame advancement
  useEffect(() => {
    if (!frame || frame.step === prevStepRef.current) {
      return;
    }
    const currentStep = frame.step;
    prevStepRef.current = currentStep;

    // Check if a safety intervention occurred at this step
    if (result?.safety.interventions) {
      const interventionAtStep = result.safety.interventions.some(
        (item) => item.step === currentStep
      );
      if (interventionAtStep) {
        playSafetyInterventionClick();
      }
    }

    // Check plume sensor measurements for acoustic ping
    if (frame.robots.length > 0) {
      const measurements = frame.robots.map((r) => r.measurement);
      const minMeas = Math.min(...measurements);
      if (prevMinMeasurementRef.current !== null) {
        // Lower scalar measurement indicates proximity to source
        if (minMeas < prevMinMeasurementRef.current - 0.05) {
          const intensity = Math.min(1, Math.max(0, 1.0 - minMeas / 10.0));
          playPlumeDetectionPing(intensity);
        }
      }
      prevMinMeasurementRef.current = minMeas;
    }
  }, [frame, result]);

  // Handle WebGL creation failure with fail-safe fallback
  const handleWebGLError = useCallback((error: Error) => {
    setWebglError(error.message || "WebGL context initialization failed");
    setViewMode("2d");
  }, []);

  const handleToggleSound = () => {
    const nextMuted = toggleMute();
    setMutedState(nextMuted);
  };

  const handleToggleFullscreen = () => {
    const el = containerRef.current;
    if (!el) return;
    if (!document.fullscreenElement) {
      el.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  };

  return (
    <div
      ref={containerRef}
      className={`arena-container ${className}`}
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        backgroundColor: "#0b0f17",
        borderRadius: "8px",
        overflow: "hidden",
        border: "1px solid var(--border, #1e293b)",
      }}
    >
      {/* Tactical Controls Bar */}
      <div
        className="arena-controls-bar"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
          padding: "8px 12px",
          backgroundColor: "#0f172a",
          borderBottom: "1px solid #1e293b",
          fontSize: "0.78rem",
          fontFamily: "var(--font-mono, monospace)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          {/* 3D vs 2D Mode Switcher */}
          <div
            style={{
              display: "inline-flex",
              backgroundColor: "#020617",
              borderRadius: "4px",
              padding: "2px",
              border: "1px solid #334155",
            }}
          >
            <button
              type="button"
              disabled={Boolean(webglError)}
              onClick={() => setViewMode("3d")}
              style={{
                background: viewMode === "3d" ? "#0ea5e9" : "transparent",
                color: viewMode === "3d" ? "#0f172a" : "#94a3b8",
                fontWeight: viewMode === "3d" ? 600 : 400,
                border: "none",
                borderRadius: "3px",
                padding: "4px 8px",
                cursor: webglError ? "not-allowed" : "pointer",
                opacity: webglError ? 0.4 : 1,
              }}
            >
              3D Tactical Twin
            </button>
            <button
              type="button"
              onClick={() => setViewMode("2d")}
              style={{
                background: viewMode === "2d" ? "#0ea5e9" : "transparent",
                color: viewMode === "2d" ? "#0f172a" : "#94a3b8",
                fontWeight: viewMode === "2d" ? 600 : 400,
                border: "none",
                borderRadius: "3px",
                padding: "4px 8px",
                cursor: "pointer",
              }}
            >
              2D Fallback
            </button>
          </div>

          {/* Camera Controls (available in 3D mode) */}
          {viewMode === "3d" && !webglError && (
            <div
              style={{
                display: "inline-flex",
                backgroundColor: "#020617",
                borderRadius: "4px",
                padding: "2px",
                border: "1px solid #334155",
                marginLeft: "6px",
              }}
            >
              <button
                type="button"
                onClick={() => setCameraMode("perspective")}
                style={{
                  background: cameraMode === "perspective" ? "#1e293b" : "transparent",
                  color: cameraMode === "perspective" ? "#38bdf8" : "#64748b",
                  border: "none",
                  borderRadius: "3px",
                  padding: "4px 8px",
                  cursor: "pointer",
                }}
              >
                Perspective
              </button>
              <button
                type="button"
                onClick={() => setCameraMode("topdown")}
                style={{
                  background: cameraMode === "topdown" ? "#1e293b" : "transparent",
                  color: cameraMode === "topdown" ? "#38bdf8" : "#64748b",
                  border: "none",
                  borderRadius: "3px",
                  padding: "4px 8px",
                  cursor: "pointer",
                }}
              >
                Top-Down
              </button>
              <button
                type="button"
                onClick={() => setCameraMode("follow")}
                style={{
                  background: cameraMode === "follow" ? "#1e293b" : "transparent",
                  color: cameraMode === "follow" ? "#38bdf8" : "#64748b",
                  border: "none",
                  borderRadius: "3px",
                  padding: "4px 8px",
                  cursor: "pointer",
                }}
              >
                Follow Leader
              </button>
            </div>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* Tactical Audio Toggle */}
          <button
            type="button"
            onClick={handleToggleSound}
            aria-label={muted ? "Unmute tactical sound" : "Mute tactical sound"}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              background: muted ? "#1e293b" : "#0284c7",
              color: muted ? "#94a3b8" : "#f0fdf4",
              border: "1px solid #334155",
              borderRadius: "4px",
              padding: "4px 8px",
              cursor: "pointer",
            }}
          >
            <span style={{ fontSize: "0.9rem" }}>{muted ? "🔇" : "🔊"}</span>
            <span>{muted ? "Muted" : "Acoustic FX"}</span>
          </button>

          {/* Fullscreen Toggle */}
          <button
            type="button"
            onClick={handleToggleFullscreen}
            aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            style={{
              background: "#1e293b",
              color: "#94a3b8",
              border: "1px solid #334155",
              borderRadius: "4px",
              padding: "4px 8px",
              cursor: "pointer",
            }}
          >
            {isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
          </button>
        </div>
      </div>

      {/* WebGL Fail-Safe Error Notice */}
      {webglError && (
        <div
          role="alert"
          style={{
            padding: "8px 12px",
            backgroundColor: "#451a03",
            color: "#fed7aa",
            fontSize: "0.78rem",
            borderBottom: "1px solid #78350f",
          }}
        >
          <strong>Notice:</strong> Hardware WebGL initialization was not available. Active mode
          switched to 2D tactical fallback canvas.
        </div>
      )}

      {/* Main Viewport Content */}
      <div style={{ position: "relative", width: "100%", height: "100%", flex: 1 }}>
        {viewMode === "3d" && !webglError ? (
          <Arena3DCanvas
            scenario={scenario}
            mission={mission}
            result={result}
            frame={frame}
            frameIndex={frameIndex}
            cameraMode={cameraMode}
            onError={handleWebGLError}
          />
        ) : (
          <ArenaCanvas
            scenario={scenario}
            mission={mission}
            result={result}
            frame={frame}
            frameIndex={frameIndex}
          />
        )}
      </div>
    </div>
  );
}
