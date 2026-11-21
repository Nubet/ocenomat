import type { components } from "@/lib/api/schema";

export type Monitoring = components["schemas"]["MonitoringResponse"];
export type MonitoredProcess = components["schemas"]["MonitoringProcess"];

export const deadlineLabels = {
  introduction: "Rozmowa wstępna",
  report: "Złożenie sprawozdania",
  assessment: "Sporządzenie oceny",
};

export function monitoringDate(value: string | null | undefined) {
  return value
    ? new Date(value).toLocaleDateString("pl-PL", { timeZone: "Europe/Warsaw" })
    : "Nie ustalono";
}
