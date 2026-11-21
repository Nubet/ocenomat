"use server";

import { unstable_rethrow } from "next/navigation";
import { getEmployeePage } from "./server";
import type { EmployeeRecord } from "./types";

export async function searchEmployees(query: string): Promise<{
  items: EmployeeRecord[];
  total: number;
  error?: string;
}> {
  if (typeof query !== "string" || query.length > 100) {
    return { items: [], total: 0, error: "Wpisz frazę do 100 znaków." };
  }
  try {
    const result = await getEmployeePage({ q: query.trim(), page_size: 8 });
    return { items: result.items, total: result.total };
  } catch (error) {
    unstable_rethrow(error);
    return { items: [], total: 0, error: "Nie udało się wyszukać pracowników. Spróbuj ponownie." };
  }
}
