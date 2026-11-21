import type { IconName } from "@/components/ui/icon";

export const navigation: { href: string; label: string; icon: IconName }[] = [
  { href: "/", label: "Pulpit", icon: "grid" },
  { href: "/assessments", label: "Oceny", icon: "file-check" },
  { href: "/employees", label: "Pracownicy", icon: "users" },
  { href: "/deadlines", label: "Terminy", icon: "calendar" },
  { href: "/help", label: "Pomoc", icon: "help" },
];

export const processNavigation = [
  { step: "setup", label: "Rozpoczęcie" },
  { step: "analysis", label: "Analiza OSP" },
  { step: "criteria", label: "Kryteria" },
  { step: "timing", label: "Terminy" },
  { step: "period", label: "Okres oceny" },
  { step: "conversation", label: "Rozmowa" },
  { step: "rating", label: "Ocena zachowań" },
  { step: "summary", label: "Podsumowanie" },
  { step: "document", label: "Dokumentacja" },
] as const;
