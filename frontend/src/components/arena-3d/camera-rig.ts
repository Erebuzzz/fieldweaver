import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

export type CameraPreset = "perspective" | "topdown" | "follow";

export class CameraRig {
  public camera: THREE.PerspectiveCamera;
  public controls: OrbitControls;
  public mode: CameraPreset = "perspective";

  private arenaWidth: number;
  private arenaHeight: number;
  private targetPosition: THREE.Vector3;
  private targetLookAt: THREE.Vector3;
  private tempChasePos = new THREE.Vector3();
  private tempLookAtPos = new THREE.Vector3();
  private isTransitioning = false;

  constructor(
    camera: THREE.PerspectiveCamera,
    domElement: HTMLElement,
    arenaWidth: number,
    arenaHeight: number
  ) {
    this.camera = camera;
    this.arenaWidth = Math.max(arenaWidth, 6);
    this.arenaHeight = Math.max(arenaHeight, 6);

    this.controls = new OrbitControls(camera, domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.05;
    this.controls.minDistance = 2.0;
    this.controls.maxDistance = Math.max(this.arenaWidth, this.arenaHeight) * 3.5;

    const maxSpan = Math.max(this.arenaWidth, this.arenaHeight);
    this.targetPosition = new THREE.Vector3(0, maxSpan * 1.15, maxSpan * 1.1);
    this.targetLookAt = new THREE.Vector3(0, 0, 0);

    this.camera.position.copy(this.targetPosition);
    this.controls.target.copy(this.targetLookAt);
    this.controls.update();
  }

  public setMode(newMode: CameraPreset): void {
    this.mode = newMode;
    this.isTransitioning = true;
    const maxSpan = Math.max(this.arenaWidth, this.arenaHeight);

    if (newMode === "perspective") {
      this.camera.up.set(0, 1, 0);
      this.controls.enabled = true;
      this.targetPosition.set(0, maxSpan * 1.15, maxSpan * 1.1);
      this.targetLookAt.set(0, 0, 0);
    } else if (newMode === "topdown") {
      this.camera.up.set(0, 0, -1);
      this.controls.enabled = false;
      this.targetPosition.set(0, maxSpan * 1.6, 0.001);
      this.targetLookAt.set(0, 0, 0);
    } else if (newMode === "follow") {
      this.camera.up.set(0, 1, 0);
      this.controls.enabled = false;
    }
  }

  public update(
    _dt: number,
    leaderState?: { x: number; z: number; heading: number } | null
  ): void {
    if (this.mode === "follow" && leaderState) {
      const chaseDist = 3.2;
      const chaseHeight = 2.0;
      const desiredX = leaderState.x - chaseDist * Math.cos(leaderState.heading);
      const desiredZ = leaderState.z + chaseDist * Math.sin(leaderState.heading);
      const desiredY = chaseHeight;

      const lookAhead = 1.2;
      const targetX = leaderState.x + lookAhead * Math.cos(leaderState.heading);
      const targetZ = leaderState.z - lookAhead * Math.sin(leaderState.heading);

      this.tempChasePos.set(desiredX, desiredY, desiredZ);
      this.tempLookAtPos.set(targetX, 0.4, targetZ);
      this.camera.position.lerp(this.tempChasePos, 0.1);
      this.controls.target.lerp(this.tempLookAtPos, 0.1);
      this.camera.lookAt(this.controls.target);
      return;
    }

    if (this.isTransitioning) {
      this.camera.position.lerp(this.targetPosition, 0.08);
      this.controls.target.lerp(this.targetLookAt, 0.08);

      if (
        this.camera.position.distanceTo(this.targetPosition) < 0.05 &&
        this.controls.target.distanceTo(this.targetLookAt) < 0.05
      ) {
        this.camera.position.copy(this.targetPosition);
        this.controls.target.copy(this.targetLookAt);
        this.isTransitioning = false;
      }
    }

    if (this.controls.enabled) {
      this.controls.update();
    } else {
      this.camera.lookAt(this.controls.target);
    }
  }

  public dispose(): void {
    this.controls.dispose();
  }
}
