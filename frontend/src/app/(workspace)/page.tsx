import { Dashboard } from "@/features/dashboard/dashboard";
import { requireUser } from "@/features/auth/session";
import { getMonitoring } from "@/features/monitoring/server";

export default async function HomePage() {
  const user = await requireUser();
  const monitoring = await getMonitoring("personal");
  return (
    <Dashboard
      canCreate={user.roles.includes("MANAGER")}
      displayName={user.display_name}
      monitoring={monitoring}
      isHr={user.roles.includes("HR")}
    />
  );
}
