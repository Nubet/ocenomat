import type { Metadata } from "next";
import { Deadlines } from "@/features/deadlines/deadlines";
export const metadata: Metadata = { title: "Terminy" };
export default function DeadlinesPage() {
  return <Deadlines />;
}
