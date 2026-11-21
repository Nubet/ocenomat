import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import { CitationCard } from "./citation-card";
import type { AssistantCitation } from "./types";

const citation: AssistantCitation = {
  chunk_id: "chunk",
  source_id: "periodic-regulation",
  title: "Rozporządzenie w sprawie ocen okresowych",
  document_version: "2016-html-v1",
  locator: "html:#para_5",
  page: null,
  quote: "Cytowany fragment <ustawy>.",
  content_sha256: "a".repeat(64),
  legal_checked_on: "2026-11-21",
  original_path: "/api/v1/knowledge/sources/periodic-regulation/original",
  official_url: "https://eli.gov.pl/api/acts/DU/2016/470/text.html",
};

it("opens the official source and keeps its supporting quote in a closed disclosure", () => {
  const html = renderToStaticMarkup(<CitationCard citation={citation} />);
  expect(html).toContain(`href="${citation.official_url}"`);
  expect(html).toContain("Otwórz oficjalne źródło");
  expect(html).toContain("§ 5");
  expect(html).toContain("Cytowany fragment &lt;ustawy&gt;.");
  expect(html).toContain("<details");
  expect(html).not.toContain(" open=");
  expect(html).not.toContain("Pobierz zapisaną kopię");
  expect(html).not.toContain('href="/knowledge/sources/');
});

it("preserves access to the saved original when the official URL is missing", () => {
  const html = renderToStaticMarkup(
    <CitationCard citation={{ ...citation, official_url: null }} />,
  );
  expect(html).toContain('href="/knowledge/sources/periodic-regulation"');
  expect(html).toContain("Pobierz zapisaną kopię");
  expect(html).not.toContain("Otwórz oficjalne źródło");
});
