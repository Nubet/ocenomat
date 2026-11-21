import type { Metadata } from "next";
import { HrOverview } from "@/features/hr/hr-overview";
export const metadata: Metadata = { title: "Panel HR" };
export default function HrPage() {
  return <HrOverview />;
}
