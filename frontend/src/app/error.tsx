"use client";

import { Button, ButtonLink } from "@/components/ui/button";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="grid min-h-dvh place-items-center px-5">
      <section className="max-w-md rounded-card border bg-surface p-8">
        <h1 className="text-xl font-semibold">Nie można otworzyć przestrzeni roboczej</h1>
        <p className="mt-3 text-body text-muted-foreground">
          Sprawdź połączenie i spróbuj ponownie. Jeśli problem się powtarza, skontaktuj się z
          administratorem.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Button variant="primary" onClick={reset}>
            Spróbuj ponownie
          </Button>
          <ButtonLink href="/login">Przejdź do logowania</ButtonLink>
        </div>
      </section>
    </main>
  );
}
