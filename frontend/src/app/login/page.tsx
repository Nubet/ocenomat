import type { Metadata } from "next";
import { Brand } from "@/components/ui/brand";
import { authConfig } from "@/features/auth/config";
import { LoginForm } from "@/features/auth/login-form";

export const metadata: Metadata = { title: "Logowanie" };
export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const { error } = await searchParams;
  return (
    <main className="grid min-h-dvh place-items-center bg-canvas px-5 py-12">
      <section
        className="w-full max-w-md rounded-card border bg-surface p-7 shadow-sm compact:p-10"
        aria-labelledby="login-heading"
      >
        <div className="mb-10 flex items-center gap-3">
          <Brand />
        </div>
        <p className="eyebrow text-primary">Oceny i rozwój kompetencji</p>
        <h1 id="login-heading" className="mt-3 text-3xl font-semibold tracking-tight">
          Twoja przestrzeń
          <br />
          do rozwoju.
        </h1>
        <p className="mt-4 text-body leading-relaxed text-muted-foreground">
          Zaloguj się kontem nadanym przez administratora, aby przejść do przestrzeni roboczej.
        </p>
        <LoginForm
          configured={Boolean(authConfig())}
          initialError={error === "account" ? "Konto nie ma aktywnego dostępu do OcenoMat." : ""}
        />
        <p className="mt-7 border-t pt-5 text-caption leading-relaxed text-subtle-foreground">
          Nie masz dostępu? Skontaktuj się z administratorem. Samodzielna rejestracja jest
          wyłączona.
        </p>
      </section>
    </main>
  );
}
