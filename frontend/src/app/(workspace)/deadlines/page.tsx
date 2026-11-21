import type { Metadata } from "next";
import { Deadlines } from "@/features/deadlines/deadlines";
import { getMonitoring } from "@/features/monitoring/server";
export const metadata: Metadata = { title: "Terminy" };
export default async function DeadlinesPage() {
  return <Deadlines monitoring={await getMonitoring("personal")} />;
}
