import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import { api, Candidate, ScreeningStatus } from "../api";

const STATUS_STYLES: Record<ScreeningStatus, string> = {
  AUTO_ACCEPTED: "bg-emerald-100 text-emerald-700",
  PENDING_HUMAN_REVIEW: "bg-amber-100 text-amber-700",
  AUTO_REJECTED: "bg-red-100 text-red-700",
  HR_APPROVED: "bg-emerald-600 text-white",
  HR_REJECTED: "bg-slate-700 text-white",
};

const fmt = (v: number | null) => (v === null ? "-" : v.toFixed(2));

export default function HRPortal() {
  const queryClient = useQueryClient();
  const { data: candidates = [], isLoading } = useQuery({
    queryKey: ["candidates"],
    queryFn: async () => (await api.get<Candidate[]>("/screening/candidates")).data,
  });

  const decide = useMutation({
    mutationFn: ({ id, action }: { id: number; action: "approve" | "reject" }) =>
      api.post(`/screening/candidates/${id}/decision`, { action }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates"] }),
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading candidates...</p>;

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500">
          <tr>
            <th className="p-3">Candidate</th>
            <th className="p-3">Score</th>
            <th className="p-3">Status</th>
            <th className="p-3">GEval</th>
            <th className="p-3">Hallucination</th>
            <th className="p-3">Bias</th>
            <th className="p-3">Reasoning</th>
            <th className="p-3">HITL</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c) => (
            <tr key={c.id} className="border-t border-slate-100 align-top">
              <td className="p-3 font-medium">{c.name}</td>
              <td className="p-3">{c.score}</td>
              <td className="p-3">
                <span className={`px-2 py-0.5 rounded-full text-xs ${STATUS_STYLES[c.status]}`}>{c.status}</span>
              </td>
              <td className="p-3">{fmt(c.geval_score)}</td>
              <td className="p-3">{fmt(c.hallucination_score)}</td>
              <td className="p-3">{fmt(c.bias_score)}</td>
              <td className="p-3 max-w-xs text-slate-600">{c.reasoning}</td>
              <td className="p-3">
                {c.status === "PENDING_HUMAN_REVIEW" && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => decide.mutate({ id: c.id, action: "approve" })}
                      className="flex items-center gap-1 bg-emerald-600 text-white px-2 py-1 rounded text-xs"
                    >
                      <Check size={14} /> Approve
                    </button>
                    <button
                      onClick={() => decide.mutate({ id: c.id, action: "reject" })}
                      className="flex items-center gap-1 bg-red-600 text-white px-2 py-1 rounded text-xs"
                    >
                      <X size={14} /> Reject
                    </button>
                  </div>
                )}
              </td>
            </tr>
          ))}
          {candidates.length === 0 && (
            <tr>
              <td colSpan={8} className="p-6 text-center text-slate-500">No applications yet.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
