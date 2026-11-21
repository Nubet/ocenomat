import type { Metadata } from "next";
import { Help } from "@/features/help/help";
import { requireUser } from "@/features/auth/session";
export const metadata: Metadata = { title: "Pomoc" };
export default async function HelpPage() {
  return <Help userRoles={(await requireUser()).roles} />;
}
