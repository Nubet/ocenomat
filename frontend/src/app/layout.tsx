import type { Metadata } from "next";
import { AccessibilitySettings } from "@/components/accessibility-settings";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "OcenoMat", template: "%s | OcenoMat" },
  description:
    "OcenoMat — interaktywny proces pierwszej i okresowej oceny w służbie cywilnej. Wersja demonstracyjna.",
  icons: { icon: "/logo-light.svg" },
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="pl">
      <body>
        {children}
        <AccessibilitySettings />
      </body>
    </html>
  );
}
