import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

/** True when both Supabase env vars are provided; false → dev bypass mode. */
export const isSupabaseConfigured = Boolean(url && anonKey);

export const supabase: SupabaseClient | null = isSupabaseConfigured
  ? createClient(url!, anonKey!)
  : null;

if (!isSupabaseConfigured) {
  console.info(
    "[auth] Supabase env vars not set — running in dev bypass mode. " +
      "The backend DISABLE_AUTH flag is expected. Set VITE_SUPABASE_URL and " +
      "VITE_SUPABASE_PUBLISHABLE_KEY to enable real authentication.",
  );
}
