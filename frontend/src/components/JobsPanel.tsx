import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Job } from "../api";

type JobForm = Pick<Job, "title" | "description" | "is_active">;

const emptyForm: JobForm = { title: "", description: "", is_active: true };

export default function JobsPanel() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<JobForm>(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: ["jobs", "all"],
    queryFn: async () => (await api.get<Job[]>("/jobs", { params: { active_only: false } })).data,
  });

  const save = useMutation({
    mutationFn: async (payload: JobForm) => {
      if (editingId === null) {
        await api.post("/jobs", payload);
      } else {
        await api.put(`/jobs/${editingId}`, payload);
      }
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setForm(emptyForm);
      setEditingId(null);
    },
  });

  const setActive = useMutation({
    mutationFn: (job: Job) =>
      api.put(`/jobs/${job.id}`, {
        title: job.title,
        description: job.description,
        is_active: !job.is_active,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    save.mutate(form);
  };

  const edit = (job: Job) => {
    setEditingId(job.id);
    setForm({ title: job.title, description: job.description, is_active: job.is_active });
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)]">
      <form onSubmit={onSubmit} className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
        <h2 className="font-semibold">{editingId === null ? "Create a job" : "Edit job"}</h2>
        <label className="block text-sm">
          Title
          <input
            required
            minLength={2}
            maxLength={200}
            className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2"
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
        </label>
        <label className="block text-sm">
          Job description
          <textarea
            required
            minLength={20}
            maxLength={20000}
            rows={7}
            className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
          />
        </label>
        <label className="flex gap-2 items-center text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
          />
          Open for applications
        </label>
        {save.isError && (
          <p className="text-sm text-red-600">
            {save.error instanceof Error ? save.error.message : "Could not save this job."}
          </p>
        )}
        <div className="flex gap-2">
          <button
            disabled={save.isPending}
            className="bg-indigo-600 text-white rounded-md px-4 py-2 text-sm disabled:opacity-50"
          >
            {save.isPending ? "Saving..." : editingId === null ? "Create job" : "Save changes"}
          </button>
          {editingId !== null && (
            <button
              type="button"
              onClick={() => { setEditingId(null); setForm(emptyForm); }}
              className="border border-slate-300 rounded-md px-4 py-2 text-sm"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-100 font-semibold">Positions</div>
        {isLoading && <p className="p-4 text-sm text-slate-500">Loading jobs...</p>}
        {isError && <p className="p-4 text-sm text-red-600">Could not load jobs. Please try again.</p>}
        {!isLoading && !isError && jobs.length === 0 && (
          <p className="p-4 text-sm text-slate-500">No positions have been created.</p>
        )}
        <ul className="divide-y divide-slate-100">
          {jobs.map((job) => (
            <li key={job.id} className="p-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-medium">{job.title}</p>
                <p className="mt-1 text-sm text-slate-600 line-clamp-2">{job.description}</p>
                <span className={`mt-2 inline-block rounded-full px-2 py-0.5 text-xs ${job.is_active ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                  {job.is_active ? "Open" : "Archived"}
                </span>
              </div>
              <div className="flex gap-2">
                <button onClick={() => edit(job)} className="text-sm text-indigo-700">Edit</button>
                <button
                  disabled={setActive.isPending}
                  onClick={() => setActive.mutate(job)}
                  className="text-sm text-slate-600 disabled:opacity-50"
                >
                  {job.is_active ? "Archive" : "Reopen"}
                </button>
              </div>
            </li>
          ))}
        </ul>
        {setActive.isError && <p className="p-4 text-sm text-red-600">Could not update this job.</p>}
      </div>
    </div>
  );
}
