import * as THREE from "three";

const TEAM_COLORS = [
  0x0ea5e9, // Rover 0: Cyan
  0xf59e0b, // Rover 1: Amber
  0x10b981, // Rover 2: Emerald
  0xa855f7, // Rover 3: Purple
  0xec4899, // Rover 4: Pink
  0x38bdf8, // Rover 5: Sky
  0xf97316, // Rover 6: Orange
  0x6366f1, // Rover 7: Indigo
];

export type RoverUserData = {
  robotId: number;
  wheels: THREE.Mesh[];
  sensorLed: THREE.Mesh;
  trailLine: THREE.Line;
  trailHistory: THREE.Vector3[];
  maxTrailLength: number;
};

export function createRoverMesh(robotId: number): THREE.Group {
  const group = new THREE.Group();
  group.name = `rover-${robotId}`;

  const accentColor = TEAM_COLORS[robotId % TEAM_COLORS.length];

  // 1. Main Chassis (length 0.44m along X, height 0.12m along Y, width 0.28m along Z)
  const chassisGeo = new THREE.BoxGeometry(0.44, 0.12, 0.28);
  const chassisMat = new THREE.MeshStandardMaterial({
    color: 0x1e293b,
    roughness: 0.4,
    metalness: 0.7,
  });
  const chassis = new THREE.Mesh(chassisGeo, chassisMat);
  chassis.position.set(0, 0.14, 0);
  chassis.castShadow = true;
  chassis.receiveShadow = true;
  group.add(chassis);

  // 2. Cockpit Canopy (chamfered visor toward forward bumper +X)
  const canopyGeo = new THREE.BoxGeometry(0.20, 0.08, 0.20);
  const canopyMat = new THREE.MeshStandardMaterial({
    color: 0x0284c7,
    roughness: 0.15,
    metalness: 0.85,
    transparent: true,
    opacity: 0.85,
  });
  const canopy = new THREE.Mesh(canopyGeo, canopyMat);
  canopy.position.set(0.06, 0.22, 0);
  group.add(canopy);

  // 3. Team Color Identification Stripe
  const stripeGeo = new THREE.BoxGeometry(0.38, 0.015, 0.07);
  const stripeMat = new THREE.MeshStandardMaterial({
    color: accentColor,
    emissive: accentColor,
    emissiveIntensity: 0.5,
    roughness: 0.3,
  });
  const stripe = new THREE.Mesh(stripeGeo, stripeMat);
  stripe.position.set(-0.02, 0.205, 0);
  group.add(stripe);

  // 4. Four Rocker Wheels
  const wheelGeo = new THREE.CylinderGeometry(0.07, 0.07, 0.06, 16);
  wheelGeo.rotateX(Math.PI / 2); // align cylinder axle along Z
  const wheelMat = new THREE.MeshStandardMaterial({
    color: 0x0f172a,
    roughness: 0.7,
    metalness: 0.3,
  });

  const wheels: THREE.Mesh[] = [];
  const wheelOffsets = [
    { x: 0.14, y: 0.07, z: 0.16 },  // Front Left
    { x: 0.14, y: 0.07, z: -0.16 }, // Front Right
    { x: -0.14, y: 0.07, z: 0.16 }, // Rear Left
    { x: -0.14, y: 0.07, z: -0.16 },// Rear Right
  ];

  for (const offset of wheelOffsets) {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    wheel.position.set(offset.x, offset.y, offset.z);
    wheel.castShadow = true;
    group.add(wheel);
    wheels.push(wheel);
  }

  // 5. Tactical Sensor Mast & Plume LED Diode
  const mastGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.16, 8);
  const mastMat = new THREE.MeshStandardMaterial({
    color: 0x475569,
    roughness: 0.5,
    metalness: 0.6,
  });
  const mast = new THREE.Mesh(mastGeo, mastMat);
  mast.position.set(-0.16, 0.26, 0);
  group.add(mast);

  const ledGeo = new THREE.SphereGeometry(0.032, 12, 12);
  const ledMat = new THREE.MeshStandardMaterial({
    color: accentColor,
    emissive: accentColor,
    emissiveIntensity: 1.2,
    roughness: 0.2,
  });
  const sensorLed = new THREE.Mesh(ledGeo, ledMat);
  sensorLed.position.set(-0.16, 0.35, 0);
  group.add(sensorLed);

  // 6. Forward Headlight Beams (+X)
  const headlightBeamGeo = new THREE.ConeGeometry(0.4, 1.6, 16, 1, true);
  headlightBeamGeo.rotateZ(-Math.PI / 2); // points along +X
  headlightBeamGeo.translate(0.8, 0, 0); // starts from front bumper
  const headlightBeamMat = new THREE.MeshBasicMaterial({
    color: 0x93c5fd,
    transparent: true,
    opacity: 0.08,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const headlightBeam = new THREE.Mesh(headlightBeamGeo, headlightBeamMat);
  headlightBeam.position.set(0.22, 0.14, 0);
  group.add(headlightBeam);

  // 7. Dynamic Trail Ribbon Line
  const maxTrailLength = 50;
  const trailPositions = new Float32Array(maxTrailLength * 3);
  const trailGeo = new THREE.BufferGeometry();
  trailGeo.setAttribute("position", new THREE.BufferAttribute(trailPositions, 3));

  const trailMat = new THREE.LineBasicMaterial({
    color: accentColor,
    transparent: true,
    opacity: 0.45,
    linewidth: 1,
  });
  const trailLine = new THREE.Line(trailGeo, trailMat);
  trailLine.frustumCulled = false;

  const userData: RoverUserData = {
    robotId,
    wheels,
    sensorLed,
    trailLine,
    trailHistory: [],
    maxTrailLength,
  };
  group.userData = userData;

  return group;
}

export function updateRover(
  group: THREE.Group,
  x3d: number,
  z3d: number,
  heading: number,
  measurement: number,
  time: number
): void {
  // Update translation and orientation
  group.position.x = x3d;
  group.position.z = z3d;
  group.position.y = 0;
  group.rotation.y = heading;

  const data = group.userData as RoverUserData;
  if (!data) return;

  // Animate sensor LED pulsation based on sensor activity
  const pulseFreq = 3.0 + Math.min(measurement * 0.5, 8.0);
  const pulse = Math.sin(time * pulseFreq) * 0.5 + 0.5;
  const ledMat = data.sensorLed.material as THREE.MeshStandardMaterial;
  if (ledMat) {
    ledMat.emissiveIntensity = 0.6 + pulse * 1.8;
  }

  // Roll wheels forward
  for (const wheel of data.wheels) {
    wheel.rotation.z += 0.08;
  }

  // Record historical ground trail position
  const currentPos = new THREE.Vector3(x3d, 0.02, z3d);
  if (
    data.trailHistory.length === 0 ||
    data.trailHistory[data.trailHistory.length - 1].distanceTo(currentPos) > 0.05
  ) {
    data.trailHistory.push(currentPos);
    if (data.trailHistory.length > data.maxTrailLength) {
      data.trailHistory.shift();
    }

    // Refresh trail buffer geometry
    const geo = data.trailLine.geometry as THREE.BufferGeometry;
    const positions = geo.attributes.position.array as Float32Array;
    for (let i = 0; i < data.maxTrailLength; i++) {
      const idx = i * 3;
      if (i < data.trailHistory.length) {
        const pt = data.trailHistory[i];
        positions[idx] = pt.x;
        positions[idx + 1] = pt.y;
        positions[idx + 2] = pt.z;
      } else if (data.trailHistory.length > 0) {
        const last = data.trailHistory[data.trailHistory.length - 1];
        positions[idx] = last.x;
        positions[idx + 1] = last.y;
        positions[idx + 2] = last.z;
      }
    }
    geo.attributes.position.needsUpdate = true;
    geo.setDrawRange(0, data.trailHistory.length);
  }
}

export function resetRoverTrail(group: THREE.Group): void {
  const data = group.userData as RoverUserData;
  if (!data) return;
  data.trailHistory = [];
  const geo = data.trailLine.geometry as THREE.BufferGeometry;
  geo.setDrawRange(0, 0);
}

export function disposeRoverMesh(group: THREE.Group): void {
  const data = group.userData as RoverUserData | undefined;

  if (data?.trailLine) {
    if (data.trailLine.parent) {
      data.trailLine.parent.remove(data.trailLine);
    }
    if (data.trailLine.geometry) {
      data.trailLine.geometry.dispose();
    }
    if (data.trailLine.material) {
      if (Array.isArray(data.trailLine.material)) {
        for (const mat of data.trailLine.material) {
          if (mat) mat.dispose();
        }
      } else {
        data.trailLine.material.dispose();
      }
    }
    data.trailHistory = [];
  }

  const disposedGeometries = new Set<THREE.BufferGeometry>();
  const disposedMaterials = new Set<THREE.Material>();

  group.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (mesh.geometry && !disposedGeometries.has(mesh.geometry)) {
      mesh.geometry.dispose();
      disposedGeometries.add(mesh.geometry);
    }
    if (mesh.material) {
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const m of mats) {
        if (m && !disposedMaterials.has(m)) {
          m.dispose();
          disposedMaterials.add(m);
        }
      }
    }
  });

  if (group.parent) {
    group.parent.remove(group);
  }

  if (data) {
    data.wheels = [];
    data.trailHistory = [];
  }
}
