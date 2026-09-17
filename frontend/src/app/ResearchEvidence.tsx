import {useState} from "react";
import {useQuery,useMutation,useQueryClient} from "@tanstack/react-query";
import {useAuth,useLabPermissions} from "../auth/AuthContext";
import {apiFetch} from "../lib/apiClient";
import {SubmissionComparison} from './SubmissionComparison';

type Claim={id:string;statement:string;assessment:string;limitations:string;reference_ids:string[];deliverable_ids:string[];evaluation_ids:string[]};
type Evaluation={id:string;name:string;origin:string;split:string;unit:string;model_metrics:{mae:number;rmse:number;bias:number};baseline_metrics:{mae:number;rmse:number;bias:number}};
export type EvidenceData={project_id:string;revision:number;references:{id:string;title:string}[];claims:Claim[];evaluations:Evaluation[]};
type Submission={id:string;revision:number;status:string;submitted_by:string;submitted_at:string;reviewed_by:string|null;feedback:string|null;digest:string};
const cls="w-full rounded-lg border border-border bg-background p-2 text-sm";
const btn="rounded-lg border px-3 py-2 text-sm disabled:opacity-50";
async function download(path:string){
  const file=await apiFetch<{filename:string;content:string}>(path);
  const url=URL.createObjectURL(new Blob([file.content],{type:"text/html;charset=utf-8"}));
  const a=document.createElement("a");a.href=url;a.download=file.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}

function SubmissionCard({item}:{item:Submission}){
  const {user}=useAuth(); const {canReview}=useLabPermissions(); const cache=useQueryClient();
  const [open,setOpen]=useState(false); const [feedback,setFeedback]=useState("");
  const snapshot=useQuery<{snapshot:{dossier:{questions:string;approach:string;findings:string;limitations:string;claims:Claim[];references:{title:string;rationale:string}[];evaluations:(Evaluation & {provenance:string;protocol:string;rows:{observed:number;predicted:number;baseline:number}[]})[]};operations:{outstanding:string[];deliverables:{title:string;status:string}[]}}}>({queryKey:["submission",user?.id,item.id],enabled:open,queryFn:()=>apiFetch(`/api/mis/dossier-submissions/${item.id}`)});
  const decision=useMutation({mutationFn:(status:string)=>apiFetch(`/api/mis/dossier-submissions/${item.id}/decision`,{method:"POST",body:JSON.stringify({status,feedback})}),onSuccess:async()=>{await cache.invalidateQueries({queryKey:["submissions"]});await cache.invalidateQueries({queryKey:["research-attention"]});}});
  const exportFile=useMutation({mutationFn:()=>download(`/api/mis/dossier-submissions/${item.id}/export`)});
  return <article className="border rounded-xl p-3 space-y-2"><p className="font-semibold">Revision {item.revision} · {item.status.replace(/_/g," ")}</p><p className="text-xs">Submitted by {item.submitted_by} · {item.submitted_at} UTC</p>
    <button className={btn} onClick={()=>setOpen(!open)}>{open?"Hide submission":"Inspect submitted version"}</button>{" "}<button className={btn} disabled={exportFile.isPending} onClick={()=>exportFile.mutate()}>Export submission and review</button>
    {open&&snapshot.isLoading&&<p>Loading submitted version…</p>}{snapshot.isError&&<p role="alert">{snapshot.error.message}</p>}
    {open&&snapshot.data&&<div className="bg-muted rounded-lg p-3 space-y-2 text-sm">{(["questions","approach","findings","limitations"] as const).map(key=><p className="whitespace-pre-wrap" key={key}><strong>{key}: </strong>{snapshot.data.snapshot.dossier[key]}</p>)}{snapshot.data.snapshot.dossier.claims.map(c=><p key={c.id}><strong>{c.assessment}: </strong>{c.statement} · Limits: {c.limitations}</p>)}{snapshot.data.snapshot.dossier.references.map((r,i)=><p key={i}>{r.title} · {r.rationale}</p>)}{snapshot.data.snapshot.operations.outstanding.map((warning,i)=><p key={i}>{warning}</p>)}<p className="break-all text-xs">Snapshot SHA-256: {item.digest}</p></div>}
    {item.feedback&&<p className="whitespace-pre-wrap text-sm">Reviewer {item.reviewed_by}: {item.feedback}</p>}
    {open&&snapshot.data&&<details><summary className="cursor-pointer text-sm">Submitted evaluations and deliverables</summary>{snapshot.data.snapshot.dossier.evaluations.map(run=><div key={run.id} className="text-sm border-b py-2"><strong>{run.name} · {run.origin} · {run.split}</strong><p>{run.provenance}</p><p>{run.protocol}</p><p>Model MAE {run.model_metrics.mae} · baseline MAE {run.baseline_metrics.mae} · unit {run.unit}</p><pre className="text-xs max-h-48 overflow-auto">{JSON.stringify(run.rows,null,2)}</pre></div>)}{snapshot.data.snapshot.operations.deliverables.map((d,i)=><p key={i} className="text-sm">{d.title}: {d.status}</p>)}</details>}
    {item.status==="pending"&&canReview&&user?.id!==item.submitted_by&&<div className="space-y-2"><label className="text-sm">Review feedback<textarea className={cls} minLength={10} maxLength={10000} value={feedback} onChange={e=>setFeedback(e.target.value)}/></label><button className={btn} disabled={!snapshot.data||feedback.trim().length<10||decision.isPending} onClick={()=>decision.mutate("changes_requested")}>Request changes</button>{" "}<button className={btn} disabled={!snapshot.data||feedback.trim().length<10||decision.isPending} onClick={()=>decision.mutate("approved")}>Approve this version</button><p className="text-xs">Inspect the submitted version before deciding. Approval records your review; it does not prove scientific validity.</p></div>}
    {item.status==="pending"&&user?.id===item.submitted_by&&<p className="text-xs">A different reviewer must assess your submission.</p>}
    {(decision.isError||exportFile.isError)&&<p role="alert" className="text-destructive">{decision.error?.message||exportFile.error?.message}</p>}
  </article>;
}

