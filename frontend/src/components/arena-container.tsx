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

  useEffect(() => {
    const updateFullscreen = () => setIsFullscreen(document.fullscreenElement === containerRef.current);
    document.addEventListener("fullscreenchange", updateFullscreen);
    return () => document.removeEventListener("fullscreenchange", updateFullscreen);
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
    <div ref={containerRef} className={`arena-container ${className}`}>
      <div className="arena-toolbar">
        <div className="arena-toolbar-group" aria-label="Arena view">
          <div className="arena-segment" role="group" aria-label="Display mode">
            <button type="button" disabled={Boolean(webglError)} aria-pressed={viewMode === "3d"} onClick={() => setViewMode("3d")}>3D view</button>
            <button type="button" aria-pressed={viewMode === "2d"} onClick={() => setViewMode("2d")}>2D view</button>
          </div>
          {viewMode === "3d" && !webglError && (
            <div className="arena-segment camera-segment" role="group" aria-label="Camera angle">
              <button type="button" aria-pressed={cameraMode === "perspective"} onClick={() => setCameraMode("perspective")}>Perspective</button>
              <button type="button" aria-pressed={cameraMode === "topdown"} onClick={() => setCameraMode("topdown")}>Top down</button>
              <button type="button" aria-pressed={cameraMode === "follow"} onClick={() => setCameraMode("follow")}>Follow</button>
            </div>
          )}
        </div>
        <div className="arena-toolbar-group arena-actions">
          <button type="button" className="arena-action" onClick={handleToggleSound} aria-pressed={!muted} aria-label={muted ? "Unmute simulation sound" : "Mute simulation sound"}>
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z M16 9c1.5 1.5 1.5 4.5 0 6M19 6c3 3 3 9 0 12" /></svg>
            {muted ? "Sound off" : "Sound on"}
          </button>
          <button type="button" className="arena-action" onClick={handleToggleFullscreen} aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}>
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" /></svg>
            {isFullscreen ? "Exit fullscreen" : "Expand"}
          </button>
        </div>
      </div>
      {webglError && (
        <div role="alert" className="arena-notice">
          3D is unavailable. Showing the 2D arena instead.
        </div>
      )}
      <div className="arena-viewport">
        {viewMode === "3d" && !webglError ? (
          <Arena3DCanvas scenario={scenario} mission={mission} result={result} frame={frame} frameIndex={frameIndex} cameraMode={cameraMode} onError={handleWebGLError} />
        ) : (
          <ArenaCanvas scenario={scenario} mission={mission} result={result} frame={frame} frameIndex={frameIndex} />
        )}
      </div>
    </div>
  );
}
