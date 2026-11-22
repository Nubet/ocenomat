import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import RootLayout from "@/app/layout";
import { dragPoint } from "./accessibility-settings";

describe("accessibility settings", () => {
  it("keeps dragged positions inside the viewport and scales them with its size", () => {
    expect(dragPoint(100, 200, 456, 456, 56)).toEqual({ x: 0.25, y: 0.5 });
    expect(dragPoint(-10, 900, 456, 456, 56)).toEqual({ x: 0, y: 1 });
    expect(dragPoint(0, 0, 20, 20, 56)).toEqual({ x: 0, y: 0 });
  });
  it("exposes the settings button on every page through the root layout", () => {
    const html = renderToStaticMarkup(
      <RootLayout>
        <main>Przykładowa strona</main>
      </RootLayout>,
    );

    expect(html).toContain("Przykładowa strona");
    expect(html).toContain('aria-label="Ustawienia dostępności"');
    expect(html).toContain('aria-expanded="false"');
  });
});
