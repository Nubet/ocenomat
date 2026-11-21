"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, Note } from "@/components/ui/card";
import { saveDocument } from "./document-actions";
import {
  documentHref,
  type AssessmentDocument,
  type DocumentActionState,
  type JobDescription,
} from "./document-types";
import { PdfFields } from "./pdf-fields";
import { assessmentHref, type AssessmentRecord } from "./types";

export function DocumentsPanel({
  assessment,
  initialFiles,
  initialDescriptions,
  visible,
  showPdf,
  onSaved,
  onPendingChange,
}: {
  assessment: AssessmentRecord;
  initialFiles: AssessmentDocument[];
  initialDescriptions: JobDescription[];
  visible: boolean;
  showPdf: boolean;
  onSaved: (assessment: AssessmentRecord) => void;
  onPendingChange: (pending: boolean) => void;
}) {
  const [files, setFiles] = useState(initialFiles);
  const [descriptions, setDescriptions] = useState(initialDescriptions);
  const [descriptionId, setDescriptionId] = useState(assessment.job_description_id ?? "");
  const [file, setFile] = useState<File | null>(null);
  const [kind, setKind] = useState("osp");
  const [state, action, pending] = useActionState(
    async (previous: DocumentActionState, form: FormData) => {
      if (previous.conflict) return previous;
      if (form.get("operation") === "upload" && file) form.set("file", file);
      onPendingChange(true);
      try {
        const result = await saveDocument(assessment.id, previous, form);
        if (result.assessment) {
          onSaved(result.assessment);
          setDescriptionId(result.assessment.job_description_id ?? "");
        }
        if (result.files) setFiles(result.files);
        if (result.descriptions) setDescriptions(result.descriptions);
        if (!result.error && form.get("operation") === "upload") setFile(null);
        return result;
      } finally {
        onPendingChange(false);
      }
    },
    { error: "", conflict: false },
  );
  const draft = assessment.status === "draft";
  const completed = assessment.status === "completed";
  const selected = descriptions.find((item) => item.id === assessment.job_description_id);
  const generated = files.find((item) => item.kind === "periodic_pdf");
  const disabled = pending || state.conflict;

  return (
    <section hidden={!visible} aria-label="Dokumenty oceny" className="space-y-5">
      {state.message ? (
        <output className="block text-body text-success">{state.message}</output>
      ) : null}
      {state.error ? (
        <Note>
          <p role="alert">{state.error}</p>
          <a
            className="mt-3 inline-block font-semibold text-primary underline"
            href={`${assessmentHref(assessment.id)}?step=documents`}
            target="_blank"
            rel="noreferrer"
          >
            Otwórz zapisaną wersję w nowej karcie
          </a>
        </Note>
      ) : null}
      <Card className="p-6 sm:p-7">
        <p className="eyebrow">Opis stanowiska pracy</p>
        <h2 className="mt-3 text-lg font-semibold">OSP używany w tej ocenie</h2>
        <p className="mt-3 text-body">
          {selected
            ? `Wersja ${selected.version}: ${selected.document.filename}`
            : "Nie wybrano wersji OSP."}
        </p>
        {selected ? (
          <a
            className="mt-3 inline-block font-semibold text-primary underline"
            href={documentHref(assessment.id, selected.id, true)}
          >
            Pobierz wybraną wersję OSP
          </a>
        ) : null}
        <p className="mt-3 text-body text-muted-foreground">
          OSP jest wersjonowany dla pracownika. Nowszy plik nie zastępuje wersji wybranej w
          poprzedniej ocenie. Po potwierdzeniu ustaleń wybór jest zamknięty.
        </p>
        {draft && descriptions.length > 0 ? (
          <form action={action} className="mt-5">
            <input type="hidden" name="revision" value={assessment.revision} />
            <fieldset disabled={disabled} className="space-y-4">
              <legend className="sr-only">Wybór wersji OSP</legend>
              <label className="block">
                <span className="field-label">Wersja OSP pracownika</span>
                <select
                  className="field"
                  name="job_description_id"
                  required
                  value={descriptionId}
                  onChange={(event) => setDescriptionId(event.target.value)}
                >
                  <option value="">Wybierz wersję</option>
                  {descriptions.map((item) => (
                    <option key={item.id} value={item.id}>
                      Wersja {item.version} — {item.document.filename}
                    </option>
                  ))}
                </select>
              </label>
              <Button
                type="submit"
                name="operation"
                value="select_osp"
                disabled={descriptionId === assessment.job_description_id}
              >
                Użyj wybranej wersji OSP
              </Button>
            </fieldset>
          </form>
        ) : null}
      </Card>
      {!completed ? (
        <Card className="p-6 sm:p-7">
          <h2 className="mb-4 text-base font-semibold">Dodaj dokument</h2>
          <form action={action}>
            <input type="hidden" name="revision" value={assessment.revision} />
            <fieldset disabled={disabled} className="space-y-4">
              <legend className="sr-only">Przesyłanie dokumentu</legend>
              {draft ? (
                <label className="block">
                  <span className="field-label">Rodzaj dokumentu</span>
                  <select
                    className="field"
                    name="kind"
                    value={kind}
                    onChange={(event) => setKind(event.target.value)}
                  >
                    <option value="osp">Nowa wersja OSP pracownika</option>
                    <option value="attachment">Załącznik do oceny</option>
                  </select>
                </label>
              ) : (
                <input type="hidden" name="kind" value="attachment" />
              )}
              <label className="block">
                <span className="field-label">Plik PDF lub DOCX (do 10 MiB)</span>
                <input
                  className="field"
                  name="file"
                  type="file"
                  accept=".pdf,.docx"
                  required={!file}
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
              </label>
              {file ? <p className="text-body">Wybrany plik: {file.name}</p> : null}
              {file && (file.size === 0 || file.size > 10 * 1024 * 1024) ? (
                <p role="alert" className="text-body text-danger">
                  Wybierz niepusty plik o rozmiarze do 10 MiB.
                </p>
              ) : null}
              <Button
                type="submit"
                name="operation"
                value="upload"
                disabled={file !== null && (file.size === 0 || file.size > 10 * 1024 * 1024)}
              >
                {pending ? "Przesyłanie…" : "Zapisz dokument"}
              </Button>
            </fieldset>
          </form>
        </Card>
      ) : null}
      <Card className="p-6 sm:p-7">
        <h2 className="mb-4 text-base font-semibold">Pliki tej oceny</h2>
        {files.length === 0 ? (
          <p className="text-body text-muted-foreground">Nie dodano jeszcze plików.</p>
        ) : (
          <ul className="divide-y">
            {files.map((item) => (
              <li key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <span className="text-body">
                  {item.filename}
                  <span className="ml-2 text-caption text-muted-foreground">
                    {Math.ceil(item.size / 1024)} KiB
                    {item.kind === "periodic_pdf" ? ` · rewizja ${item.assessment_revision}` : ""}
                  </span>
                </span>
                <a
                  className="font-semibold text-primary underline"
                  href={documentHref(assessment.id, item.id)}
                >
                  Pobierz<span className="sr-only"> {item.filename}</span>
                </a>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <div hidden={!showPdf}>
        {!completed ? (
          <Note>
            PDF arkusza {assessment.form} będzie dostępny po zakończeniu oceny i zatwierdzeniu
            wszystkich ocen cząstkowych.
          </Note>
        ) : generated ? (
          <Note>
            Arkusz {assessment.form} jest gotowy — pobierz go z listy plików. Dokument nie jest
            podpisany ani doręczony. Zachowano wersję szablonu i zakończoną rewizję oceny.
          </Note>
        ) : (
          <Card className="p-6 sm:p-7">
            <form action={action}>
              <input type="hidden" name="revision" value={assessment.revision} />
              <PdfFields assessment={assessment} disabled={disabled} />
            </form>
          </Card>
        )}
      </div>
    </section>
  );
}
