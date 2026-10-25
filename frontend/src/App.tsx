import { useState } from "react";
import { Briefcase, Shield } from "lucide-react";
import CandidateView from "./components/CandidateView";
import HRPortal from "./components/HRPortal";

type View = "candidate" | "hr";

export default function App() {
  const [view, setView] = useState<View>("candidate");

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="font-semibold text-lg">AI HR Recruitment</span>
          <nav className="flex gap-2">
            <button
              onClick={() => setView("candidate")}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm ${view === "candidate" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              <Briefcase size={16} /> Candidate
            </button>
            <button
              onClick={() => setView("hr")}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm ${view === "hr" ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              <Shield size={16} /> HR Portal
            </button>
          </nav>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-6">
        {view === "candidate" ? <CandidateView /> : <HRPortal />}
      </main>
    </div>
  );
}
