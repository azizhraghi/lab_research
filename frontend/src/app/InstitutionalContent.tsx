import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import { useLabPermissions } from "../auth/AuthContext";

type Kind = "news" | "events" | "theses";
type Status = "draft" | "published" | "withdrawn";
type Entry = { id: string; kind: Kind; title: string; body: string; details: Record<string, string>; status: Status; published_at: string | null };
const names = { news: "News & updates", events: "Events & conferences", theses: "Theses & masters" };
const inputStyle = "w-full rounded-xl border border-border bg-background p-3 text-sm";

export function InstitutionalContent({ kind, publicOnly = false }: { kind: Kind; publicOnly?: boolean }) {
  const { isAdministrator } = useLabPermissions();
  const manage = isAdministrator && !publicOnly;
  const cache = useQueryClient();
  const [editing, setEditing] = useState<Entry | null | undefined>(undefined);
  const [message, setMessage] = useState("");
  const query = useQuery<Entry[]>({
    queryKey: ["institutional-content", kind, manage],
    queryFn: () => apiFetch(`/api/public/${manage ? "admin/" : ""}content?kind=${kind}`),
  });
  const mutation = useMutation({
    mutationFn: ({ path, method, body }: { path: string; method: string; body: object }) =>
      apiFetch<Entry>(`/api/public/admin/content${path}`, { method, body: JSON.stringify(body) }),
    onSuccess: async (saved) => {
      // Remove withdrawn/edited records from the cached public view immediately.
      // Invalidation alone can briefly show the previous publication on return.
      cache.setQueryData<Entry[]>(["institutional-content", kind, false], previous => {
        if (!previous) return previous;
        const remaining = previous.filter(item => item.id !== saved.id);
        return saved.status === "published" ? [saved, ...remaining] : remaining;
      });
      await cache.invalidateQueries({ queryKey: ["institutional-content"], refetchType: "all" });
      setEditing(undefined);
      setMessage("Changes saved.");
    },
  });
  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget));
    const body = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ""));
    mutation.mutate({ path: editing ? `/${editing.id}` : "", method: editing ? "PUT" : "POST", body: { ...body, kind } });
  }
  function field(name: string, label: string, type = "text", required = false) {
    const initial = name === "title" ? editing?.title : editing?.details[name];
    return <label className="block text-sm font-medium">{label}<input name={name} type={type} required={required} defaultValue={initial ?? ""} className={inputStyle} maxLength={name === "title" ? 240 : 300} /></label>;
  }
  return <section className={`space-y-5 ${publicOnly ? "" : "p-4 sm:p-6"}`}>
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-bold">{names[kind]}</h2><p className="text-sm text-muted-foreground">{manage ? "Draft, review and publish laboratory content." : "Published laboratory records."}</p></div>
      {manage && <button className="rounded-xl bg-primary px-4 py-2 text-primary-foreground" onClick={() => { mutation.reset(); setMessage(""); setEditing(null); }}>New {kind === "theses" ? "thesis" : kind === "events" ? "event" : "announcement"}</button>}
    </div>
    {message && <p role="status" className="text-sm text-primary">{message}</p>}
    {mutation.isError && <p role="alert" className="text-sm text-destructive">{mutation.error.message}</p>}
    {manage && editing !== undefined && <form key={editing?.id ?? "new"} onSubmit={save} className="space-y-4 rounded-2xl border border-border bg-card p-5">
      <h3 className="font-bold">{editing ? "Edit content" : "New draft"}</h3>
      <p className="text-sm text-muted-foreground">Saving returns this record to draft and removes it from public display until you publish it again.</p>
      {field("title", "Title", "text", true)}
      <label className="block text-sm font-medium">Content<textarea name="body" required minLength={20} maxLength={20000} defaultValue={editing?.body ?? ""} rows={6} className={inputStyle} /></label>
      {kind === "events" && <div className="grid sm:grid-cols-2 gap-4">{field("event_date", "Start date", "date", true)}{field("end_date", "End date", "date")}{field("location", "Location or online venue", "text", true)}</div>}
      {kind === "theses" && <div className="grid sm:grid-cols-2 gap-4">{field("author", "Author", "text", true)}{field("supervisor", "Supervisor", "text", true)}<label className="text-sm font-medium">Degree<select name="degree" defaultValue={editing?.details.degree ?? "Masters"} className={inputStyle}><option>Masters</option><option>PhD</option></select></label>{field("defense_date", "Defence date", "date")}</div>}
      {field("link", kind === "theses" ? "Repository URL (optional)" : "Further information URL (optional)", "url")}
      <div className="flex gap-3"><button disabled={mutation.isPending} className="rounded-xl bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">{mutation.isPending ? "Saving…" : "Save draft"}</button><button type="button" onClick={() => setEditing(undefined)} className="rounded-xl border px-4 py-2">Cancel</button></div>
    </form>}
    {query.isLoading && <p role="status">Loading…</p>}
    {query.isError && <div role="alert"><p>{query.error.message}</p><button onClick={() => query.refetch()} className="text-primary">Retry</button></div>}
    {!query.isLoading && !query.isError && !query.data?.length && <p className="rounded-2xl border border-dashed border-border p-6 text-sm text-muted-foreground">{manage ? "No records yet. Create a draft to begin." : "No records have been published yet."}</p>}
    <div className="grid md:grid-cols-2 gap-4">{query.data?.map(item => <article key={item.id} className="rounded-2xl border border-border bg-card p-5 space-y-3">
      {manage && <p className="text-xs font-bold uppercase text-primary">{item.status}</p>}
      <h3 className="font-bold text-lg">{item.title}</h3>
      {kind === "events" && <p className="text-sm text-primary">{item.details.event_date}{item.details.end_date ? ` – ${item.details.end_date}` : ""} · {item.details.location}</p>}
      {kind === "theses" && <p className="text-sm text-primary">{item.details.degree} · {item.details.author}<br />Supervisor: {item.details.supervisor}{item.details.defense_date && <><br />Defence: {item.details.defense_date}</>}</p>}
      <p className="whitespace-pre-wrap break-words text-sm leading-6 text-muted-foreground">{item.body}</p>
      {item.details.link && <a className="inline-block text-sm font-semibold text-primary" href={item.details.link} target="_blank" rel="noreferrer">{kind === "theses" ? "View repository record" : "Further information"} ↗</a>}
      {manage && <div className="flex flex-wrap gap-3 text-sm"><button disabled={mutation.isPending} onClick={() => { mutation.reset(); setEditing(item); setMessage(""); }} className="text-primary">Edit</button>{(["published", "withdrawn"] as Status[]).filter(status => status !== item.status).map(status => <button key={status} disabled={mutation.isPending} className="rounded-lg border px-3 py-1 disabled:opacity-50" onClick={() => mutation.mutate({ path: `/${item.id}/status`, method: "PATCH", body: { status } })}>{status === "published" ? "Publish" : "Withdraw"}</button>)}</div>}
    </article>)}</div>
  </section>;
}
