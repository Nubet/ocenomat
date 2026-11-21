import { unstable_rethrow } from "next/navigation";
import { apiRequest } from "@/lib/api/server";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ assessmentId: string; documentId: string }> },
) {
  const { assessmentId, documentId } = await params;
  const osp = new URL(request.url).searchParams.get("osp") === "1";
  const headers = new Headers({
    "Cache-Control": "private, no-store",
    "X-Content-Type-Options": "nosniff",
  });
  try {
    const response = await apiRequest(
      `/api/v1/assessments/${encodeURIComponent(assessmentId)}/documents/${osp ? "job-descriptions/" : ""}${encodeURIComponent(documentId)}/download`,
    );
    if (!response.ok)
      return new Response(
        response.status === 404
          ? "Nie masz dostępu do dokumentu lub dokument nie istnieje."
          : "Nie udało się pobrać dokumentu. Spróbuj ponownie za chwilę.",
        { status: response.status, headers },
      );
    headers.set("Content-Type", response.headers.get("Content-Type") ?? "application/octet-stream");
    headers.set("Content-Disposition", response.headers.get("Content-Disposition") ?? "attachment");
    return new Response(response.body, { headers });
  } catch (error) {
    unstable_rethrow(error);
    return new Response("Pobranie dokumentu jest chwilowo niedostępne.", { status: 503, headers });
  }
}
