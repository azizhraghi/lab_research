import {useState} from 'react';
import {useMutation,useQueryClient} from '@tanstack/react-query';
import {useAuth} from '../auth/AuthContext';
import {useProjets} from '../api/mis';
import {apiFetch} from '../lib/apiClient';
export function ShareReviewedPaper({reviewId,itemId}:{reviewId:string;itemId:string}){
  const {user}=useAuth();const projects=useProjets();const cache=useQueryClient();
  const [project,setProject]=useState(''),[rationale,setRationale]=useState('');
  const save=useMutation({mutationFn:async()=>{
    const path=`/api/mis/projets/${project}/dossier`;
    const dossier=await apiFetch<{revision:number}>(path);
    return apiFetch(path+'/references',{method:'POST',body:JSON.stringify({revision:dossier.revision,review_id:reviewId,item_id:itemId,rationale})});
  },onSuccess:result=>{cache.setQueryData(['project-dossier',user?.id,project],result);}});
  return <details className="border-t pt-3"><summary className="cursor-pointer text-sm font-semibold">Use this included paper in a project</summary><p className="text-xs my-2">Share its citation and source excerpt with laboratory users. Enter a project rationale; private screening notes stay private.</p><form className="space-y-2" onSubmit={e=>{e.preventDefault();save.mutate();}}><label className="block text-xs">Target project<select required disabled={save.isPending} value={project} onChange={e=>{setProject(e.target.value);save.reset();}} className="w-full border rounded-lg p-2 bg-background"><option value="">Choose project</option>{projects.data?.map(p=><option key={p.id} value={p.id}>{p.nom}</option>)}</select></label><label className="block text-xs">Project relevance<textarea required minLength={3} maxLength={3000} disabled={save.isPending} value={rationale} onChange={e=>{setRationale(e.target.value);save.reset();}} className="w-full border rounded-lg p-2 bg-background"/></label><button disabled={!project||save.isPending||save.isSuccess} className="border rounded-lg px-3 py-2 text-sm disabled:opacity-50">Add to project dossier</button></form>{save.isSuccess&&<p role="status" className="text-sm">Paper added. Open this project's research dossier to connect it to a finding.</p>}{(save.isError||projects.isError)&&<p role="alert">{save.error?.message||projects.error?.message}</p>}</details>;
}
