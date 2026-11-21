import type { Metadata } from "next";
import { Help } from "@/features/help/help";
export const metadata: Metadata = { title: "Pomoc" };
export default function HelpPage() {
  return <Help />;
}
