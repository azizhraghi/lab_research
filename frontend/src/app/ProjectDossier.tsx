import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth, useLabPermissions } from "../auth/AuthContext";
import { apiFetch } from "../lib/apiClient";
import { ResearchEvidence, type EvidenceData } from "./ResearchEvidence";

type Reference = {id:string; title:string; url:string; doi:string|null; rationale:string; evidence_basis:string; evidence_excerpt?:string|null; captured_at?:string};
type Dossier = Omit<EvidenceData, "references"> & {questions:string; approach:string; findings:string; limitations:string; references:Reference[]};
type Review = {id:string; topic:string; items:{id:string;title:string;decision:string}[]};
const fields = [["questions","Research questions"],["approach","Approach and methods"],["findings","Findings and conclusions"],["limitations","Limitations and missing evidence"]] as const;
const inputClass = "w-full rounded-lg border border-border bg-background p-3 text-sm";

function DossierEditor({data,refresh}:{data:Dossier;refresh:()=>void}) {
  const {canWrite}=useLabPermissions();
  const {user}=useAuth();
  const cache=useQueryClient();
  const [draft,setDraft]=useState({questions:data.questions,approach:data.approach,findings:data.findings,limitations:data.limitations});
  const [choice,setChoice]=useState("");
  const [rationale,setRationale]=useState("");
  const [exportError,setExportError]=useState("");
  const [exporting,setExporting]=useState(false);
  const dirty=fields.some(([key])=>draft[key]!==data[key]);
  const path=`/api/mis/projets/${data.project_id}/dossier`;
  const queryKey=["project-dossier",user?.id,data.project_id];
  const reviews=useQuery<Review[]>({queryKey:["literature-reviews",user?.id],enabled:canWrite&&!!user,queryFn:()=>apiFetch("/api/veille/research/reviews")});
  const choices=(reviews.data??[]).flatMap(review=>review.items.filter(item=>item.decision==="include").map(item=>({reviewId:review.id,itemId:item.id,label:`${review.topic} — ${item.title}`})));
  const selected=choices.find(item=>`${item.reviewId}/${item.itemId}`===choice);
  const change=useMutation({mutationFn:({method,suffix,body}:{method:string;suffix?:string;body?:object})=>apiFetch<Dossier>(path+(suffix??""),{method,body:body?JSON.stringify(body):undefined}),
    onSuccess:result=>cache.setQueryData(queryKey,result)});
  async function download(){
    setExportError("");setExporting(true);
    try {
      const result=await apiFetch<{filename:string;content:string}>(path+"/export");
      const url=URL.createObjectURL(new Blob([result.content],{type:"text/html;charset=utf-8"}));
      const a=document.createElement("a");a.href=url;a.download=result.filename;a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(error){setExportError(error instanceof Error?error.message:String(error));}
    finally{setExporting(false);}
  }
  return <div className="space-y-4">
    <p className="text-xs text-muted-foreground">Saved revision {data.revision}. Shared with internal laboratory users who can access projects. Author-entered findings require scientific review.</p>
    <form className="space-y-3" onSubmit={event=>{event.preventDefault();change.mutate({method:"PUT",body:{revision:data.revision,...draft}});}}>
      {fields.map(([key,label])=><label key={key} className="block text-sm font-semibold">{label}<textarea className={inputClass} rows={3} value={draft[key]} maxLength={key==="findings"?20000:12000} disabled={!canWrite||change.isPending} onChange={event=>setDraft({...draft,[key]:event.target.value})}/></label>)}
      <button disabled={!canWrite||change.isPending||!dirty} className="rounded-xl bg-primary text-primary-foreground px-4 py-2 disabled:opacity-50">{change.isPending?"Saving…":"Save dossier"}</button>
      <span role="status" className="ml-3 text-xs">{dirty?"Unsaved changes":"All displayed text is saved"}</span>
    </form>
    {change.isError&&<div role="alert" className="text-sm text-destructive">{change.error.message}<button className="ml-3 underline" onClick={refresh}>Reload saved version (discards local edits)</button></div>}
    <h4 className="font-semibold">Selected literature · {data.references.length}</h4>
    <p className="text-xs text-muted-foreground">Add an included paper from your Scientific Watch reviews. This shares its citation, source excerpt and the project relevance you enter below. Your private screening annotations are not copied. The saved citation remains unchanged if you later edit the review.</p>
    {data.references.map(ref=><article key={ref.id} className="border border-border rounded-xl p-3 space-y-2"><p className="font-semibold text-sm">{ref.title}</p><p className="text-xs break-all">{ref.url}{ref.doi&&` · DOI: ${ref.doi}`} · {ref.evidence_basis}</p><p className="text-sm whitespace-pre-wrap">{ref.rationale}</p><details><summary className="cursor-pointer text-sm">Inspect captured evidence</summary><p className="text-sm whitespace-pre-wrap">{ref.evidence_excerpt||'No abstract excerpt was available. Check the original publication.'}</p><p className="text-xs">Captured {ref.captured_at||'date unavailable'} · source excerpt, not independent appraisal</p><p className="text-xs">Cited by {data.claims.filter(c=>c.reference_ids.includes(ref.id)).length} findings</p></details><button disabled={!canWrite||dirty||change.isPending} onClick={()=>change.mutate({method:"DELETE",suffix:`/references/${ref.id}?revision=${data.revision}`})} className="text-xs underline disabled:opacity-50">Remove from dossier</button></article>)}
    {!data.references.length&&<p className="text-sm text-muted-foreground">No papers linked yet.</p>}
    {canWrite&&<form className="space-y-2" onSubmit={event=>{event.preventDefault();if(selected)change.mutate({method:"POST",suffix:"/references",body:{revision:data.revision,review_id:selected.reviewId,item_id:selected.itemId,rationale}});}}>
      <label className="block text-sm">Included paper<select className={inputClass} required value={choice} disabled={change.isPending||dirty} onChange={event=>setChoice(event.target.value)}><option value="">Choose from your included literature</option>{choices.map(item=><option key={`${item.reviewId}/${item.itemId}`} value={`${item.reviewId}/${item.itemId}`}>{item.label}</option>)}</select></label>
      <label className="block text-sm">How does this paper support the project?<textarea className={inputClass} rows={2} required minLength={3} maxLength={3000} value={rationale} disabled={change.isPending||dirty} onChange={event=>setRationale(event.target.value)}/></label>
      <button disabled={dirty||!selected||change.isPending} className="rounded-xl border px-4 py-2 disabled:opacity-50">Add paper to shared dossier</button>
      {reviews.isError&&<p role="alert" className="text-destructive text-sm">{reviews.error.message}</p>}
      {!reviews.isLoading&&!reviews.isError&&!choices.length&&<p className="text-xs text-muted-foreground">Include a paper in a Scientific Watch literature review first.</p>}
    </form>}
    {dirty&&<p className="text-xs text-muted-foreground">Save the narrative before changing references or exporting.</p>}
    <div className="border-t pt-3"><button onClick={download} disabled={dirty||change.isPending||exporting} className="rounded-xl border px-4 py-2 disabled:opacity-50">{exporting?"Preparing report…":"Export readable dossier (HTML)"}</button><p className="mt-2 text-xs text-muted-foreground">Includes saved research text, references and current milestones, deliverables, risks and outstanding work. Open the downloaded file in a browser to read or print it. It is a working report, not a signed approval.</p></div>
    {exportError&&<p role="alert" className="text-destructive text-sm">{exportError}</p>}
    <ResearchEvidence data={data} disabled={dirty||change.isPending}/>
  </div>;
}

export function ProjectDossier({projectId}:{projectId:string}) {
  const {user}=useAuth();
  const dossier=useQuery<Dossier>({queryKey:["project-dossier",user?.id,projectId],enabled:!!user,staleTime:Infinity,
    queryFn:()=>apiFetch(`/api/mis/projets/${projectId}/dossier`)});
  return <section className="p-5 border-t border-border space-y-4"><h3 className="text-lg font-bold">Project research dossier</h3>
    {dossier.isLoading&&<p role="status">Loading dossier…</p>}
    {dossier.isError&&<p role="alert" className="text-destructive">{dossier.error.message}</p>}
    {dossier.data&&<DossierEditor key={`${user?.id}-${projectId}-${dossier.data.revision}`} data={dossier.data} refresh={()=>void dossier.refetch()}/>}
  </section>;
}
