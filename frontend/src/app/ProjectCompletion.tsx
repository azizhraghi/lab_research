import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import { useLabPermissions } from "../auth/AuthContext";

type Report = {
  project: { id: string; nom: string; statut: string; responsable: string };
  generated_at: string; outstanding: string[];
  milestones: { id: string; title: string; status: string }[];
  deliverables: { id: string; title: string; status: string }[];
  risks: { id: string; title: string; status: string }[];
  staff: { id: string; name: string; role: string }[];
  budgets: { budget_id: string; currency: string; allocated: number; spent: number; committed: number; available: number }[];
};

export function ProjectCompletion({ projectId }: { projectId: string }) {
  const { canWrite, canReview } = useLabPermissions();
  const cache = useQueryClient();
  const report = useQuery<Report>({queryKey: ["mis", "project-operations", projectId, "completion-report"],
    queryFn: () => apiFetch(`/api/mis/projets/${projectId}/completion-report`)});
  const update = useMutation({
    mutationFn: ({ path, status }: { path: string; status: string }) => apiFetch(`/api/mis/${path}`, {method: "PATCH", body: JSON.stringify({status})}),
    onSuccess: async () => { await cache.invalidateQueries({queryKey: ["mis"]}); },
  });
  async function download() {
    const result = await report.refetch();
    if (!result.data || result.isError) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(result.data, null, 2)], {type: "application/json"}));
    const anchor = document.createElement("a"); anchor.href = url; anchor.download = `project-${projectId}-report.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  if (report.isLoading) return <p role="status" className="p-5">Loading project report…</p>;
  if (report.isError) return <p role="alert" className="p-5 text-destructive">{report.error.message}</p>;
  const data = report.data;
  if (!data) return null;
  return <section className="p-5 border-t border-border space-y-4">
    <div className="flex flex-wrap justify-between gap-3"><div><h3 className="font-bold">Project completion & report</h3><p className="text-xs text-muted-foreground">Current project-wide snapshot. Review outstanding work before changing the project status in Edit project.</p></div><button disabled={report.isFetching} onClick={download} className="rounded-xl border px-3 py-2 text-sm">Download report (JSON)</button></div>
    {update.isError && <p role="alert" className="text-sm text-destructive">{update.error.message}</p>}
    <div className="rounded-xl bg-muted p-3 text-sm">{data.outstanding.length ? <ul className="list-disc pl-5">{data.outstanding.map(item => <li key={item}>{item}</li>)}</ul> : "All recorded milestones are complete, deliverables approved, and no open risks or budget overruns are recorded."}</div>
    <div className="grid lg:grid-cols-3 gap-4">{([
      ["Milestones", "milestones", data.milestones, ["pending", "at_risk", "completed"]],
      ["Deliverables", "deliverables", data.deliverables, ["planned", "draft", "submitted", "approved"]],
      ["Risks", "risks", data.risks, ["open", "mitigated", "closed"]],
    ] as const).map(([title, path, rows, statuses]) => <div key={path} className="space-y-2"><h4 className="font-semibold text-sm">{title}</h4>{!rows.length && <p className="text-xs text-muted-foreground">None recorded.</p>}{rows.map(item => <label key={item.id} className="block rounded-xl border border-border p-3 text-sm"><span className="block mb-2">{item.title}</span><select aria-label={`${title}: ${item.title} status`} value={item.status} disabled={!canWrite || update.isPending} onChange={event => update.mutate({path: `${path}/${item.id}`, status: event.target.value})} className="w-full rounded-lg border border-border bg-background p-2">{statuses.map(status => <option key={status} value={status} disabled={status === "approved" && (!canReview || !["submitted", "approved"].includes(item.status))}>{status}</option>)}</select></label>)}</div>)}</div>
    <div className="text-sm"><h4 className="font-semibold">Assigned staff</h4>{data.staff.length ? data.staff.map(item => <p key={item.id}>{item.name} · {item.role}</p>) : <p className="text-muted-foreground">No staff assigned.</p>}</div>
    <div className="space-y-2"><h4 className="font-semibold text-sm">Project budgets</h4>{data.budgets.map(item => <p key={item.budget_id} className="text-sm">{item.currency}: {item.allocated} allocated · {item.spent} spent · {item.committed} committed · {item.available} available</p>)}{!data.budgets.length && <p className="text-sm text-muted-foreground">No budget records.</p>}</div>
  </section>;
}
