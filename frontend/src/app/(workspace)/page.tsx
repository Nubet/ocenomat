import { Dashboard } from "@/features/dashboard/dashboard";
import { requireUser } from "@/features/auth/session";

export default async function HomePage() {
  const user = await requireUser();
  return <Dashboard canCreate={user.roles.includes("MANAGER")} displayName={user.display_name} />;
}
