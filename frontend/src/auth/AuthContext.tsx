import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Session } from "@supabase/supabase-js";
import { supabase, isSupabaseConfigured } from "../lib/supabase";
import { setTokenProvider } from "../lib/apiClient";

export type Role = "viewer" | "researcher" | "reviewer" | "administrator";

export interface AuthUser {
  id: string;
  email: string | null;
  role: Role;
}

interface AuthContextValue {
  user: AuthUser | null;
  session: Session | null;
  loading: boolean;
  /** True when Supabase is not configured — auth is bypassed for local dev. */
  devBypass: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const DEV_USER: AuthUser = { id: "dev", email: "dev@local", role: "administrator" };
const VALID_ROLES: Role[] = ["viewer", "researcher", "reviewer", "administrator"];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const devBypass = !isSupabaseConfigured;

  const user: AuthUser | null = useMemo(() => {
    if (devBypass) return DEV_USER;
    if (!session?.user) return null;
    const meta = (session.user.app_metadata ?? {}) as Record<string, unknown>;
    const role = VALID_ROLES.includes(meta.lab_role as Role)
      ? (meta.lab_role as Role)
      : "viewer";
    return { id: session.user.id, email: session.user.email ?? null, role };
  }, [session, devBypass]);

  useEffect(() => {
    if (!supabase) {
      setLoading(false);
      return;
    }
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  // Feed the current Supabase session token to the API client.
  useEffect(() => {
    setTokenProvider(async () => {
      if (supabase) {
        const { data } = await supabase.auth.getSession();
        return data.session?.access_token ?? null;
      }
      return null; // dev bypass: backend DISABLE_AUTH ignores the token
    });
  }, []);

  const signIn = async (email: string, password: string) => {
    if (!supabase) return; // dev bypass: already signed in
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  };

  const signUp = async (email: string, password: string) => {
    if (!supabase) return;
    const { error } = await supabase.auth.signUp({ email, password });
    if (error) throw error;
  };

  const signOut = async () => {
    if (supabase) await supabase.auth.signOut();
    setSession(null);
  };

  const value: AuthContextValue = {
    user,
    session,
    loading,
    devBypass,
    signIn,
    signUp,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}

export function useLabPermissions() {
  const { user } = useAuth();
  return {
    canWrite: !!user && user.role !== "viewer",
    canReview: user?.role === "reviewer" || user?.role === "administrator",
    isAdministrator: user?.role === "administrator",
  };
}
