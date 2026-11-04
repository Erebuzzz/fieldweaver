# Visual Presentation Roadmap

## Current direction

FieldWeaver has a deterministic 2D simulation interface. The current worktree adds a browser-side Three.js scene intended to render the same mission and simulation frames. Keep that layer read-only and preserve the 2D view as the fallback.

~~~mermaid
flowchart LR
    Sim[Simulation and safety core] --> API[Public API response]
    API --> UI[Next.js workbench]
    UI --> Three[Three.js presentation]
    UI --> Canvas[2D fallback]
    Blender[Optional Blender-authored assets] -->|optional export| Three
    MuJoCo[Optional separate dynamics validation] -->|recorded comparison| Sim
    Isaac[Optional sensor simulation] -->|evaluated separately| Sim
~~~

## Verification gates

1. Run the frontend type check, lint, and production build with the current dependency lockfile.
2. Open the built app in a browser and confirm the 3D canvas renders the supplied public frame.
3. Exercise perspective, top-down, and follow camera modes, then switch to the 2D view.
4. Confirm WebGL initialization failure and context loss leave the 2D view usable.
5. Inspect live and completed mission views to ensure the source is only disclosed when the backend response permits it.
6. Check narrow and wide viewport layouts and capture any console errors.
7. If making performance claims, record device, browser, scene size, measured frame rate, and measurement method.

Do not add Blender, MuJoCo, or Isaac Sim to the runtime path solely for visual polish. Revisit those tools only when their modeling, contact-dynamics, or sensor-simulation capability is needed and can be validated independently.
