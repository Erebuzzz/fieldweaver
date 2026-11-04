"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";
import type { Frame, MissionSpec, PublicRegion, RunResult, Scenario } from "@/lib/types";
import { CameraPreset, CameraRig } from "./arena-3d/camera-rig";
import { createPlumeMaterial } from "./arena-3d/plume-material";
import { createRoverMesh, disposeRoverMesh, resetRoverTrail, updateRover } from "./arena-3d/robot-mesh";

export type Arena3DCanvasProps = {
  scenario: Scenario | null;
  mission: MissionSpec | null;
  result: RunResult | null;
  frame: Frame | null;
  frameIndex: number;
  cameraMode?: CameraPreset;
  onError?: (err: Error) => void;
};

function to3dX(x2d: number, arenaWidth: number): number {
  return x2d - arenaWidth / 2;
}

function to3dZ(y2d: number, arenaHeight: number): number {
  return -(y2d - arenaHeight / 2);
}

function collectActiveRegions(
  scenario: Scenario,
  result: RunResult | null,
  frame: Frame | null
): PublicRegion[] {
  const regionsMap = new Map<string, PublicRegion>();
  for (const region of scenario.initial_regions) {
    regionsMap.set(region.id, region);
  }
  for (const event of result?.world_events ?? []) {
    for (const region of event.regions) {
      regionsMap.set(region.id, region);
    }
  }

  const currentTime = frame?.t ?? 0;
  const activeIds = frame ? new Set(frame.active_region_ids) : null;

  return [...regionsMap.values()].filter((region) => {
    if (result && frame && activeIds) {
      return activeIds.has(region.id);
    }
    return region.active_from_s <= currentTime;
  });
}

function disposeObject3D(obj: THREE.Object3D | null | undefined): void {
  if (!obj) return;
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();

  obj.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (mesh.geometry) {
      geometries.add(mesh.geometry);
    }
    if (mesh.material) {
      if (Array.isArray(mesh.material)) {
        for (const mat of mesh.material) {
          if (mat) materials.add(mat);
        }
      } else {
        materials.add(mesh.material);
      }
    }
    const dirLight = child as THREE.DirectionalLight;
    if (dirLight.isDirectionalLight && dirLight.shadow?.map) {
      dirLight.shadow.map.dispose();
    }
  });

  geometries.forEach((geo) => geo.dispose());
  materials.forEach((mat) => mat.dispose());
}

