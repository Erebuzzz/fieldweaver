# Visual Presentation Review

**Status:** Engineering recommendation. The browser implementation is in progress and still needs production-build and browser verification.

## Recommendation

Keep a browser-native Three.js view as an optional presentation layer for the existing simulation. It can make robot orientation, obstacle height, plume estimates, and camera motion easier to read during a demo. It does not improve localization accuracy or the safety algorithm by itself.

The current worktree already has a Three.js viewport, camera presets, and a 2D fallback. The renderer receives the scenario, mission, result, and current public frame as props. Verify the complete data path and source disclosure behavior before describing the view as a validated digital twin.

## Tool fit

| Tool | Fit for FieldWeaver | Recommendation |
| --- | --- | --- |
| Three.js | Browser rendering alongside the existing Next.js interface | Keep as the first presentation option, subject to browser and accessibility checks |
| Blender | Modeling and offline asset creation | Use only if custom rover or environment assets materially improve the demo; export browser-ready assets |
| MuJoCo | Rigid-body dynamics and contact simulation | Consider as a separate physics-validation effort if physical interaction fidelity becomes a requirement |
| NVIDIA Isaac Sim | Robotics and sensor simulation with a larger runtime and hardware footprint | Defer unless sensor realism or interoperability with an Isaac workflow becomes a project requirement |

The simulator remains the authority for robot state. Adding another physics engine to the live control path would require a separate design and validation effort.

## Verification status

No FPS, latency, bandwidth, cross-device compatibility, judging score, or award probability is asserted here. Measure rendering and payload behavior on named hardware before publishing performance claims. Confirm WebGL failure and context-loss behavior, 2D fallback, responsive sizing, public telemetry fields, and post-run source disclosure in a browser run.

## References

- [Three.js documentation](https://threejs.org/docs/)
- [Blender Python API](https://docs.blender.org/api/current/index.html)
- [MuJoCo overview](https://mujoco.readthedocs.io/en/stable/overview.html)
- [Isaac Sim system requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html)