export function ResearchEvidence({data,disabled}:{data:EvidenceData;disabled:boolean}){
  const {user}=useAuth(); const {canWrite}=useLabPermissions(); const cache=useQueryClient();
  const path=`/api/mis/projets/${data.project_id}/dossier`;
  const [statement,setStatement]=useState("");const [limits,setLimits]=useState("");const [assessment,setAssessment]=useState("proposed");
  const [refs,setRefs]=useState<string[]>([]);const [deliverables,setDeliverables]=useState<string[]>([]);const [evaluations,setEvaluations]=useState<string[]>([]);
  const [name,setName]=useState("");const [unit,setUnit]=useState("");const [origin,setOrigin]=useState("synthetic");const [split,setSplit]=useState("development");const [provenance,setProvenance]=useState("");const [protocol,setProtocol]=useState("");const [rows,setRows]=useState("");
  const operations=useQuery<{deliverables:{id:string;title:string}[]}>({queryKey:["dossier-deliverables",user?.id,data.project_id],queryFn:()=>apiFetch(`/api/mis/projets/${data.project_id}/completion-report`)});
  const submissions=useQuery<Submission[]>({queryKey:["submissions",user?.id,data.project_id],queryFn:()=>apiFetch(path+"/submissions")});
  const mutate=useMutation({mutationFn:({suffix,body,method="POST"}:{suffix:string;body?:object;method?:string})=>apiFetch(path+suffix,{method,body:body?JSON.stringify(body):undefined}),onSuccess:result=>cache.setQueryData(["project-dossier",user?.id,data.project_id],result)});
  const submit=useMutation({mutationFn:()=>apiFetch(path+"/submissions",{method:"POST",body:JSON.stringify({revision:data.revision})}),onSuccess:async()=>{await cache.invalidateQueries({queryKey:["submissions"]});await cache.invalidateQueries({queryKey:["research-attention"]});}});
  const [parseError,setParseError]=useState("");
  const locked=disabled||!canWrite||mutate.isPending||submit.isPending;
  function saveEvaluation(){
    setParseError("");
    const parsed=rows.trim().split(/\r?\n/).map(line=>line.trim().split(/\s+/).map(Number));
    if(parsed.length<2||parsed.length>1000||parsed.some(row=>row.length!==3||row.some(n=>!Number.isFinite(n)))){setParseError("Enter 2–1000 lines of three finite numbers: observed predicted baseline.");return;}
    mutate.mutate({suffix:"/evaluations",body:{revision:data.revision,name,unit,origin,split,provenance,protocol,rows:parsed.map(([observed,predicted,baseline])=>({observed,predicted,baseline}))}});
  }
  function evidenceOptions(title:string,options:{id:string;title:string}[],selected:string[],set:(ids:string[])=>void){return <fieldset className="space-y-1"><legend className="text-xs font-semibold">{title}</legend>{options.map(option=><label key={option.id} className="block text-xs"><input type="checkbox" disabled={locked} checked={selected.includes(option.id)} onChange={e=>set(e.target.checked?[...selected,option.id]:selected.filter(id=>id!==option.id))}/> {option.title}</label>)}{!options.length&&<p className="text-xs text-muted-foreground">None recorded.</p>}</fieldset>;}
  return <section className="border-t pt-4 space-y-4">
    <h4 className="font-semibold">Evidence-linked findings</h4><p className="text-xs text-muted-foreground">State what the evidence supports and what remains uncertain. These are author assessments, not automatic scientific validation.</p>
    {data.claims.map(c=><article className="border rounded-lg p-3 text-sm space-y-1" key={c.id}><p className="font-semibold">{c.statement}</p><p>{c.assessment.replace(/_/g," ")}</p><p>Limitations: {c.limitations}</p><p>{c.reference_ids.length} papers · {c.deliverable_ids.length} deliverables · {c.evaluation_ids.length} evaluations</p><button className={btn} disabled={locked} onClick={()=>mutate.mutate({suffix:`/findings/${c.id}?revision=${data.revision}`,method:"DELETE"})}>Remove finding</button></article>)}
    {canWrite&&<form className="space-y-2" onSubmit={e=>{e.preventDefault();mutate.mutate({suffix:"/findings",body:{revision:data.revision,statement,assessment,limitations:limits,reference_ids:refs,deliverable_ids:deliverables,evaluation_ids:evaluations}});}}>
      <label className="block text-sm">Finding statement<textarea required minLength={5} maxLength={3000} className={cls} value={statement} disabled={locked} onChange={e=>setStatement(e.target.value)}/></label>
      <label className="block text-sm">Evidence assessment<select className={cls} disabled={locked} value={assessment} onChange={e=>setAssessment(e.target.value)}><option value="proposed">Proposed / evidence still needed</option><option value="supported_with_limits">Supported with stated limitations</option></select></label>
      <label className="block text-sm">Finding limitations<textarea required minLength={5} maxLength={3000} className={cls} value={limits} disabled={locked} onChange={e=>setLimits(e.target.value)}/></label>
      {evidenceOptions("Selected literature",data.references,refs,setRefs)}{evidenceOptions("Project deliverables",operations.data?.deliverables??[],deliverables,setDeliverables)}{evidenceOptions("Evaluation records",data.evaluations.map(r=>({id:r.id,title:r.name})),evaluations,setEvaluations)}
      {operations.isError&&<p role="alert">{operations.error.message}</p>}<button className={btn} disabled={locked||data.revision<1}>Save evidence-linked finding</button>
    </form>}
    <details className="border rounded-xl p-3"><summary className="cursor-pointer font-semibold">Evaluation workspace · {data.evaluations.length} records</summary><p className="text-xs my-2">Compare model and baseline against the same observations. Provenance and held-out status are user declarations. Synthetic results demonstrate software behavior only.</p>
      {data.evaluations.map(r=><article className="border-b py-2 text-sm" key={r.id}><strong>{r.name}</strong><p>{r.origin} · {r.split} · {r.unit}</p><p>Model MAE {r.model_metrics.mae.toPrecision(4)} · RMSE {r.model_metrics.rmse.toPrecision(4)} · bias {r.model_metrics.bias.toPrecision(4)}</p><p>Baseline MAE {r.baseline_metrics.mae.toPrecision(4)} · RMSE {r.baseline_metrics.rmse.toPrecision(4)}</p></article>)}
      {canWrite&&<form className="space-y-2 mt-3" onSubmit={e=>{e.preventDefault();saveEvaluation();}}>
        <label className="block text-sm">Evaluation name<input className={cls} required minLength={3} maxLength={200} value={name} onChange={e=>setName(e.target.value)} disabled={locked}/></label>
        <label className="block text-sm">Measurement unit<input className={cls} required maxLength={80} value={unit} onChange={e=>setUnit(e.target.value)} disabled={locked}/></label>
        <label className="block text-sm">Data origin<select className={cls} value={origin} onChange={e=>setOrigin(e.target.value)} disabled={locked}><option value="synthetic">Synthetic demonstration</option><option value="field">Declared field measurements</option></select></label>
        <label className="block text-sm">Evaluation split<select className={cls} value={split} onChange={e=>setSplit(e.target.value)} disabled={locked}><option value="development">Development / calibration</option><option value="held_out">Declared independent held-out set</option></select></label>
        <label className="block text-sm">Dataset provenance<textarea className={cls} required minLength={10} maxLength={3000} value={provenance} onChange={e=>setProvenance(e.target.value)} disabled={locked}/></label>
        <label className="block text-sm">Protocol and baseline definition<textarea className={cls} required minLength={10} maxLength={3000} value={protocol} onChange={e=>setProtocol(e.target.value)} disabled={locked}/></label>
        <label className="block text-sm">Paired values: observed predicted baseline (one row per line)<textarea className={cls} required rows={5} maxLength={100000} value={rows} onChange={e=>setRows(e.target.value)} placeholder={"10 11 13\n20 19 23"} disabled={locked}/></label>
        <button className={btn} disabled={locked||data.revision<1}>Calculate and save evaluation</button>{parseError&&<p role="alert">{parseError}</p>}
      </form>}
    </details>
    <h4 className="font-semibold">Supervisor submissions and review</h4><p className="text-xs">Submission preserves this dossier version and current project progress. Future edits remain a working draft. Review decisions require a different reviewer account.</p>
    <button className={btn} disabled={locked||data.revision<1||submissions.data?.some(s=>s.revision===data.revision)} onClick={()=>submit.mutate()}>Submit saved revision {data.revision} for review</button>
    <SubmissionComparison items={submissions.data??[]}/>
    {submissions.data?.map(item=><SubmissionCard key={`${item.id}-${item.status}`} item={item}/>)}
    {(mutate.isError||submit.isError||submissions.isError)&&<p role="alert" className="text-destructive text-sm">{mutate.error?.message||submit.error?.message||submissions.error?.message} <button className="underline" onClick={()=>void cache.invalidateQueries({queryKey:["project-dossier",user?.id,data.project_id]})}>Reload saved dossier (discards local form edits)</button></p>}
  </section>;
}
