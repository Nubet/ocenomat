"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/button";
import { signIn } from "./actions";

export function LoginForm({
  configured,
  initialError,
}: {
  configured: boolean;
  initialError: string;
}) {
  const [state, action, pending] = useActionState(signIn, { error: initialError });
  return (
    <form action={action} className="mt-8 space-y-5" aria-busy={pending}>
      <div>
        <label htmlFor="email" className="mb-2 block text-body font-semibold">
          Służbowy adres e-mail
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          required
          maxLength={320}
          disabled={!configured || pending}
          className="h-12 w-full rounded-control border bg-surface px-3 text-body"
        />
      </div>
      <div>
        <label htmlFor="password" className="mb-2 block text-body font-semibold">
          Hasło
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          maxLength={1024}
          disabled={!configured || pending}
          className="h-12 w-full rounded-control border bg-surface px-3 text-body"
        />
      </div>
      <output aria-live="polite" className="block min-h-5 text-body text-muted-foreground">
        {!configured
          ? "Logowanie oczekuje na konfigurację Supabase przez administratora."
          : state.error}
      </output>
      <Button
        type="submit"
        variant="primary"
        disabled={!configured || pending}
        className="min-h-12 w-full disabled:opacity-50"
      >
        {pending ? "Logowanie…" : "Zaloguj się"}
      </Button>
    </form>
  );
}
