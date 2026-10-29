import type { Frame, MissionSpec, PublicRegion, RunResult, Scenario } from "@/lib/types";

const SIZE = 720;

function pxX(value: number, width: number): number {
  return (value / width) * SIZE;
}

function pxY(value: number, height: number): number {
  return SIZE - (value / height) * SIZE;
}

function allRegions(scenario: Scenario, result: RunResult | null): PublicRegion[] {
  const regions = new Map<string, PublicRegion>();
  for (const region of scenario.initial_regions) regions.set(region.id, region);
  for (const event of result?.world_events ?? []) {
    for (const region of event.regions) regions.set(region.id, region);
  }
  return [...regions.values()];
}

type Props = {
  scenario: Scenario | null;
  mission: MissionSpec | null;
  result: RunResult | null;
  frame: Frame | null;
  frameIndex: number;
};

export function ArenaCanvas({ scenario, mission, result, frame, frameIndex }: Props) {
  if (!scenario) {
    return <div className="arena-empty">Connect to the simulation API to load the arenas.</div>;
  }

  const width = scenario.arena.width_m;
  const height = scenario.arena.height_m;
  const currentTime = frame?.t ?? 0;
  const visibleIds = new Set(frame?.active_region_ids ?? []);
  const regions = allRegions(scenario, result).filter((region) => {
    if (result && frame) return visibleIds.has(region.id);
    return region.active_from_s <= currentTime;
  });
  const estimate = frame?.estimate;
  const robots = frame?.robots ?? [];
  const pastFrames = result?.frames.slice(0, frameIndex + 1) ?? [];
  const robotIds = [...new Set(pastFrames.flatMap((item) => item.robots.map((robot) => robot.id)))];
  const ringRadius = mission?.formation.radius;
  const ringCount = mission?.robot_count ?? scenario.default_robot_count;
  const revealedTruth = result?.evaluation.ground_truth.revealed === "after_run_only"
    ? result.evaluation.ground_truth
    : null;

  return (
    <div className="arena-frame">
      <svg
        className="arena-svg"
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        role="img"
        aria-label={`${scenario.name} arena showing robot positions and trajectories`}
      >
        <defs>
          <pattern id="minor-grid" width={SIZE / width} height={SIZE / height} patternUnits="userSpaceOnUse">
            <path d={`M ${SIZE / width} 0 L 0 0 0 ${SIZE / height}`} className="grid-line" />
          </pattern>
        </defs>
        <rect width={SIZE} height={SIZE} className="arena-ground" />
        <rect width={SIZE} height={SIZE} fill="url(#minor-grid)" />
        {Array.from({ length: Math.floor(width) + 1 }, (_, index) => (
          <text key={`x-${index}`} x={pxX(index, width) + 4} y={SIZE - 6} className="axis-label">
            {index} m
          </text>
        ))}
        {Array.from({ length: Math.floor(height) + 1 }, (_, index) => (
          <text key={`y-${index}`} x={5} y={pxY(index, height) - 4} className="axis-label">
            {index}
          </text>
        ))}

        {regions.map((region) => {
          const regionClass = region.kind === "restricted" ? "region restricted-region" : "region obstacle-region";
          if (region.shape === "rect") {
            const x = pxX(region.x_min ?? 0, width);
            const y = pxY(region.y_max ?? 0, height);
            const regionWidth = pxX((region.x_max ?? 0) - (region.x_min ?? 0), width);
            const regionHeight = pxY(region.y_min ?? 0, height) - y;
            return (
              <g key={region.id}>
                <rect x={x} y={y} width={regionWidth} height={regionHeight} className={regionClass} />
                <text x={x + 8} y={y + 18} className="region-label">{region.label}</text>
              </g>
            );
          }
          const cx = pxX(region.cx ?? 0, width);
          const cy = pxY(region.cy ?? 0, height);
          const radius = pxX(region.radius ?? 0, width);
          return (
            <g key={region.id}>
              <circle cx={cx} cy={cy} r={radius} className={regionClass} />
              <text x={cx} y={cy} className="region-label centered-label">{region.label}</text>
            </g>
          );
        })}

        {estimate?.valid && ringRadius ? (
          <g className="formation-targets">
            <circle
              cx={pxX(estimate.x, width)}
              cy={pxY(estimate.y, height)}
              r={pxX(ringRadius, width)}
              className="formation-ring"
            />
            {Array.from({ length: ringCount }, (_, index) => {
              const angle = (Math.PI * 2 * index) / ringCount;
              const x = estimate.x + ringRadius * Math.cos(angle);
              const y = estimate.y + ringRadius * Math.sin(angle);
              return (
                <circle
                  key={`slot-${index}`}
                  cx={pxX(x, width)}
                  cy={pxY(y, height)}
                  r={5}
                  className="formation-slot"
                />
              );
            })}
          </g>
        ) : null}

        {robotIds.map((robotId) => {
          const points = pastFrames
            .map((item) => item.robots.find((robot) => robot.id === robotId))
            .filter((robot) => robot !== undefined)
            .map((robot) => `${pxX(robot.x, width)},${pxY(robot.y, height)}`)
            .join(" ");
          return <polyline key={`path-${robotId}`} points={points} className="robot-path" />;
        })}

        {revealedTruth ? (
          <g className="truth-marker" aria-label="Ground truth shown after evaluation">
            <circle cx={pxX(revealedTruth.x, width)} cy={pxY(revealedTruth.y, height)} r={9} />
            <path
              d={`M ${pxX(revealedTruth.x, width) - 13} ${pxY(revealedTruth.y, height)} h 26 M ${pxX(revealedTruth.x, width)} ${pxY(revealedTruth.y, height) - 13} v 26`}
            />
          </g>
        ) : null}

        {estimate?.valid ? (
          <g className="estimate-marker">
            <circle cx={pxX(estimate.x, width)} cy={pxY(estimate.y, height)} r={8} />
            <text x={pxX(estimate.x, width) + 12} y={pxY(estimate.y, height) - 12}>
              estimate
            </text>
          </g>
        ) : null}

        {robots.map((robot) => (
          <g key={robot.id} className="robot-marker">
            <circle cx={pxX(robot.x, width)} cy={pxY(robot.y, height)} r={13} />
            <text x={pxX(robot.x, width)} y={pxY(robot.y, height) + 4}>
              {robot.id + 1}
            </text>
          </g>
        ))}
        <rect width={SIZE} height={SIZE} className="arena-border" />
      </svg>

      <div className="arena-legend" aria-label="Arena legend">
        <span><i className="legend-robot" /> Robot</span>
        <span><i className="legend-estimate" /> Estimate</span>
        <span><i className="legend-ring" /> Formation slot</span>
        <span><i className="legend-obstacle" /> Obstacle</span>
        {revealedTruth ? <span><i className="legend-truth" /> Evaluated source</span> : null}
      </div>
    </div>
  );
}
