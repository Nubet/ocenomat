"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Note } from "@/components/ui/card";
import type { components } from "@/lib/api/schema";
import { analyzeJobDescription } from "@/features/assistant/osp-actions";

export function OspAnalysisPanel({
  assessmentId,
  jobDescriptionId,
  revision,
}: {
  assessmentId: string;
  jobDescriptionId: string | null;
  revision: number;
}) {
  const [analysis, setAnalysis] = useState<components["schemas"]["OspAnalysis"] | null>(null);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  return (
    <div className="mt-5 space-y-3" aria-busy={pending}>
      <Button
        disabled={pending || !jobDescriptionId}
        onClick={() => {
          setError("");
          setAnalysis(null);
          startTransition(async () => {
            const result = await analyzeJobDescription(assessmentId);
            if ("error" in result) {
              setError(result.error);
              return;
            }
            if (
              result.analysis.assessment_revision !== revision ||
              result.analysis.job_description_id !== jobDescriptionId
            ) {
              setError("Wybrana wersja lub zapis oceny zmieniły się. Odśwież ocenę przed analizą.");
              return;
            }
            setAnalysis(result.analysis);
          });
        }}
      >
        Przeanalizuj wybrane OSP
      </Button>
      {!jobDescriptionId && (
        <p className="text-caption text-muted-foreground">
          Najpierw dodaj lub wybierz zapisaną wersję OSP poniżej.
        </p>
      )}
      {pending && (
        <output className="block text-body">
          Analizuję zadania i sprawdzam dowody rekomendacji…
        </output>
      )}
      {error && (
        <p role="alert" className="text-body text-danger">
          {error}
        </p>
      )}
      {analysis && (
        <div aria-live="polite">
          {analysis.status === "insufficient_evidence" && (
            <Note>
              Brak wystarczających podstaw do rekomendacji dodatkowych kryteriów. Sprawdź wybrane
              OSP.
            </Note>
          )}
          {(analysis.recommendations ?? []).map((suggestion) => (
            <div key={suggestion.criterion_id} className="mt-3 rounded-xl border p-4">
              <h3 className="text-label font-semibold">Propozycja: {suggestion.name}</h3>
              <p className="mt-2 text-body">{suggestion.reason}</p>
              {suggestion.evidence.map((proof) => (
                <blockquote key={proof.fragment_id} className="mt-3 border-l-2 pl-3 text-caption">
                  <p className="whitespace-pre-wrap">{proof.quote}</p>
                  <p className="mt-1 text-muted-foreground">
                    {proof.locator}
                    {proof.page ? ` · str. ${proof.page}` : ""}
                  </p>
                </blockquote>
              ))}
            </div>
          ))}
          <a
            className="mt-3 inline-block text-caption underline"
            href={`/assessments/${assessmentId}/documents/${analysis.job_description_id}?osp=1`}
            target="_blank"
            rel="noreferrer"
          >
            Sprawdź cytaty w oryginalnym OSP
          </a>
          <Note className="mt-3">
            To analiza stanowiska, nie ocena osoby. Niczego nie zapisano ani nie wybrano
            automatycznie. W następnym kroku samodzielnie wybierz kryteria i zapisz ich
            uzasadnienie.
          </Note>
          {(analysis.limitations ?? []).map((text, i) => (
            <p key={i} className="mt-2 text-caption text-muted-foreground">
              {text}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
