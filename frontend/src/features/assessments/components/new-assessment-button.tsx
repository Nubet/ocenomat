import { ButtonLink } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";

export function NewAssessmentButton({
  employeeId,
  compact = false,
}: {
  employeeId?: string;
  compact?: boolean;
}) {
  const href = employeeId
    ? `/assessments/new?employee_id=${encodeURIComponent(employeeId)}`
    : "/assessments/new";
  return (
    <ButtonLink href={href} variant={compact ? "ghost" : "primary"}>
      <Icon name="plus" size={16} />
      Nowa ocena
    </ButtonLink>
  );
}
