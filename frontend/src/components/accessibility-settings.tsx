"use client";

import { useEffect, useRef, useState, type PointerEvent } from "react";

type Contrast = "default" | "dark" | "light";
type Position = "bottom-right" | "bottom-left" | "top-right" | "top-left";
type Point = { x: number; y: number };

export function dragPoint(
  x: number,
  y: number,
  width: number,
  height: number,
  size: number,
): Point {
  return {
    x: Math.min(1, Math.max(0, x / Math.max(1, width - size))),
    y: Math.min(1, Math.max(0, y / Math.max(1, height - size))),
  };
}

const positions: Record<Position, string> = {
  "bottom-right": "Prawy dolny róg",
  "bottom-left": "Lewy dolny róg",
  "top-right": "Prawy górny róg",
  "top-left": "Lewy górny róg",
};

export function AccessibilitySettings() {
  const [open, setOpen] = useState(false);
  const [contrast, setContrast] = useState<Contrast>("default");
  const [position, setPosition] = useState<Position>("bottom-right");
  const [point, setPoint] = useState<Point | null>(null);
  const drag = useRef<{
    x: number;
    y: number;
    left: number;
    top: number;
    size: number;
    moved: boolean;
  } | null>(null);

  useEffect(() => {
    let active = true;
    try {
      const saved = localStorage.getItem("ocenomat-contrast");
      if (saved === "dark" || saved === "light") {
        document.documentElement.dataset.contrast = saved;
        queueMicrotask(() => {
          if (active) setContrast(saved);
        });
      }
      const savedPosition = localStorage.getItem("ocenomat-accessibility-position");
      if (savedPosition && Object.hasOwn(positions, savedPosition)) {
        queueMicrotask(() => {
          if (active) setPosition(savedPosition as Position);
        });
      }
      const savedPoint = localStorage.getItem("ocenomat-accessibility-point");
      if (savedPoint) {
        const parsed: unknown = JSON.parse(savedPoint);
        if (
          typeof parsed === "object" &&
          parsed !== null &&
          "x" in parsed &&
          "y" in parsed &&
          typeof parsed.x === "number" &&
          typeof parsed.y === "number" &&
          parsed.x >= 0 &&
          parsed.x <= 1 &&
          parsed.y >= 0 &&
          parsed.y <= 1
        ) {
          const saved = { x: parsed.x, y: parsed.y };
          queueMicrotask(() => {
            if (active) setPoint(saved);
          });
        }
      }
    } catch {
      // Settings still work for the current page when storage is unavailable.
    }
    return () => {
      active = false;
    };
  }, []);

  function changeContrast(value: Contrast) {
    setContrast(value);
    if (value === "default") delete document.documentElement.dataset.contrast;
    else document.documentElement.dataset.contrast = value;
    try {
      if (value === "default") localStorage.removeItem("ocenomat-contrast");
      else localStorage.setItem("ocenomat-contrast", value);
    } catch {
      // Storage may be unavailable in private browsing.
    }
  }

  function changePosition(value: Position) {
    setPosition(value);
    setPoint(null);
    try {
      localStorage.setItem("ocenomat-accessibility-position", value);
      localStorage.removeItem("ocenomat-accessibility-point");
    } catch {
      // Storage may be unavailable in private browsing.
    }
  }

  function startDrag(event: PointerEvent<HTMLButtonElement>) {
    if (event.button !== 0) return;
    const rect = event.currentTarget.getBoundingClientRect();
    drag.current = {
      x: event.clientX,
      y: event.clientY,
      left: rect.left,
      top: rect.top,
      size: rect.width,
      moved: false,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function moveDrag(event: PointerEvent<HTMLButtonElement>) {
    const start = drag.current;
    if (!start) return;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (!start.moved && Math.hypot(dx, dy) < 5) return;
    start.moved = true;
    setOpen(false);
    setPoint(
      dragPoint(start.left + dx, start.top + dy, window.innerWidth, window.innerHeight, start.size),
    );
  }

  function endDrag(event: PointerEvent<HTMLButtonElement>) {
    const start = drag.current;
    if (!start?.moved) return;
    const next = dragPoint(
      start.left + event.clientX - start.x,
      start.top + event.clientY - start.y,
      window.innerWidth,
      window.innerHeight,
      start.size,
    );
    setPoint(next);
    try {
      localStorage.setItem("ocenomat-accessibility-point", JSON.stringify(next));
    } catch {
      // The position remains available for this page without storage.
    }
  }

  const side = point
    ? `${point.y < 0.5 ? "top" : "bottom"}-${point.x < 0.5 ? "left" : "right"}`
    : position;
  const pointStyle = point
    ? {
        left: point.x < 0.5 ? `calc((100vw - 3.5rem) * ${point.x})` : "auto",
        right: point.x >= 0.5 ? `calc((100vw - 3.5rem) * ${1 - point.x})` : "auto",
        top: point.y < 0.5 ? `calc((100dvh - 3.5rem) * ${point.y})` : "auto",
        bottom: point.y >= 0.5 ? `calc((100dvh - 3.5rem) * ${1 - point.y})` : "auto",
      }
    : undefined;

  return (
    <div className="accessibility-widget no-print" data-position={side} style={pointStyle}>
      {open && (
        <section
          className="accessibility-panel"
          id="accessibility-panel"
          aria-label="Ustawienia dostępności"
          style={
            point
              ? {
                  maxHeight: `calc((100dvh - 3.5rem) * ${point.y < 0.5 ? 1 - point.y : point.y} - 0.75rem)`,
                }
              : undefined
          }
        >
          <div className="accessibility-heading">
            <h2>Ustawienia dostępności</h2>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Zamknij ustawienia dostępności"
            >
              ×
            </button>
          </div>
          <fieldset>
            <legend>Tryby kontrastu</legend>
            <div className="accessibility-options">
              <button
                type="button"
                aria-pressed={contrast === "dark"}
                onClick={() => changeContrast("dark")}
              >
                Białe na czarnym
              </button>
              <button
                type="button"
                aria-pressed={contrast === "light"}
                onClick={() => changeContrast("light")}
              >
                Czarne na białym
              </button>
            </div>
          </fieldset>
          <label htmlFor="accessibility-position">Pozycja przycisku</label>
          <select
            id="accessibility-position"
            value={point ? "custom" : position}
            onChange={(event) => changePosition(event.target.value as Position)}
          >
            {point && (
              <option value="custom" disabled>
                Pozycja własna
              </option>
            )}
            {Object.entries(positions).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          <button
            className="accessibility-reset"
            type="button"
            onClick={() => changeContrast("default")}
          >
            Wyłącz wysoki kontrast
          </button>
        </section>
      )}
      <button
        className="accessibility-trigger"
        type="button"
        aria-label="Ustawienia dostępności"
        aria-expanded={open}
        aria-controls="accessibility-panel"
        onPointerDown={startDrag}
        onPointerMove={moveDrag}
        onPointerUp={endDrag}
        onPointerCancel={() => {
          drag.current = null;
        }}
        onClick={() => {
          if (!drag.current?.moved) setOpen(!open);
          drag.current = null;
        }}
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="4" r="2" />
          <path d="M4 8l8 1 8-1M12 9v5m0 0-4 7m4-7 4 7" />
        </svg>
      </button>
    </div>
  );
}
