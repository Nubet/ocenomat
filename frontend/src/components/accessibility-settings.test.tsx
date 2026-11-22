import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import RootLayout from "@/app/layout";

describe("accessibility settings", () => {
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
