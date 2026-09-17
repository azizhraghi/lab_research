import {useState} from 'react';
import {useQuery,useMutation,useQueryClient} from '@tanstack/react-query';
import {apiFetch} from '../lib/apiClient';
import {useAuth,useLabPermissions} from '../auth/AuthContext';
import {PublicationAudit} from './PublicationAudit';
type Trust={identifiers:Record<string,string|null>;identity_status:string;history:{id:string;reviewer_id:string;rationale:string;reviewed_at:string}[];metrics:{name:string;value:number;source:string;retrieved_at:string;validation:string}[]};
export function BibliographicTrust({researchers}:{researchers:{id:number;name:string}[]}){
  const {user}=useAuth();const {canReview}=useLabPermissions();const cache=useQueryClient();const [selected,setSelected]=useState('');const [note,setNote]=useState('');
  const id=selected||String(researchers[0]?.id??'');
  const trust=useQuery<Trust>({queryKey:['bibliographic-trust',user?.id,id],enabled:!!id,queryFn:()=>apiFetch(`/api/biblio/researchers/${id}/trust`)});
  const confirm=useMutation({mutationFn:()=>apiFetch(`/api/biblio/researchers/${id}/trust`,{method:'POST',body:JSON.stringify({identifiers:trust.data?.identifiers,rationale:note})}),onSuccess:result=>{cache.setQueryData(['bibliographic-trust',user?.id,id],result);setNote('');}});
  return <details className="border rounded-xl p-4"><summary className="font-semibold cursor-pointer">Identity review and metric provenance</summary><p className="text-xs my-2">Check the source profiles before confirming identifiers. This records a human check; provider metrics and name-based matches still need independent assessment.</p><label className="text-sm">Researcher<select className="w-full border rounded-lg p-2 bg-background" value={id} onChange={e=>{setSelected(e.target.value);setNote('');confirm.reset();}}>{researchers.map(r=><option value={r.id} key={r.id}>{r.name}</option>)}</select></label>
    {trust.data&&<div className="text-sm space-y-2 mt-2"><p>{trust.data.identity_status.replace(/_/g,' ')}</p>{Object.entries(trust.data.identifiers).map(([key,value])=><p key={key}>{key}: {value||'not supplied'}</p>)}{trust.data.metrics.map((m,i)=><p key={i}>{m.name}: {m.value} · {m.source} · {m.retrieved_at} · {m.validation}</p>)}{!trust.data.metrics.length&&<p>No metrics retrieved.</p>}{trust.data.history.map(r=><p key={r.id}>{r.reviewed_at} · {r.reviewer_id}: {r.rationale}</p>)}
      {canReview&&<form onSubmit={e=>{e.preventDefault();confirm.mutate();}}><label className="block">Identity check evidence<textarea className="w-full border rounded-lg p-2 bg-background" required minLength={20} maxLength={3000} value={note} onChange={e=>setNote(e.target.value)} placeholder="Record the source profile URL, matching affiliation/publications and how you confirmed the identity."/></label><button disabled={confirm.isPending} className="border rounded-lg px-3 py-2">Record manual identity confirmation</button></form>}
      <PublicationAudit key={id} researcherId={id}/>
    </div>}{(trust.isError||confirm.isError)&&<p role="alert" className="text-destructive">{trust.error?.message||confirm.error?.message}</p>}
  </details>;
}
