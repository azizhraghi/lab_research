import { useState } from "react";
import { FlaskConical, KeyRound, LoaderCircle } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";

export default function Login() {
  const { configured, signInWithPassword } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    const { error: signInError } = await signInWithPassword(email, password);
    setSubmitting(false);
    if (signInError) {
      setError(signInError.message);
    }
  };

  return (
    <main className="min-h-screen bg-background px-5 py-8 flex items-center justify-center">
      <section className="w-full max-w-md border border-border bg-card shadow-xl shadow-primary/10 p-7 sm:p-8 rounded-lg">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-11 h-11 bg-primary text-white rounded-lg flex items-center justify-center">
            <FlaskConical size={22} />
          </div>
          <div>
            <p className="text-sm font-bold text-foreground">AI Research Laboratory</p>
            <p className="text-xs text-muted-foreground">Platform access</p>
          </div>
        </div>

        <h1 className="text-xl font-bold text-foreground">Sign in</h1>
        <p className="mt-1 text-sm text-muted-foreground">Use your laboratory account.</p>

        {!configured ? (
          <div className="mt-6 border border-destructive/25 bg-destructive/10 text-destructive rounded-lg p-3 text-sm">
            Authentication is not configured for this environment.
          </div>
        ) : (
          <form className="mt-6 grid gap-4" onSubmit={submit}>
            <label className="grid gap-1.5 text-sm text-foreground">
              Email
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                className="h-10 rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </label>
            <label className="grid gap-1.5 text-sm text-foreground">
              Password
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                className="h-10 rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </label>

            {error && (
              <p className="rounded-md border border-destructive/25 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="h-10 rounded-md bg-primary text-sm font-semibold text-primary-foreground disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {submitting ? <LoaderCircle size={16} className="animate-spin" /> : <KeyRound size={16} />}
              {submitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        )}
      </section>
    </main>
  );
}