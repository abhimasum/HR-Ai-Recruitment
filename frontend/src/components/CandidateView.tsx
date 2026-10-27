import { useRef, useState, DragEvent, FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload, Send, Bot, User } from "lucide-react";
import { api, Candidate, Job, PolicyAnswer } from "../api";

const PROMPT_CHIPS = [
  "What is the remote work policy?",
  "How many paid leaves do I get?",
  "What are the recruitment stages?",
];

type Tab = "apply" | "applications" | "chat";

export default function CandidateView() {
  const [tab, setTab] = useState<Tab>("apply");

  return (
    <div>
      <div className="flex gap-2 mb-4">
        {(["apply", "applications", "chat"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium ${tab === t ? "bg-white shadow border border-slate-200" : "text-slate-500"}`}
          >
            {t === "apply" ? "Apply for a job" : t === "applications" ? "My applications" : "Policy Assistant"}
          </button>
        ))}
      </div>
      {tab === "apply" ? <ApplyPanel /> : tab === "applications" ? <MyApplications /> : <PolicyChat />}
    </div>
  );
}

function ApplyPanel() {
  const queryClient = useQueryClient();
  const [jobId, setJobId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [result, setResult] = useState<Candidate | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: ["jobs", "active"],
    queryFn: async () => (await api.get<Job[]>("/jobs")).data,
  });
  const selectedJob = jobs.find((job) => String(job.id) === jobId) ?? jobs[0];

  const submit = useMutation({
    mutationFn: async () => {
      if (!selectedJob || !file) throw new Error("Select a job and resume before submitting.");
      const form = new FormData();
      form.append("job_id", String(selectedJob.id));
      form.append("resume", file);
      const { data } = await api.post<Candidate>("/screening/resume", form);
      return data;
    },
    onSuccess: (candidate) => {
      setResult(candidate);
      void queryClient.invalidateQueries({ queryKey: ["my-applications"] });
    },
  });

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Position</label>
          <select
            className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm"
            value={selectedJob ? String(selectedJob.id) : ""}
            onChange={(e) => setJobId(e.target.value)}
            disabled={isLoading || jobs.length === 0}
          >
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>{job.title}</option>
            ))}
          </select>
          {isError && <p className="text-xs text-red-600 mt-1">Could not load open positions.</p>}
          {!isLoading && !isError && jobs.length === 0 && (
            <p className="text-xs text-slate-500 mt-1">There are no open positions right now.</p>
          )}
        </div>
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${dragging ? "border-indigo-500 bg-indigo-50" : "border-slate-300"}`}
        >
          <Upload className="mx-auto mb-2 text-slate-400" />
          <p className="text-sm">{file ? file.name : "Drag and drop your resume (PDF, DOCX, TXT)"}</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </div>
        <button
          disabled={!file || !selectedJob || submit.isPending}
          onClick={() => submit.mutate()}
          className="w-full bg-indigo-600 text-white rounded-md py-2 text-sm font-medium disabled:opacity-40"
        >
          {submit.isPending ? "Screening..." : "Submit application"}
        </button>
        {submit.isError && (
          <p className="text-sm text-red-600">
            {submit.error instanceof Error ? submit.error.message : "Submission failed. Please try again."}
          </p>
        )}
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5">
        {result ? (
          <div className="space-y-2 text-sm">
            <p className="font-semibold">Your application for {result.job_title} was received.</p>
            <p className="text-slate-600">Resume match: {result.score}%</p>
            <p className="text-slate-600">
              {result.status === "AUTO_REJECTED"
                ? "Based on this screening, your profile does not match this role at this time."
                : "Your application is in progress. The HR team will be in touch."}
            </p>
          </div>
        ) : (
          <p className="text-sm text-slate-500">Your screening status will appear here after you submit.</p>
        )}
      </div>
    </div>
  );
}

function MyApplications() {
  const { data: applications = [], isLoading, isError } = useQuery({
    queryKey: ["my-applications"],
    queryFn: async () => (await api.get<Candidate[]>("/screening/me")).data,
  });

  if (isLoading) return <p className="text-sm text-slate-500">Loading your applications...</p>;
  if (isError) return <p className="text-sm text-red-600">Could not load your applications. Please try again.</p>;
  if (applications.length === 0) {
    return <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">You have not applied to any positions yet.</p>;
  }
  return (
    <div className="space-y-3">
      {applications.map((application) => (
        <article key={application.id} className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex flex-wrap justify-between gap-2">
            <h2 className="font-semibold">{application.job_title ?? "Position no longer available"}</h2>
            <span className="text-sm font-medium">Resume match: {application.score}%</span>
          </div>
          <p className="mt-1 text-sm text-slate-600">{application.status.replace(/_/g, " ")}</p>
          <p className="mt-2 text-sm text-slate-600">{application.reasoning}</p>
        </article>
      ))}
    </div>
  );
}

interface Message {
  role: "user" | "bot";
  text: string;
  sources?: string[];
}

function PolicyChat() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "bot", text: "Hi! Ask me about leave, remote work, benefits, interviews, or life at the company." },
  ]);
  const [input, setInput] = useState("");

  const ask = useMutation({
    mutationFn: async (question: string) => {
      const { data } = await api.post<PolicyAnswer>("/chat/policy", { question });
      return data;
    },
    onSuccess: (data) =>
      setMessages((m) => [...m, { role: "bot", text: data.answer, sources: data.sources }]),
    onError: () =>
      setMessages((m) => [...m, { role: "bot", text: "Sorry, something went wrong. Please try again." }]),
  });

  const send = (question: string) => {
    const q = question.trim();
    if (!q || ask.isPending) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    ask.mutate(q);
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 flex flex-col h-[520px]">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "bot" && <Bot size={18} className="text-indigo-600 mt-1 shrink-0" />}
            <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "bg-indigo-600 text-white" : "bg-slate-100"}`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.sources && m.sources.length > 0 && (
                <p className="text-xs text-slate-500 mt-1">Sources: {m.sources.join(", ")}</p>
              )}
            </div>
            {m.role === "user" && <User size={18} className="text-slate-500 mt-1 shrink-0" />}
          </div>
        ))}
        {ask.isPending && <p className="text-xs text-slate-400">Thinking...</p>}
      </div>

      <div className="px-4 pb-2 flex flex-wrap gap-2">
        {PROMPT_CHIPS.map((chip) => (
          <button
            key={chip}
            onClick={() => send(chip)}
            className="text-xs border border-indigo-200 text-indigo-700 rounded-full px-3 py-1 hover:bg-indigo-50"
          >
            {chip}
          </button>
        ))}
      </div>

      <form onSubmit={onSubmit} className="border-t border-slate-200 p-3 flex gap-2">
        <input
          className="flex-1 border border-slate-300 rounded-md px-3 py-2 text-sm"
          placeholder="Ask about company policies..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button type="submit" className="bg-indigo-600 text-white rounded-md px-3 disabled:opacity-40" disabled={ask.isPending}>
          <Send size={16} />
        </button>
      </form>
    </div>
  );
}
