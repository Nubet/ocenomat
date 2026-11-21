import type { Metadata } from "next";
import { HrOverview } from "@/features/hr/hr-overview";
import { notFound } from "next/navigation";
import { requireUser } from "@/features/auth/session";
export const metadata: Metadata = { title: "Panel HR" };
export default async function HrPage() {
  const user = await requireUser();
  if (!user.roles.includes("HR")) notFound();
  return <HrOverview />;
}
