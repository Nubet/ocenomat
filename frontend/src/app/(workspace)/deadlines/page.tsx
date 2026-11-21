import type { Metadata } from "next";
import { Deadlines } from "@/features/deadlines/deadlines";
import { getMonitoring } from "@/features/monitoring/server";
import type { DeadlineParams } from "@/features/deadlines/query";
export const metadata: Metadata = { title: "Terminy" };
export default async function DeadlinesPage({
  searchParams,
}: {
  searchParams: Promise<DeadlineParams>;
}) {
  const [monitoring, params] = await Promise.all([getMonitoring("personal"), searchParams]);
  return <Deadlines monitoring={monitoring} params={params} />;
}
