import {useQuery} from '@tanstack/react-query';
import {apiFetch} from '../lib/apiClient';
type Entry={id:string;entry_type:string;description:string;amount:number;currency:string;occurred_at:string};
export function BudgetLedger({budgetId,spent}:{budgetId:string;spent:number}){
  const entries=useQuery<Entry[]>({queryKey:['mis','budget-entries',budgetId],queryFn:()=>apiFetch(`/api/mis/budgets/${budgetId}/entries`)});
  const recorded=entries.data?.filter(e=>e.entry_type==='expense').reduce((sum,e)=>sum+e.amount,0)??0;
  return <details className="border rounded-xl p-3"><summary className="cursor-pointer text-sm font-semibold">Budget entry history</summary>
    {entries.isLoading&&<p>Loading entries…</p>}{entries.isError&&<p role="alert">{entries.error.message}</p>}{entries.data&&<><p className="text-xs my-2">Recorded expenses: {recorded.toFixed(2)}. Difference from budget spent total: {(spent-recorded).toFixed(2)}. A difference may reflect opening balances or direct budget edits; inspect before reporting.</p><p className="text-xs mb-2">Commitments remain reserved separately. Recording an expense does not settle an existing commitment; avoid treating both entries as separate purchases.</p><div className="overflow-x-auto"><table className="w-full text-xs text-left"><thead><tr><th scope="col">Date</th><th scope="col">Type</th><th scope="col">Description</th><th scope="col">Amount</th></tr></thead><tbody>{entries.data.map(e=><tr key={e.id} className="border-t"><td className="py-2">{e.occurred_at}</td><td>{e.entry_type}</td><td>{e.description}</td><td>{e.amount.toFixed(2)} {e.currency}</td></tr>)}</tbody></table></div>{!entries.data.length&&<p className="text-xs">No entries recorded.</p>}</>}
  </details>;
}
