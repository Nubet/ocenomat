import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Kompas Kompetencji", template: "%s | Kompas Kompetencji" },
  description:
    "Kompas Kompetencji — interaktywny proces pierwszej i okresowej oceny w służbie cywilnej. Wersja demonstracyjna.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pl">
      <body>{children}</body>
    </html>
  );
}
