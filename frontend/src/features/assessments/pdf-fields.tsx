"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { AssessmentRecord } from "./types";

const textFields = [
  ["office_name", "Nazwa urzędu"],
  ["assessor_department", "Komórka organizacyjna oceniającego"],
  ["assessor_position", "Stanowisko oceniającego"],
] as const;

export function PdfFields({
  assessment,
  disabled,
}: {
  assessment: AssessmentRecord;
  disabled: boolean;
}) {
  const [draft, setDraft] = useState({
    office_name: "",
    assessor_department: "",
    assessor_position: "",
    period_end: "",
    civil_service_status: "",
    previous_exists: "no",
    previous_outcome: "",
    previous_level: "",
    previous_date: "",
    no_promotion_request: false,
  });
  return (
    <fieldset disabled={disabled} className="space-y-5">
      <legend className="mb-4 text-base font-semibold">Dane do arkusza {assessment.form}</legend>
      <p className="text-body text-muted-foreground">
        Nazwiska, stanowisko pracownika, kryteria, oceny i wynik pochodzą z zapisanej oceny.
        Uzupełnij brakujące dane. Pierwszy wygenerowany dokument zostanie zachowany wraz z tymi
        danymi.
      </p>
      <div className="grid gap-5 sm:grid-cols-2">
        {textFields.map(([name, label]) => (
          <label key={name} className="block">
            <span className="field-label">{label}</span>
            <input
              className="field"
              name={name}
              required
              maxLength={200}
              value={draft[name]}
              onChange={(event) => setDraft({ ...draft, [name]: event.target.value })}
            />
          </label>
        ))}
        <label className="block">
          <span className="field-label">Koniec okresu oceny (data „do”)</span>
          <input
            className="field"
            name="period_end"
            type="date"
            required
            min={assessment.date_talk ?? undefined}
            value={draft.period_end}
            onChange={(event) => setDraft({ ...draft, period_end: event.target.value })}
          />
        </label>
        <label className="block">
          <span className="field-label">Status ocenianego</span>
          <select
            className="field"
            name="civil_service_status"
            required
            value={draft.civil_service_status}
            onChange={(event) => setDraft({ ...draft, civil_service_status: event.target.value })}
          >
            <option value="">Wybierz status</option>
            <option value="employee">Pracownik służby cywilnej</option>
            <option value="official">Urzędnik służby cywilnej</option>
          </select>
        </label>
      </div>
      <p className="text-body text-muted-foreground">
        Data „do” to data sporządzenia oceny na piśmie, a w przypadku wskazanym we wzorze — ostatni
        dzień pracy na stanowisku. Nie jest automatycznie kopiowana z planowanego terminu oceny.
      </p>
      {draft.civil_service_status === "official" ? (
        <>
          <label className="block">
            <span className="field-label">Poprzednia ocena okresowa urzędnika</span>
            <select
              className="field"
              name="previous_exists"
              value={draft.previous_exists}
              onChange={(event) => setDraft({ ...draft, previous_exists: event.target.value })}
            >
              <option value="no">Nie było poprzedniej oceny</option>
              <option value="yes">Uzupełniam poprzednią ocenę</option>
            </select>
          </label>
          {draft.previous_exists === "yes" ? (
            <div className="grid gap-5 sm:grid-cols-3">
              <label>
                <span className="field-label">Wynik poprzedniej oceny</span>
                <select
                  className="field"
                  name="previous_outcome"
                  required
                  value={draft.previous_outcome}
                  onChange={(event) => setDraft({ ...draft, previous_outcome: event.target.value })}
                >
                  <option value="">Wybierz wynik</option>
                  <option value="positive">Pozytywna</option>
                  <option value="negative">Negatywna</option>
                </select>
              </label>
              <label>
                <span className="field-label">Poziom poprzedniej oceny</span>
                <select
                  className="field"
                  name="previous_level"
                  required
                  value={draft.previous_level}
                  onChange={(event) => setDraft({ ...draft, previous_level: event.target.value })}
                >
                  <option value="">Wybierz poziom</option>
                  {[
                    "Znacznie poniżej oczekiwań",
                    "Poniżej oczekiwań",
                    "Na poziomie oczekiwań",
                    "Powyżej oczekiwań",
                    "Znacznie powyżej oczekiwań",
                  ].map((label, index) => (
                    <option key={label} value={index + 1}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span className="field-label">Data poprzedniej oceny</span>
                <input
                  className="field"
                  name="previous_date"
                  type="date"
                  required
                  value={draft.previous_date}
                  onChange={(event) => setDraft({ ...draft, previous_date: event.target.value })}
                />
              </label>
            </div>
          ) : null}
        </>
      ) : null}
      <label className="flex items-start gap-3 text-body">
        <input
          className="mt-1"
          name="no_promotion_request"
          type="checkbox"
          required
          checked={draft.no_promotion_request}
          onChange={(event) => setDraft({ ...draft, no_promotion_request: event.target.checked })}
        />
        <span>
          Nie dołączam wniosku o kolejny stopień służbowy. Zgodnie z objaśnieniem wzoru część III
          nie będzie drukowana. Taki wniosek wymaga odrębnego przygotowania.
        </span>
      </label>
      <Button type="submit" name="operation" value="pdf">
        {disabled ? "Przygotowywanie…" : `Wygeneruj PDF arkusza ${assessment.form}`}
      </Button>
    </fieldset>
  );
}
