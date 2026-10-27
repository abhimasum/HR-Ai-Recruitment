import axios from "axios";

export const api = axios.create({ baseURL: "/api/v1", withCredentials: true });

export interface AuthAccount {
  id: number;
  username: string;
  role: "candidate" | "hr";
}

export type ScreeningStatus =
  | "AUTO_ACCEPTED"
  | "PENDING_HUMAN_REVIEW"
  | "AUTO_REJECTED"
  | "HR_APPROVED"
  | "HR_REJECTED";

export interface Candidate {
  id: number;
  name: string;
  job_id: number | null;
  job_title: string | null;
  score: number;
  status: ScreeningStatus;
  reasoning: string;
  geval_score: number | null;
  hallucination_score: number | null;
  bias_score: number | null;
}

export interface JobSummary {
  id: number;
  title: string;
  is_active: boolean;
  application_count: number;
  average_match_percent: number | null;
}

export interface Job {
  id: number;
  title: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface PolicyAnswer {
  answer: string;
  sources: string[];
  grounded: boolean;
}
