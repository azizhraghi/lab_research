import {useState} from 'react';
import {useMutation,useQueryClient} from '@tanstack/react-query';
import {useLabPermissions} from '../auth/AuthContext';
import {apiFetch} from '../lib/apiClient';
import {usePersonnels,useProjectMilestones,useProjectDeliverables,useBudgets,useCreateMilestone,useCreateDeliverable} from '../api/mis';

const input='w-full border rounded-lg p-2 bg-background text-sm';
export function ProjectSetup({projectId,onBudget,onStaff}:{projectId:string;onBudget:()=>void;onStaff:()=>void}){
  const {canWrite}=useLabPermissions();const cache=useQueryClient();
  const staff=usePersonnels(),budgets=useBudgets(),milestones=useProjectMilestones(projectId),deliverables=useProjectDeliverables(projectId);
  const milestone=useCreateMilestone(projectId),deliverable=useCreateDeliverable(projectId);
  const [person,setPerson]=useState(''),[title,setTitle]=useState(''),[due,setDue]=useState('');
  const assigned=staff.data?.filter(p=>p.projet_actuel_id===projectId)??[];
  const available=staff.data?.filter(p=>!p.projet_actuel_id&&p.disponible)??[];
  const assign=useMutation({mutationFn:()=>apiFetch(`/api/mis/projets/${projectId}/assign-staff`,{method:'POST',body:JSON.stringify({personnel_id:person})}),onSuccess:async()=>{setPerson('');await cache.invalidateQueries({queryKey:['mis']});}});
  const ready=[!!assigned.length,!!budgets.data?.some(b=>b.projet_id===projectId),!!milestones.data?.length,!!deliverables.data?.length];
  const queries=[staff,budgets,milestones,deliverables];
  const loading=queries.some(q=>q.isLoading),error=queries.find(q=>q.isError)?.error;
  const step=ready.findIndex(done=>!done);
  const pending=assign.isPending||milestone.isPending||deliverable.isPending;
  return <section className="border-b p-5 space-y-3"><h3 className="font-semibold">Project setup guide</h3>
    <p className="text-xs">Each step saves separately, so you can resume later. This checks recorded setup, not project approval.</p>
    {loading?<p role="status">Checking setup…</p>:error?<p role="alert">{error.message}</p>:<>
      <ol className="grid sm:grid-cols-4 gap-2">{['Assign team','Create budget record','Plan milestone','Define deliverable'].map((label,i)=><li className="border rounded-lg p-2 text-sm" key={label}>{ready[i]?'✓':'○'} {i+1}. {label}</li>)}</ol>
      <p role="status" className="text-sm">{step<0?'All four setup steps are recorded. Continue with project work and the research dossier.':`Next: ${['assign a team member','add a project budget','schedule the first milestone','define the first deliverable'][step]}.`}</p>
      <details open={step===0}><summary className="cursor-pointer text-sm">Team · {assigned.length} assigned</summary>{assigned.map(p=><p className="text-sm" key={p.id}>{p.prenom} {p.nom} · {p.role}</p>)}
        {canWrite&&<form className="flex flex-wrap gap-2 mt-2" onSubmit={e=>{e.preventDefault();assign.mutate();}}><label className="flex-1 text-xs">Unassigned available staff<select className={input} value={person} onChange={e=>setPerson(e.target.value)} required><option value="">Select a staff member</option>{available.map(p=><option key={p.id} value={p.id}>{p.prenom} {p.nom} · {p.role}</option>)}</select></label><button disabled={!person||pending} className="border rounded-lg px-3 disabled:opacity-50">Assign to project</button><button type="button" onClick={onStaff} className="underline text-sm">Create staff record</button></form>}
      </details>
      {canWrite&&!ready[1]&&<button className="border rounded-lg px-3 py-2 text-sm" onClick={onBudget}>Add the project budget</button>}
      {canWrite&&(step===2||step===3)&&<form className="grid sm:grid-cols-3 gap-2" onSubmit={e=>{e.preventDefault();const options={onSuccess:()=>{setTitle('');setDue('');}};if(step===2)milestone.mutate({title,due_date:due},options);else deliverable.mutate({title,due_date:due},options);}}><label className="text-xs">{step===2?'Milestone':'Deliverable'} title<input required minLength={3} maxLength={180} className={input} value={title} onChange={e=>setTitle(e.target.value)}/></label><label className="text-xs">Due date<input required type="date" className={input} value={due} onChange={e=>setDue(e.target.value)}/></label><button disabled={pending} className="border rounded-lg text-sm">Save {step===2?'milestone':'deliverable'}</button></form>}
    </>}
    {(assign.isError||milestone.isError||deliverable.isError)&&<p role="alert">{assign.error?.message||milestone.error?.message||deliverable.error?.message}</p>}
  </section>;
}
