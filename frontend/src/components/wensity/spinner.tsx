import type { CSSProperties } from "react";

type SpinnerProps = {
  label: string;
};

export function Spinner({ label }: SpinnerProps) {
  return (
    <span className="wensity-spinner" role="status" aria-label={label}>
      <span className="wensity-spinner-lines" aria-hidden="true">
        {Array.from({ length: 12 }, (_, index) => (
          <span
            key={index}
            className="wensity-spinner-line"
            style={{
              transform: `rotate(${index * 30}deg)`,
              animationDelay: `${index * -70}ms`,
              opacity: 0.22 + index * 0.045,
            } as CSSProperties}
          />
        ))}
      </span>
    </span>
  );
}
