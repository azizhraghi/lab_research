import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import { useAuth, useLabPermissions } from "../auth/AuthContext";
import { ShareReviewedPaper } from './ShareReviewedPaper';

type Item = {id:string;title:string;authors:string[];doi:string|null;url:string;abstract:string|null;evidence_basis:string;evidence_excerpt:string|null;relevance:string;decision:"pending"|"include"|"exclude";note:string};
type Review = {id:string;topic:string;status:string;error_message:string|null;created_at:string;items:Item[]};
const cls="w-full rounded-xl border border-border bg-background p-2 text-sm";

function ReviewItem({item,reviewId}:{item:Item;reviewId:string}) {
  const {canWrite}=useLabPermissions();
  const cache=useQueryClient();
  const [note,setNote]=useState(item.note);
  const [decision,setDecision]=useState(item.decision);
  const [saved,setSaved]=useState(false);
  const mutation=useMutation({mutationFn:()=>apiFetch(`/api/veille/research/reviews/${reviewId}/items/${item.id}`,{method:"PATCH",body:JSON.stringify({decision,note})}),onSuccess:async()=>{await cache.invalidateQueries({queryKey:["literature-reviews"]});setSaved(true);}});
  return <article className="rounded-xl border border-border bg-card p-4 space-y-3">
    <h4 className="font-bold">{item.title}</h4><p className="text-xs text-muted-foreground">{item.authors.join(", ") || "Authors unavailable"}</p>
    <div className="flex flex-wrap gap-3 text-xs"><span className="rounded-full bg-primary/10 px-2 py-1 text-primary">{item.evidence_basis}</span><a className="text-primary underline" href={item.url} target="_blank" rel="noreferrer">Original source ↗</a>{item.doi && <span>DOI: {item.doi}</span>}</div>
    <p className="text-xs text-muted-foreground">{item.relevance}</p>
    <div className="rounded-lg bg-muted p-3"><p className="text-xs font-bold mb-1">Source excerpt · not an AI synthesis</p><p className="whitespace-pre-wrap text-sm leading-6">{item.evidence_excerpt || "No abstract supplied. A scientific summary is unavailable; consult the original publication."}</p></div>
    {item.abstract && <details><summary className="cursor-pointer text-sm text-primary">Read complete retrieved abstract</summary><p className="mt-2 whitespace-pre-wrap text-sm leading-6">{item.abstract}</p></details>}
    <form className="space-y-2" onSubmit={event=>{event.preventDefault();mutation.mutate();}}>
      <label className="block text-xs font-semibold">Screening decision<select disabled={!canWrite} value={decision} onChange={e=>{setDecision(e.target.value as Item["decision"]);setSaved(false);}} className={cls}><option value="pending">Pending review</option><option value="include">Include in bibliography</option><option value="exclude">Exclude from this review</option></select></label>
      <label className="block text-xs font-semibold">Your annotation<textarea disabled={!canWrite} value={note} onChange={e=>{setNote(e.target.value);setSaved(false);}} maxLength={5000} rows={3} className={cls} placeholder="Why include or exclude it? Note limitations and questions to investigate." /></label>
      <button disabled={!canWrite||mutation.isPending} className="rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground disabled:opacity-50">{mutation.isPending?"Saving…":"Save review"}</button>
      {saved && <p role="status" className="text-xs text-primary">Decision and annotation saved.</p>}{mutation.isError && <p role="alert" className="text-sm text-destructive">{mutation.error.message}</p>}
    </form>
    {canWrite&&item.decision==='include'&&<ShareReviewedPaper reviewId={reviewId} itemId={item.id}/>}
  </article>;
}

export function LiteratureReviewWorkspace(){
  const {user}=useAuth();
  const {canWrite}=useLabPermissions();
  const cache=useQueryClient();
  const [topic,setTopic]=useState("");
  const [selected,setSelected]=useState("");
  const [error,setError]=useState("");
  const [exporting,setExporting]=useState(false);
  const reviews=useQuery<Review[]>({queryKey:["literature-reviews",user?.id],enabled:!!user,queryFn:()=>apiFetch("/api/veille/research/reviews")});
  const collect=useMutation({mutationFn:()=>apiFetch<Review>("/api/veille/research/reviews",{method:"POST",body:JSON.stringify({topic,max_results:10})}),onSuccess:async data=>{await cache.invalidateQueries({queryKey:["literature-reviews"]});setSelected(data.id);}});
  const review=reviews.data?.find(r=>r.id===selected) ?? reviews.data?.[0];
  async function download(){
    if(!review)return;setError("");setExporting(true);
    try{const result=await apiFetch<{filename:string;content:string}>(`/api/veille/research/reviews/${review.id}/export`);const url=URL.createObjectURL(new Blob([result.content],{type:"text/plain;charset=utf-8"}));const a=document.createElement("a");a.href=url;a.download=result.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
    catch(e){setError(e instanceof Error?e.message:String(e));}finally{setExporting(false);}
  }
  return <section className="rounded-2xl border border-border bg-card p-5 space-y-4">
    <div><h3 className="font-bold text-lg">Literature review workspace</h3><p className="text-sm text-muted-foreground">Choose a topic, examine PubMed abstract evidence, and build your annotated bibliography. Decisions are private to your account and this review.</p></div>
    <form onSubmit={e=>{e.preventDefault();collect.mutate();}} className="flex flex-wrap gap-2"><input aria-label="Research topic or PubMed query" required minLength={3} maxLength={200} value={topic} onChange={e=>setTopic(e.target.value)} className={`${cls} flex-1 min-w-48`} placeholder="e.g. water quality monitoring" /><button disabled={!canWrite||collect.isPending} className="rounded-xl bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50">{collect.isPending?"Collecting abstracts…":"Start review"}</button></form>
    <p className="text-xs text-muted-foreground">Up to 10 records per review. Source excerpts require no AI service; keyword matches are not scientific relevance scores. This is a screening aid, not an exhaustive systematic search.</p>
    {collect.isError&&<p role="alert" className="text-destructive">{collect.error.message}</p>}{reviews.isLoading&&<p role="status">Loading reviews…</p>}{reviews.isError&&<p role="alert" className="text-destructive">{reviews.error.message}</p>}
    {!!reviews.data?.length&&<label className="block text-xs font-semibold">Saved reviews (latest 50)<select className={cls} value={review?.id??""} onChange={e=>{setSelected(e.target.value);setError("");}}>{reviews.data.map(r=><option key={r.id} value={r.id}>{r.topic} · {r.status} · {new Date(r.created_at+"Z").toLocaleDateString()}</option>)}</select></label>}
    {review&&<><div className="flex flex-wrap justify-between gap-2"><p className="text-sm">{review.items.length} records · {review.items.filter(i=>i.decision==="include").length} included · {review.items.filter(i=>i.decision==="pending").length} pending</p><button disabled={exporting||!review.items.some(i=>i.decision==="include")} onClick={download} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50">Export annotated bibliography</button></div>
      {review.status==="failed"&&<p role="alert" className="text-destructive">Collection failed: {review.error_message}. Start a new review when the source is available.</p>}
      {review.status==="collecting"&&<p role="status">Collection has not completed. If the server restarted, start a new review.</p>}
      {review.status==="ready"&&!review.items.length&&<p>No records returned. Try a broader query.</p>}
      {error&&<p role="alert" className="text-destructive">{error}</p>}
      <div className="space-y-4">{review.items.map(item=><ReviewItem key={`${review.id}-${item.id}`} item={item} reviewId={review.id}/>)}</div></>}
  </section>;
}
