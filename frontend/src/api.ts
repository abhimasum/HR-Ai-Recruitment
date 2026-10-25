import axios from "axios";

export const api = axios.create({ baseURL: "/api/v1" });

export type ScreeningStatus =
  | "AUTO_ACCEPTED"
  | "PENDING_HUMAN_REVIEW"
  | "AUTO_REJECTED"
  | "HR_APPROVED"
  | "HR_REJECTED";

export interface Candidate {
  id: number;
  name: string;
  score: number;
  status: ScreeningStatus;
  reasoning: string;
  geval_score: number | null;
  hallucination_score: number | null;
  bias_score: number | null;
}

export interface PolicyAnswer {
  answer: string;
  sources: string[];
  grounded: boolean;
}
