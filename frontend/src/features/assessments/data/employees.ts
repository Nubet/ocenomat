import type { Employee, EmployeeId } from "../model/types";

export const employees: readonly Employee[] = [
  {
    id: "jan",
    name: "Jan Kowalski",
    role: "Starszy specjalista",
    department: "Departament Analiz",
    initials: "JK",
    avatar: "primary",
    manager: false,
    osp: "DC WZKSOiC 6",
  },
  {
    id: "maria",
    name: "Maria Wiśniewska",
    role: "Radca",
    department: "Departament Prawny",
    initials: "MW",
    avatar: "peach",
    manager: false,
    osp: "DSI WWI 5",
  },
  {
    id: "alicja",
    name: "Alicja Zielińska",
    role: "Główny specjalista",
    department: "Biuro Organizacji",
    initials: "AZ",
    avatar: "green",
    manager: false,
    osp: "Dane demonstracyjne",
  },
  {
    id: "piotr",
    name: "Piotr Nowak",
    role: "Naczelnik wydziału",
    department: "Wydział Koordynacji",
    initials: "PN",
    avatar: "purple",
    manager: true,
    osp: "DWM WKAM 1",
  },
];

export function findEmployee(id: string): Employee | undefined {
  return employees.find((employee) => employee.id === id);
}

export function assessmentHref(id: EmployeeId, step?: string) {
  return `/assessments/${id}${step ? `?step=${step}` : ""}`;
}
