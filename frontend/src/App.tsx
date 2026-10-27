import { FormEvent, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Briefcase, LogOut, Shield } from "lucide-react";
import { api, AuthAccount } from "./api";
import CandidateView from "./components/CandidateView";
import HRPortal from "./components/HRPortal";

function Login({ onLogin }: { onLogin: (account: AuthAccount) => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const { data } = await api.post<AuthAccount>("/auth/login", { username, password });
      onLogin(data);
    } catch {
      setError("Sign in failed. Check your username and password.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <form onSubmit={submit} className="w-full max-w-sm bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div>
          <h1 className="text-xl font-semibold">AI HR Recruitment</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to continue.</p>
        </div>
        <label className="block text-sm">
          Username
          <input
            required
            autoComplete="username"
            className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            required
            type="password"
            autoComplete="current-password"
            className="mt-1 w-full border border-slate-300 rounded-md px-3 py-2"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
        <button
          disabled={submitting}
          className="w-full bg-indigo-600 text-white rounded-md py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}

export default function App() {
  const queryClient = useQueryClient();
  const [account, setAccount] = useState<AuthAccount | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [logoutError, setLogoutError] = useState("");

  useEffect(() => {
    let active = true;
    api.get<AuthAccount>("/auth/me")
      .then(({ data }) => { if (active) setAccount(data); })
      .catch(() => { if (active) setAccount(null); })
      .finally(() => { if (active) setCheckingSession(false); });
    return () => { active = false; };
  }, []);

  const signOut = async () => {
    setLogoutError("");
    try {
      await api.post("/auth/logout");
      queryClient.clear();
      setAccount(null);
    } catch {
      setLogoutError("Could not sign out. Please try again.");
    }
  };

  const signIn = (nextAccount: AuthAccount) => {
    queryClient.clear();
    setAccount(nextAccount);
  };

  if (checkingSession) {
    return <div className="min-h-screen flex items-center justify-center text-sm text-slate-500">Checking session...</div>;
  }
  if (!account) return <Login onLogin={signIn} />;

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <span className="font-semibold text-lg">AI HR Recruitment</span>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">{account.username}</span>
            <span className="flex items-center gap-1 text-sm text-slate-500">
              {account.role === "hr" ? <Shield size={16} /> : <Briefcase size={16} />}
              {account.role === "hr" ? "HR" : "Candidate"}
            </span>
            <button
              onClick={() => { void signOut(); }}
              className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm text-slate-600 hover:bg-slate-100"
            >
              <LogOut size={16} /> Sign out
            </button>
          </div>
        </div>
      </header>
      {logoutError && <p role="alert" className="max-w-5xl mx-auto px-4 pt-3 text-sm text-red-600">{logoutError}</p>}
      <main className="max-w-5xl mx-auto px-4 py-6">
        {account.role === "candidate" ? <CandidateView /> : <HRPortal />}
      </main>
    </div>
  );
}
