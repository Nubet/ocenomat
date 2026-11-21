"use client";

import { useRef, useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { sendReminder } from "./actions";

export function ReminderButton({ assessmentId }: { assessmentId: string }) {
  const key = useRef<string | null>(null);
  const [message, setMessage] = useState("");
  const [pending, startTransition] = useTransition();
  return (
    <div>
      <Button
        disabled={pending}
        onClick={() => {
          key.current ??= crypto.randomUUID();
          const requestKey = key.current;
          startTransition(async () => {
            try {
              const error = await sendReminder(assessmentId, requestKey);
              setMessage(error ?? "Dostarczono na pulpit prowadzącego ocenę.");
              if (!error) key.current = null;
            } catch {
              setMessage("Nie potwierdzono dostarczenia. Ponów próbę.");
            }
          });
        }}
      >
        {pending ? "Wysyłanie…" : "Wyślij przypomnienie w aplikacji"}
      </Button>
      <output className="mt-2 block text-label text-muted-foreground">{message}</output>
    </div>
  );
}
