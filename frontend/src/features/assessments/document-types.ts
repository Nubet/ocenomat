import type { components } from "@/lib/api/schema";
import type { AssessmentRecord } from "./types";

export type AssessmentDocument = components["schemas"]["DocumentResponse"];
export type JobDescription = components["schemas"]["JobDescriptionResponse"];

export type DocumentActionState = {
  error: string;
  conflict: boolean;
  message?: string;
  assessment?: AssessmentRecord;
  files?: AssessmentDocument[];
  descriptions?: JobDescription[];
};

export function documentHref(assessmentId: string, id: string, osp = false) {
  return `/assessments/${encodeURIComponent(assessmentId)}/documents/${encodeURIComponent(id)}${osp ? "?osp=1" : ""}`;
}
