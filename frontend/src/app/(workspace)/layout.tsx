import { AppShell } from "@/components/layout/app-shell";
import { WorkspaceProvider } from "@/features/workspace/workspace-provider";
import { requireUser } from "@/features/auth/session";
import { getEmployees } from "@/features/employees/server";

export const dynamic = "force-dynamic";

export default async function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const [user, employees] = await Promise.all([requireUser(), getEmployees()]);
  return (
    <WorkspaceProvider>
      <AppShell user={user} employees={employees}>
        {children}
      </AppShell>
    </WorkspaceProvider>
  );
}
