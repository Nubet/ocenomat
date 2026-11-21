import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto max-w-xl px-6 py-24">
      <p className="eyebrow">404</p>
      <h1 className="mt-3 text-title font-semibold tracking-heading">Nie znaleziono strony</h1>
      <p className="mt-4 text-body text-muted-foreground">
        Ten widok lub pracownik nie istnieje w wersji demonstracyjnej.
      </p>
      <Link href="/" className="mt-6 inline-block text-body font-semibold text-primary">
        Wróć na pulpit →
      </Link>
    </main>
  );
}