export function Arena3DCanvas({
  scenario,
  mission,
  result,
  frame,
  frameIndex,
  cameraMode = "perspective",
  onError,
}: Arena3DCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  // References to keep Three.js scene instances across prop re-renders
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRigRef = useRef<CameraRig | null>(null);
  const plumeMatRef = useRef<THREE.ShaderMaterial | null>(null);
  const plumeGeoRef = useRef<THREE.PlaneGeometry | null>(null);
  const roversMapRef = useRef<Map<number, THREE.Group>>(new Map());
  const trailGroupRef = useRef<THREE.Group | null>(null);
  const regionsGroupRef = useRef<THREE.Group | null>(null);
  const formationGroupRef = useRef<THREE.Group | null>(null);
  const estimateGroupRef = useRef<THREE.Group | null>(null);
  const truthGroupRef = useRef<THREE.Group | null>(null);
  const animFrameIdRef = useRef<number | null>(null);

  // Initialize Three.js scene once on mount
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !scenario) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        powerPreference: "high-performance",
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.setSize(container.clientWidth || 720, container.clientHeight || 540);
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.setClearColor(0x0b0f17, 1);
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFShadowMap;
      container.appendChild(renderer.domElement);
      rendererRef.current = renderer;
    } catch (err) {
      if (onError && err instanceof Error) {
        onError(err);
      }
      return;
    }

    const handleContextLost = (event: Event) => {
      event.preventDefault();
      onError?.(new Error("WebGL context was lost"));
    };
    renderer.domElement.addEventListener("webglcontextlost", handleContextLost);

    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const width = scenario.arena.width_m;
    const height = scenario.arena.height_m;

    // Camera and CameraRig
    const camera = new THREE.PerspectiveCamera(
      45,
      (container.clientWidth || 720) / (container.clientHeight || 540),
      0.1,
      200
    );
    const cameraRig = new CameraRig(camera, renderer.domElement, width, height);
    cameraRigRef.current = cameraRig;

    // Ambient and Directional Lighting
    const ambientLight = new THREE.AmbientLight(0x1e293b, 1.4);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.0);
    keyLight.position.set(10, 20, 10);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x0ea5e9, 0.9);
    rimLight.position.set(-10, 12, -10);
    scene.add(rimLight);

    // Ground Grid
    const maxSpan = Math.max(width, height);
    const grid = new THREE.GridHelper(maxSpan, Math.floor(maxSpan), 0x334155, 0x1e293b);
    grid.position.y = 0.005;
    scene.add(grid);

    // Tactical Plume Shader Floor
    const plumeMat = createPlumeMaterial(width, height);
    plumeMatRef.current = plumeMat;
    const plumeGeo = new THREE.PlaneGeometry(width, height, 48, 48);
    plumeGeoRef.current = plumeGeo;
    plumeGeo.rotateX(-Math.PI / 2);
    const plumeMesh = new THREE.Mesh(plumeGeo, plumeMat);
    plumeMesh.position.y = 0.01;
    plumeMesh.receiveShadow = true;
    scene.add(plumeMesh);

    // Arena Perimeter Border
    const borderPoints = [
      new THREE.Vector3(-width / 2, 0.02, -height / 2),
      new THREE.Vector3(width / 2, 0.02, -height / 2),
      new THREE.Vector3(width / 2, 0.02, height / 2),
      new THREE.Vector3(-width / 2, 0.02, height / 2),
      new THREE.Vector3(-width / 2, 0.02, -height / 2),
    ];
    const borderGeo = new THREE.BufferGeometry().setFromPoints(borderPoints);
    const borderMat = new THREE.LineBasicMaterial({ color: 0x475569, linewidth: 2 });
    const borderLine = new THREE.Line(borderGeo, borderMat);
    scene.add(borderLine);

    // Dedicated groups for dynamic objects
    const trailGroup = new THREE.Group();
    scene.add(trailGroup);
    trailGroupRef.current = trailGroup;

    const regionsGroup = new THREE.Group();
    scene.add(regionsGroup);
    regionsGroupRef.current = regionsGroup;

    const formationGroup = new THREE.Group();
    scene.add(formationGroup);
    formationGroupRef.current = formationGroup;

    const estimateGroup = new THREE.Group();
    scene.add(estimateGroup);
    estimateGroupRef.current = estimateGroup;

    const truthGroup = new THREE.Group();
    scene.add(truthGroup);
    truthGroupRef.current = truthGroup;

    // ResizeObserver for responsive rendering
    const resizeObserver = new ResizeObserver(() => {
      if (!container || !rendererRef.current || !cameraRigRef.current) return;
      const w = container.clientWidth || 720;
      const h = container.clientHeight || 540;
      cameraRigRef.current.camera.aspect = w / h;
      cameraRigRef.current.camera.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    });
    resizeObserver.observe(container);

    // Animation Loop
    let lastTime = performance.now();
    const animate = (timeNow: number) => {
      const dt = (timeNow - lastTime) / 1000;
      lastTime = timeNow;

      if (plumeMatRef.current) {
        plumeMatRef.current.uniforms.u_time.value = timeNow * 0.001;
      }

      // Find Rover 0 state for chase camera tracking
      let leaderState: { x: number; z: number; heading: number } | null = null;
      const rover0 = roversMapRef.current.get(0);
      if (rover0) {
        leaderState = {
          x: rover0.position.x,
          z: rover0.position.z,
          heading: rover0.rotation.y,
        };
      }

      if (cameraRigRef.current) {
        cameraRigRef.current.update(dt, leaderState);
      }

      if (rendererRef.current && sceneRef.current && cameraRigRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRigRef.current.camera);
      }

      animFrameIdRef.current = requestAnimationFrame(animate);
    };
    animFrameIdRef.current = requestAnimationFrame(animate);

    const roversMap = roversMapRef.current;

    return () => {
      resizeObserver.disconnect();
      if (animFrameIdRef.current !== null) {
        cancelAnimationFrame(animFrameIdRef.current);
        animFrameIdRef.current = null;
      }
      if (cameraRigRef.current) {
        cameraRigRef.current.dispose();
        cameraRigRef.current = null;
      }
      if (plumeMatRef.current) {
        plumeMatRef.current.dispose();
        plumeMatRef.current = null;
      }
      if (plumeGeoRef.current) {
        plumeGeoRef.current.dispose();
        plumeGeoRef.current = null;
      }
      roversMap.forEach((roverGroup) => {
        disposeRoverMesh(roverGroup);
      });
      roversMap.clear();

      if (sceneRef.current) {
        disposeObject3D(sceneRef.current);
        sceneRef.current.clear();
        sceneRef.current = null;
      }

      trailGroupRef.current = null;
      regionsGroupRef.current = null;
      formationGroupRef.current = null;
      estimateGroupRef.current = null;
      truthGroupRef.current = null;

      if (rendererRef.current) {
        const renderer = rendererRef.current;
        renderer.domElement.removeEventListener("webglcontextlost", handleContextLost);
        renderer.dispose();
        if (typeof renderer.forceContextLoss === "function") {
          renderer.forceContextLoss();
        }
        if (renderer.domElement.parentElement) {
          renderer.domElement.parentElement.removeChild(renderer.domElement);
        }
        rendererRef.current = null;
      }
    };
  }, [scenario, onError]);

  // Handle camera mode change
  useEffect(() => {
    if (cameraRigRef.current) {
      cameraRigRef.current.setMode(cameraMode);
    }
  }, [cameraMode]);

  // Reset trails when scrubbing backward or resetting to frame 0
  useEffect(() => {
    if (frameIndex === 0) {
      roversMapRef.current.forEach((group) => {
        resetRoverTrail(group);
      });
    }
  }, [frameIndex]);

  // Update dynamic elements on each frame / result change
  useEffect(() => {
    if (!scenario || !sceneRef.current) return;

    const width = scenario.arena.width_m;
    const height = scenario.arena.height_m;

    // 1. Update Regions (Obstacles & Restricted Zones)
    const regionsGroup = regionsGroupRef.current;
    if (regionsGroup) {
      // Clear previous region meshes
      while (regionsGroup.children.length > 0) {
        const child = regionsGroup.children[0];
        disposeObject3D(child);
        regionsGroup.remove(child);
      }

      const activeRegions = collectActiveRegions(scenario, result, frame);
      for (const region of activeRegions) {
        const isRestricted = region.kind === "restricted";

        if (region.shape === "rect") {
          const xMin = region.x_min ?? 0;
          const xMax = region.x_max ?? 0;
          const yMin = region.y_min ?? 0;
          const yMax = region.y_max ?? 0;

          const rw = xMax - xMin;
          const rd = yMax - yMin;
          const cx3d = to3dX((xMin + xMax) / 2, width);
          const cz3d = to3dZ((yMin + yMax) / 2, height);

          if (isRestricted) {
            // Flat glowing warning floor
            const restGeo = new THREE.PlaneGeometry(rw, rd);
            restGeo.rotateX(-Math.PI / 2);
            const restMat = new THREE.MeshBasicMaterial({
              color: 0xef4444,
              transparent: true,
              opacity: 0.28,
              depthWrite: false,
            });
            const restMesh = new THREE.Mesh(restGeo, restMat);
            restMesh.position.set(cx3d, 0.02, cz3d);
            regionsGroup.add(restMesh);

            // Red perimeter border
            const bPoints = [
              new THREE.Vector3(-rw / 2, 0.025, -rd / 2),
              new THREE.Vector3(rw / 2, 0.025, -rd / 2),
              new THREE.Vector3(rw / 2, 0.025, rd / 2),
              new THREE.Vector3(-rw / 2, 0.025, rd / 2),
              new THREE.Vector3(-rw / 2, 0.025, -rd / 2),
            ];
            const bGeo = new THREE.BufferGeometry().setFromPoints(bPoints);
            const bMat = new THREE.LineBasicMaterial({ color: 0xef4444, linewidth: 2 });
            const bLine = new THREE.Line(bGeo, bMat);
            bLine.position.set(cx3d, 0, cz3d);
            regionsGroup.add(bLine);
          } else {
            // 3D Extruded Obstacle Box
            const boxHeight = 0.8;
            const boxGeo = new THREE.BoxGeometry(rw, boxHeight, rd);
            const boxMat = new THREE.MeshStandardMaterial({
              color: 0x334155,
              roughness: 0.35,
              metalness: 0.65,
            });
            const boxMesh = new THREE.Mesh(boxGeo, boxMat);
            boxMesh.position.set(cx3d, boxHeight / 2, cz3d);
            boxMesh.castShadow = true;
            boxMesh.receiveShadow = true;
            regionsGroup.add(boxMesh);
          }
        } else if (region.shape === "circle") {
          const cx = region.cx ?? 0;
          const cy = region.cy ?? 0;
          const radius = region.radius ?? 0.5;
          const cx3d = to3dX(cx, width);
          const cz3d = to3dZ(cy, height);

          if (isRestricted) {
            const restGeo = new THREE.CircleGeometry(radius, 32);
            restGeo.rotateX(-Math.PI / 2);
            const restMat = new THREE.MeshBasicMaterial({
              color: 0xef4444,
              transparent: true,
              opacity: 0.28,
              depthWrite: false,
            });
            const restMesh = new THREE.Mesh(restGeo, restMat);
            restMesh.position.set(cx3d, 0.02, cz3d);
            regionsGroup.add(restMesh);
          } else {
            const cylHeight = 0.8;
            const cylGeo = new THREE.CylinderGeometry(radius, radius, cylHeight, 24);
            const cylMat = new THREE.MeshStandardMaterial({
              color: 0x334155,
              roughness: 0.35,
              metalness: 0.65,
            });
            const cylMesh = new THREE.Mesh(cylGeo, cylMat);
            cylMesh.position.set(cx3d, cylHeight / 2, cz3d);
            cylMesh.castShadow = true;
            cylMesh.receiveShadow = true;
            regionsGroup.add(cylMesh);
          }
        }
      }
    }

    // 2. Update Rovers
    const scene = sceneRef.current;
    const trailGroup = trailGroupRef.current;
    const robots = frame?.robots ?? [];

    for (const robot of robots) {
      let roverMesh = roversMapRef.current.get(robot.id);
      if (!roverMesh) {
        roverMesh = createRoverMesh(robot.id);
        scene.add(roverMesh);
        roversMapRef.current.set(robot.id, roverMesh);

        if (trailGroup) {
          const userData = roverMesh.userData as { trailLine: THREE.Line };
          if (userData?.trailLine) {
            trailGroup.add(userData.trailLine);
          }
        }
      }

      const r3dX = to3dX(robot.x, width);
      const r3dZ = to3dZ(robot.y, height);
      updateRover(roverMesh, r3dX, r3dZ, robot.heading, robot.measurement, performance.now() * 0.001);
    }

    // 3. Update Formation Ring and Slot Target Pads
    const formationGroup = formationGroupRef.current;
    const estimate = frame?.estimate;
    const ringRadius = mission?.formation.radius;
    const ringCount = mission?.robot_count ?? scenario.default_robot_count;

    if (formationGroup) {
      while (formationGroup.children.length > 0) {
        const child = formationGroup.children[0];
        disposeObject3D(child);
        formationGroup.remove(child);
      }

      if (estimate?.valid && ringRadius) {
        const est3dX = to3dX(estimate.x, width);
        const est3dZ = to3dZ(estimate.y, height);

        // Holographic ring circle
        const ringSegments = 64;
        const ringPoints: THREE.Vector3[] = [];
        for (let i = 0; i <= ringSegments; i++) {
          const theta = (i / ringSegments) * Math.PI * 2;
          ringPoints.push(
            new THREE.Vector3(
              est3dX + ringRadius * Math.cos(theta),
              0.035,
              est3dZ - ringRadius * Math.sin(theta)
            )
          );
        }
        const ringGeo = new THREE.BufferGeometry().setFromPoints(ringPoints);
        const ringMat = new THREE.LineBasicMaterial({
          color: 0x0ea5e9,
          transparent: true,
          opacity: 0.65,
          linewidth: 2,
        });
        const ringLine = new THREE.Line(ringGeo, ringMat);
        formationGroup.add(ringLine);

        // Individual slot pads
        for (let index = 0; index < ringCount; index++) {
          const angle = (Math.PI * 2 * index) / ringCount;
          const slotX = est3dX + ringRadius * Math.cos(angle);
          const slotZ = est3dZ - ringRadius * Math.sin(angle);

          const padGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.02, 16);
          const padMat = new THREE.MeshStandardMaterial({
            color: 0x0284c7,
            emissive: 0x0ea5e9,
            emissiveIntensity: 0.8,
            roughness: 0.3,
          });
          const pad = new THREE.Mesh(padGeo, padMat);
          pad.position.set(slotX, 0.04, slotZ);
          formationGroup.add(pad);
        }
      }
    }

    // 4. Update Estimate Reticle Pillar
    const estimateGroup = estimateGroupRef.current;
    if (estimateGroup) {
      while (estimateGroup.children.length > 0) {
        const child = estimateGroup.children[0];
        disposeObject3D(child);
        estimateGroup.remove(child);
      }

      if (estimate?.valid) {
        const est3dX = to3dX(estimate.x, width);
        const est3dZ = to3dZ(estimate.y, height);

        // Vertical cyan beacon beam
        const beamGeo = new THREE.CylinderGeometry(0.012, 0.012, 2.4, 8);
        const beamMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.5,
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        beam.position.set(est3dX, 1.2, est3dZ);
        estimateGroup.add(beam);

        // Crosshair disc
        const crosshairGeo = new THREE.RingGeometry(0.18, 0.22, 24);
        crosshairGeo.rotateX(-Math.PI / 2);
        const crosshairMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          side: THREE.DoubleSide,
        });
        const crosshair = new THREE.Mesh(crosshairGeo, crosshairMat);
        crosshair.position.set(est3dX, 0.05, est3dZ);
        estimateGroup.add(crosshair);
      }
    }

    // 5. Update Ground Truth Beacon (Quarantined until after run evaluation)
    const truthGroup = truthGroupRef.current;
    const revealedTruth =
      result?.evaluation.ground_truth.revealed === "after_run_only"
        ? result.evaluation.ground_truth
        : null;

    if (truthGroup) {
      while (truthGroup.children.length > 0) {
        const child = truthGroup.children[0];
        disposeObject3D(child);
        truthGroup.remove(child);
      }

      if (revealedTruth) {
        const truth3dX = to3dX(revealedTruth.x, width);
        const truth3dZ = to3dZ(revealedTruth.y, height);

        // Emerald ground beacon pillar
        const truthBeamGeo = new THREE.CylinderGeometry(0.018, 0.018, 3.2, 8);
        const truthBeamMat = new THREE.MeshBasicMaterial({
          color: 0x10b981,
          transparent: true,
          opacity: 0.8,
        });
        const truthBeam = new THREE.Mesh(truthBeamGeo, truthBeamMat);
        truthBeam.position.set(truth3dX, 1.6, truth3dZ);
        truthGroup.add(truthBeam);

        // Dual golden/emerald target rings
        const ring1Geo = new THREE.RingGeometry(0.3, 0.35, 32);
        ring1Geo.rotateX(-Math.PI / 2);
        const ring1Mat = new THREE.MeshBasicMaterial({ color: 0x10b981, side: THREE.DoubleSide });
        const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
        ring1.position.set(truth3dX, 0.05, truth3dZ);
        truthGroup.add(ring1);

        const ring2Geo = new THREE.RingGeometry(0.55, 0.6, 32);
        ring2Geo.rotateX(-Math.PI / 2);
        const ring2Mat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, side: THREE.DoubleSide });
        const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
        ring2.position.set(truth3dX, 0.05, truth3dZ);
        truthGroup.add(ring2);
      }
    }

    // 6. Feed uniforms to Plume Shader
    const plumeMat = plumeMatRef.current;
    if (plumeMat) {
      if (estimate?.valid) {
        plumeMat.uniforms.u_estimate_valid.value = 1.0;
        plumeMat.uniforms.u_estimate_pos.value.set(
          to3dX(estimate.x, width),
          to3dZ(estimate.y, height)
        );
        plumeMat.uniforms.u_estimate_confidence.value = estimate.confidence ?? 0.5;
      } else {
        plumeMat.uniforms.u_estimate_valid.value = 0.0;
      }

      plumeMat.uniforms.u_robot_count.value = Math.min(robots.length, 8);
      for (let i = 0; i < 8; i++) {
        if (i < robots.length) {
          const r = robots[i];
          plumeMat.uniforms.u_robot_positions.value[i].set(
            to3dX(r.x, width),
            to3dZ(r.y, height)
          );
          plumeMat.uniforms.u_robot_measurements.value[i] = r.measurement;
        } else {
          plumeMat.uniforms.u_robot_positions.value[i].set(0, 0);
          plumeMat.uniforms.u_robot_measurements.value[i] = 0;
        }
      }

      if (revealedTruth) {
        plumeMat.uniforms.u_revealed.value = 1.0;
        plumeMat.uniforms.u_truth_pos.value.set(
          to3dX(revealedTruth.x, width),
          to3dZ(revealedTruth.y, height)
        );
      } else {
        plumeMat.uniforms.u_revealed.value = 0.0;
      }
    }
  }, [scenario, mission, result, frame]);

  if (!scenario) {
    return <div className="arena-empty">Connect to the simulation API to load the arenas.</div>;
  }

  return (
    <div
      ref={containerRef}
      className="arena-3d-wrapper"
      role="region"
      aria-label={`${scenario.name} 3D Tactical Digital Twin Viewport`}
      style={{
        width: "100%",
        height: "100%",
        minHeight: "540px",
        position: "relative",
        overflow: "hidden",
        backgroundColor: "#0b0f17",
      }}
    />
  );
}
