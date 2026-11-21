import { AppShell } from "@/components/layout/app-shell";
import { WorkspaceProvider } from "@/features/workspace/workspace-provider";
import { requireUser } from "@/features/auth/session";

export const dynamic = "force-dynamic";

export default async function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser();
  return (
    <WorkspaceProvider>
      <AppShell user={user}>{children}</AppShell>
    </WorkspaceProvider>
  );
}
