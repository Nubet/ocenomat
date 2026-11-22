"use client";

import { useEffect, useState } from "react";

type Contrast = "default" | "dark" | "light";
type Position = "bottom-right" | "bottom-left" | "top-right" | "top-left";

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
    try {
      localStorage.setItem("ocenomat-accessibility-position", value);
    } catch {
      // Storage may be unavailable in private browsing.
    }
  }

  return (
    <div className="accessibility-widget no-print" data-position={position}>
      {open && (
        <section
          className="accessibility-panel"
          id="accessibility-panel"
          aria-label="Ustawienia dostępności"
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
            value={position}
            onChange={(event) => changePosition(event.target.value as Position)}
          >
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
        onClick={() => setOpen(!open)}
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
