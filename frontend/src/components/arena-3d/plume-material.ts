import * as THREE from "three";

export function createPlumeMaterial(width: number, height: number): THREE.ShaderMaterial {
  return new THREE.ShaderMaterial({
    uniforms: {
      u_time: { value: 0 },
      u_arena_size: { value: new THREE.Vector2(width, height) },
      u_estimate_valid: { value: 0.0 },
      u_estimate_pos: { value: new THREE.Vector2(0, 0) },
      u_estimate_confidence: { value: 0.0 },
      u_robot_count: { value: 0 },
      u_robot_positions: { value: Array.from({ length: 8 }, () => new THREE.Vector2(0, 0)) },
      u_robot_measurements: { value: new Float32Array(8) },
      u_revealed: { value: 0.0 },
      u_truth_pos: { value: new THREE.Vector2(0, 0) },
    },
    vertexShader: `
      varying vec2 vUv;
      varying vec3 vWorldPos;

      void main() {
        vUv = uv;
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vWorldPos = worldPosition.xyz;
        gl_Position = projectionMatrix * viewMatrix * worldPosition;
      }
    `,
    fragmentShader: `
      precision highp float;

      uniform float u_time;
      uniform vec2 u_arena_size;
      uniform float u_estimate_valid;
      uniform vec2 u_estimate_pos;
      uniform float u_estimate_confidence;
      uniform int u_robot_count;
      uniform vec2 u_robot_positions[8];
      uniform float u_robot_measurements[8];
      uniform float u_revealed;
      uniform vec2 u_truth_pos;

      varying vec2 vUv;
      varying vec3 vWorldPos;

      void main() {
        vec2 p = vWorldPos.xz;

        // Base dark tactical graphite surface
        vec3 color = vec3(0.043, 0.059, 0.090);
        float alpha = 0.92;

        // Subtle precision grid coordinates
        vec2 grid = abs(fract(p - 0.5) - 0.5) / max(fwidth(p), vec2(0.001));
        float gridLine = 1.0 - min(min(grid.x, grid.y), 1.0);
        color += vec3(0.07, 0.12, 0.20) * gridLine * 0.35;

        // Local rover radar halos based on real-time sensor measurements
        float roverInfluence = 0.0;
        for (int i = 0; i < 8; i++) {
          if (i >= u_robot_count) break;
          float d = length(p - u_robot_positions[i]);
          float pulse = sin(u_time * 2.4 - d * 3.5) * 0.5 + 0.5;
          float ring = smoothstep(0.08, 0.0, abs(d - 0.75)) * pulse * 0.4;
          float core = smoothstep(0.9, 0.0, d) * 0.15;
          roverInfluence += (ring + core);
        }
        color += vec3(0.05, 0.65, 0.91) * min(roverInfluence, 0.7);

        // Estimated source dispersion field (only active when estimate is valid)
        if (u_estimate_valid > 0.5) {
          float distEst = length(p - u_estimate_pos);
          float sigma = max(2.2 - u_estimate_confidence * 1.1, 0.7);
          float intensity = exp(-0.5 * (distEst * distEst) / (sigma * sigma));

          vec3 heatColor = mix(
            vec3(0.05, 0.65, 0.91),
            vec3(0.08, 0.72, 0.65),
            smoothstep(0.25, 0.65, intensity)
          );
          heatColor = mix(
            heatColor,
            vec3(0.96, 0.62, 0.07),
            smoothstep(0.65, 0.95, intensity)
          );

          // Topographic contour isolines with smooth antialiased steps
          float contour = abs(fract(distEst * 1.25 - u_time * 0.12) - 0.5);
          float line = smoothstep(0.07, 0.0, contour) * smoothstep(4.5, 0.0, distEst);

          color += heatColor * (intensity * 0.65 + line * 0.3);
        }

        // Evaluated ground truth target ring (quarantined until post-run evaluation)
        if (u_revealed > 0.5) {
          float distTruth = length(p - u_truth_pos);
          float truthRing1 = smoothstep(0.05, 0.0, abs(distTruth - 0.6));
          float truthRing2 = smoothstep(0.04, 0.0, abs(distTruth - 0.3));
          color += vec3(0.16, 0.85, 0.53) * (truthRing1 * 0.7 + truthRing2 * 0.9);
        }

        gl_FragColor = vec4(color, alpha);
      }
    `,
    transparent: true,
    depthWrite: false,
  });
}
