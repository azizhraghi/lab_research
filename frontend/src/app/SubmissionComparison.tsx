import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {useAuth} from '../auth/AuthContext';
import {apiFetch} from '../lib/apiClient';
type Version={id:string;revision:number;status:string};
type Change={section:string;field:string;kind:string;before:unknown;after:unknown};
function ReadableValue({value}:{value:unknown}){
  if(value==null)return <p className="text-muted-foreground">Not present</p>;
  if(Array.isArray(value))return value.length?<ul className="space-y-2">{value.map((item,i)=><li key={i}><ReadableValue value={item}/></li>)}</ul>:<p>None recorded</p>;
  if(typeof value==='object')return <dl className="space-y-2">{Object.entries(value).filter(([key])=>!['id','project_id','created_at','updated_at','created_by'].includes(key)).map(([key,item])=><div key={key}><dt className="font-semibold capitalize">{key.replace(/_/g,' ').replace(/ ids$/,' links')}</dt><dd>{key.endsWith('_ids')&&Array.isArray(item)?`${item.length} linked records`:key==='rows'&&Array.isArray(item)?`${item.length} paired observations (inspect the submission for values)`:<ReadableValue value={item}/>}</dd></div>)}</dl>;
  return <p className="whitespace-pre-wrap break-words">{typeof value==='boolean'?(value?'Yes':'No'):String(value)}</p>;
}
export function SubmissionComparison({items}:{items:Version[]}){
  const {user}=useAuth();const [before,setBefore]=useState(''),[after,setAfter]=useState('');
  const old=before||items[1]?.id||'',current=after||items[0]?.id||'';
  const [open,setOpen]=useState(false);
  const query=useQuery<{changes:Change[];before_revision:number;after_revision:number}>({queryKey:['submission-comparison',user?.id,old,current],enabled:open&&!!old&&!!current&&old!==current,queryFn:()=>apiFetch(`/api/mis/dossier-submissions/${current}/comparison?against=${encodeURIComponent(old)}`)});
  if(items.length<2)return null;
  return <details onToggle={e=>setOpen(e.currentTarget.open)} className="border rounded-xl p-3 space-y-3"><summary className="font-semibold cursor-pointer">Compare submitted versions</summary><p className="text-xs">Compare preserved research and project records. Current unsaved edits are not included.</p><div className="grid sm:grid-cols-2 gap-3">{([['Before',old,setBefore],['After',current,setAfter]] as const).map(([label,value,set])=><label key={label} className="text-sm">{label}<select className="w-full border rounded-lg p-2 bg-background" value={value} onChange={e=>set(e.target.value)}>{items.map(s=><option key={s.id} value={s.id}>Revision {s.revision} · {s.status}</option>)}</select></label>)}</div>
    {old===current?<p>Select two different submissions.</p>:query.isLoading?<p role="status">Comparing versions…</p>:query.isError?<p role="alert">{query.error.message}</p>:query.data&&<><p className="text-sm">{query.data.changes.length} changes · revision {query.data.before_revision} → {query.data.after_revision}</p>{query.data.changes.map((c,i)=><article key={i} className="border rounded-lg p-3"><h5 className="text-sm font-semibold capitalize">{c.field==='claims'?'Evidence-linked findings':c.field} · {c.kind}</h5><div className="grid sm:grid-cols-2 gap-3 mt-2">{[['Before',c.before],['After',c.after]].map(([label,value])=><div key={String(label)}><p className="text-xs font-semibold mb-1">{String(label)}</p><div className="text-sm max-h-80 overflow-auto bg-muted p-3 rounded-lg"><ReadableValue value={value}/></div></div>)}</div></article>)}</>}
  </details>;
}
