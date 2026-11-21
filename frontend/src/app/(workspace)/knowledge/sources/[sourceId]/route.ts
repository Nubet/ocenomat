import { unstable_rethrow } from "next/navigation";
import { apiRequest } from "@/lib/api/server";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ sourceId: string }> },
) {
  const { sourceId } = await params;
  const headers = new Headers({
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "sandbox; default-src 'none'",
  });
  try {
    const response = await apiRequest(
      `/api/v1/knowledge/sources/${encodeURIComponent(sourceId)}/original`,
    );
    if (!response.ok)
      return new Response(
        response.status === 404
          ? "Źródło nie istnieje lub nie masz do niego dostępu."
          : "Pobranie źródła jest chwilowo niedostępne.",
        { status: response.status, headers },
      );
    headers.set("Content-Type", response.headers.get("Content-Type") ?? "application/octet-stream");
    headers.set("Content-Disposition", response.headers.get("Content-Disposition") ?? "attachment");
    return new Response(response.body, { headers });
  } catch (error) {
    unstable_rethrow(error);
    return new Response("Pobranie źródła jest chwilowo niedostępne.", { status: 503, headers });
  }
}
