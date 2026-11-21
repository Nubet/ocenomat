import { Icon } from "@/components/ui/icon";
import type { AssistantCitation } from "./types";

export function CitationCard({ citation }: { citation: AssistantCitation }) {
  const href =
    citation.official_url ?? `/knowledge/sources/${encodeURIComponent(citation.source_id)}`;
  const locator = citation.locator.replace(/^html:#para_(\d+)$/, "§ $1");

  return (
    <div className="mt-3 rounded-xl border bg-surface p-3.5">
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="group block rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary"
      >
        <span className="flex items-start gap-2 text-label font-semibold text-primary-strong group-hover:underline">
          <Icon name="file" size={15} className="mt-0.5 shrink-0" />
          <span className="min-w-0 flex-1">{citation.title}</span>
          <Icon name="arrow-up-right" size={15} className="mt-0.5 shrink-0" />
        </span>
        <span className="mt-2 block text-caption text-primary">
          {citation.official_url ? "Otwórz oficjalne źródło" : "Pobierz zapisaną kopię"}
          <span className="sr-only"> (nowa karta)</span>
        </span>
      </a>
      <p className="mt-2 text-caption text-muted-foreground">
        {locator}
        {citation.page ? ` · str. ${citation.page}` : ""}
      </p>
      <details className="mt-3 border-t pt-2 text-caption text-muted-foreground">
        <summary className="rounded py-1 font-medium text-foreground focus-visible:outline-2 focus-visible:outline-primary">
          Zobacz cytowany fragment
        </summary>
        <blockquote className="mt-2 border-l-2 border-primary-border pl-3 leading-5 whitespace-pre-wrap">
          {citation.quote}
        </blockquote>
        <p className="mt-3">
          Aktualność sprawdzona:{" "}
          {new Date(citation.legal_checked_on).toLocaleDateString("pl-PL", {
            timeZone: "Europe/Warsaw",
          })}
        </p>
      </details>
    </div>
  );
}
