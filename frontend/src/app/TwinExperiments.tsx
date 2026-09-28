import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ReferenceLine } from 'recharts';
import { apiFetch } from '../lib/apiClient';
import { useParcels, useParcelForecast, useRefreshForecast } from '../api/digitaltwin';
import { useLabPermissions } from '../auth/AuthContext';

type Mode = 'demonstration' | 'field';
type Row = Record<string, any>;
type Run = Row & { id: number; assumptions: Row; kind: 'simulation' | 'optimisation' };
const input = 'w-full rounded-lg border border-border bg-background p-2 text-sm';
const button = 'rounded-lg border border-border px-3 py-2 text-sm disabled:opacity-50';
const card = 'rounded-2xl border border-border bg-card p-5 space-y-3';
function download(name: string, text: string, type: string) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const link = document.createElement('a'); link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function TwinExperiments({ onAddParcel }: { onAddParcel: () => void }) {
  const { data: parcels } = useParcels();
  const [selection, setSelection] = useState<number>();
  const parcel = parcels?.find(p => p.id === selection) ?? parcels?.[0];
  return <div className="h-full overflow-auto p-6 space-y-5">
    <div className="flex flex-wrap justify-between gap-3"><h2 className="text-xl font-bold">Digital Twin experiments</h2><div className="flex gap-2">
      <select aria-label="Parcel" className={input} value={parcel?.id ?? ''} onChange={e => setSelection(Number(e.target.value))}>{parcels?.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
      <button className={button} onClick={onAddParcel}>Add parcel</button></div></div>
    {parcel ? <Experiment key={parcel.id} parcel={parcel} /> : <p>Add a parcel to begin an experiment.</p>}
  </div>;
}

function Experiment({ parcel }: { parcel: Row }) {
  const qc = useQueryClient(); const { canReview } = useLabPermissions();
  const [mode, setMode] = useState<Mode>('demonstration');
  const [name, setName] = useState('Water stress experiment');
  const [initial, setInitial] = useState('70'); const [horizon, setHorizon] = useState(14);
  const [rain, setRain] = useState(1); const [et, setEt] = useState(1); const [temperature, setTemperature] = useState(0);
  const [quota, setQuota] = useState(''); const [capacity, setCapacity] = useState('25');
  const [selected, setSelected] = useState<Run | null>(null); const [day, setDay] = useState(0); const [playing, setPlaying] = useState(false);
  const forecast = useParcelForecast(parcel.id); const refresh = useRefreshForecast();
  const trail = useQuery<{ eligibility: { eligible: boolean; reason: string } }>({queryKey: ['experiment-eligibility', parcel.id], queryFn: () => apiFetch(`/api/twin/parcels/${parcel.id}/evidence-trail`), refetchInterval: 15000});
  const saved = useQuery<Run[]>({queryKey: ['experiments', parcel.id], queryFn: async () => {
    const [sim, opt] = await Promise.all(['simulation', 'optimisation'].map(kind => apiFetch<Row[]>(`/api/${kind}/parcels/${parcel.id}/runs?limit=100`)));
    return ([...sim.map(r => ({...r, kind: 'simulation'})), ...opt.map(r => ({...r, kind: 'optimisation'}))] as Run[]).sort((a,b) => String(b.created_at).localeCompare(String(a.created_at)));
  }});
  const execute = useMutation({mutationFn: async (kind: Run['kind']) => {
    const common = {mode, horizon_days: horizon, rainfall_factor: rain, et_factor: et, temperature_delta_c: temperature, initial_moisture_mm: mode === 'demonstration' ? Number(initial) : null};
    const body = kind === 'simulation' ? {...common, scenario_name: name} : {...common, run_name: name, water_quota_mm: quota === '' ? null : Number(quota), max_irrigation_mm_per_day: Number(capacity)};
    const result = await apiFetch<Row>(`/api/${kind}/parcels/${parcel.id}/runs`, {method: 'POST', body: JSON.stringify(body)});
    return {...result, kind} as Run;
  }, onSuccess: run => { setSelected(run); setDay(0); setPlaying(false); void qc.invalidateQueries({queryKey: ['experiments', parcel.id]}); }});
  const approve = useMutation({mutationFn: (id: number) => apiFetch(`/api/optimisation/runs/${id}/approve`, {method: 'POST'}), onSuccess: () => {setSelected(r => r ? {...r, is_approved: true} : r); void qc.invalidateQueries({queryKey: ['experiments', parcel.id]});}});
  const run = selected;
  const assumptions = run?.assumptions ?? {};
  const snapshot = assumptions.parcel_snapshot ?? parcel;
  const runMode = assumptions.mode ?? 'legacy / unspecified';
  const comparison = run?.kind === 'optimisation' ? assumptions.comparison : run;
  const series: Row[] = (comparison?.time_series ?? []).map((r: Row, i: number) => ({date: r.date, baseline: r.baseline.soil_moisture_end_mm, scenario: r.scenario.soil_moisture_end_mm, plan: run?.kind === 'optimisation' ? run.schedule[i]?.soil_moisture_end_mm : undefined}));
  const cursor = series[Math.min(day, Math.max(0, series.length - 1))];
  useEffect(() => { if (!playing || !series.length) return; const timer = setInterval(() => setDay(d => (d + 1) % series.length), 900); return () => clearInterval(timer); }, [playing, series.length]);
  const summary = run?.kind === 'optimisation' ? run.summary : run?.scenario_summary;
  const threshold = Number(run?.constraints?.trigger_moisture_mm ?? comparison?.scenario_summary?.target_minimum_mm ?? snapshot.field_capacity_mm - (snapshot.field_capacity_mm - snapshot.wilting_point_mm) * .45);
  const fc = Number(snapshot.field_capacity_mm); const wp = Number(snapshot.wilting_point_mm);
  const missing = !forecast.data?.length ? 'Refresh the forecast before running.' : mode === 'demonstration' && (initial.trim() === '' || !Number.isFinite(Number(initial)) || Number(initial) < 0 || Number(initial) > Number(parcel.field_capacity_mm)) ? `Enter initial moisture from 0 to ${parcel.field_capacity_mm} mm.` : mode === 'field' && !trail.data?.eligibility.eligible ? (trail.data?.eligibility.reason ?? 'Checking reviewed field measurements…') : '';
  const planMissing = !Number.isFinite(Number(capacity)) || Number(capacity) < 1 || Number(capacity) > 80 ? 'Daily capacity must be 1–80 mm.' : quota !== '' && (!Number.isFinite(Number(quota)) || Number(quota) < 0) ? 'Water quota must be zero or greater.' : '';
  function reopen(r: Run) {
    setSelected(r); setDay(0); setPlaying(false); execute.reset(); approve.reset();
    const p = r.assumptions?.request;
    if (p) {setMode(p.mode); setName(p.scenario_name ?? p.run_name); setHorizon(p.horizon_days); setRain(p.rainfall_factor); setEt(p.et_factor); setTemperature(p.temperature_delta_c); setInitial(p.initial_moisture_mm == null ? '' : String(p.initial_moisture_mm)); setQuota(p.water_quota_mm == null ? '' : String(p.water_quota_mm)); setCapacity(String(p.max_irrigation_mm_per_day ?? 25));}
  }
  return <>
    <div className="grid xl:grid-cols-[340px_1fr] gap-5">
      <section className={card}><h3 className="font-bold">Experiment controls</h3>
        <label className="block text-sm">Mode<select className={input} value={mode} onChange={e => setMode(e.target.value as Mode)}><option value="demonstration">Demonstration — assumed inputs</option><option value="field">Field — reviewed measurements</option></select></label>
        <p className="text-xs">{mode === 'demonstration' ? 'Hypothetical experiments cannot be approved or generate field tasks.' : 'Requires a current quality-reviewed field measurement. Plans require human approval.'}</p>
        <label className="block text-sm">Experiment name<input className={input} value={name} onChange={e => setName(e.target.value)} /></label>
        {mode === 'demonstration' && <label className="block text-sm">Initial moisture (mm)<input type="number" min="0" max={parcel.field_capacity_mm} className={input} value={initial} onChange={e => setInitial(e.target.value)} /></label>}
        {([{label:'Horizon (days)',value:horizon,set:setHorizon,min:3,max:16,step:1},{label:'Rainfall factor',value:rain,set:setRain,min:0,max:3,step:.05},{label:'Evapotranspiration factor',value:et,set:setEt,min:0,max:3,step:.05},{label:'Temperature change (°C)',value:temperature,set:setTemperature,min:-10,max:15,step:.5}]).map(c => <label className="block text-sm" key={c.label}>{c.label}: <strong>{c.value}</strong><input className="w-full accent-emerald-700" type="range" min={c.min} max={c.max} step={c.step} value={c.value} onChange={e => c.set(Number(e.target.value))}/></label>)}
        <div className="flex gap-2"><button className={button} onClick={() => {setRain(1);setEt(1);setTemperature(0);}}>Baseline</button><button className={button} onClick={() => {setRain(.5);setEt(1.2);setTemperature(2);}}>Hot + dry</button></div>
        <label className="block text-sm">Total water quota (mm)<input type="number" min="0" placeholder="Unlimited" className={input} value={quota} onChange={e => setQuota(e.target.value)}/></label>
        <label className="block text-sm">Daily capacity (mm)<input type="number" min="1" max="80" className={input} value={capacity} onChange={e => setCapacity(e.target.value)}/></label>
        <button className={button} disabled={refresh.isPending} onClick={() => refresh.mutate(parcel.id)}>{refresh.isPending ? 'Refreshing…' : 'Refresh forecast'}</button>
        <p className="text-xs" role="status">{forecast.data?.length ?? 0} forecast days available. {refresh.isSuccess && 'Forecast refreshed.'}</p>
        {refresh.isError && <p role="alert">{refresh.error.message}</p>}
        {missing && <p className="text-amber-800 text-sm" role="status">{missing}</p>}{planMissing && <p className="text-amber-800 text-sm">{planMissing}</p>}
        <button className={button+' w-full bg-emerald-700 text-white'} disabled={!!missing || execute.isPending || !name.trim()} onClick={() => execute.mutate('simulation')}>Run simulation</button>
        <button className={button+' w-full'} disabled={!!missing || !!planMissing || execute.isPending || !name.trim()} onClick={() => execute.mutate('optimisation')}>{mode === 'demonstration' ? 'Generate hypothetical irrigation plan' : 'Generate field irrigation plan'}</button>
        {execute.isPending && <p role="status">Calculating and saving experiment…</p>}{execute.isError && <p role="alert" className="text-red-700">{execute.error.message}</p>}
        <p className="text-xs">Both actions use these same weather assumptions and horizon. Planning uses a constrained greedy heuristic, not a proof of optimality.</p>
      </section>
      <div className="space-y-5">
        {!run ? <section className={card}>Run an experiment or open a saved result below.</section> : <>
          <section className={card}><div className="flex flex-wrap justify-between gap-2"><h3 className="font-bold">{run.scenario_name ?? run.run_name}</h3><strong className="rounded bg-emerald-50 text-emerald-900 px-3 py-1 text-sm">{runMode} · {run.kind}</strong></div>
            <p className="text-xs">Saved {run.created_at} · results retain the saved inputs when you edit the controls.</p>
            <div className="grid sm:grid-cols-3 gap-3">{[['Final moisture',`${summary?.final_moisture_mm ?? '—'} mm`],['Days below stress threshold',summary?.stress_days ?? '—'],['Planned irrigation',run.kind === 'optimisation' ? `${summary.total_irrigation_mm} mm` : 'None applied']].map(([label,value]) => <div className="rounded-xl bg-muted p-3" key={String(label)}><p className="text-xs">{label}</p><strong className="text-xl">{value}</strong></div>)}</div>
            {run.kind === 'optimisation' && <p>{summary.stress_days === 0 ? 'This schedule keeps moisture above the stress threshold under these assumptions.' : `This schedule leaves ${summary.stress_days} stress days: the quota, daily capacity, or scheduling rule is insufficient.`} {summary.quota_remaining_mm != null && `Remaining quota: ${summary.quota_remaining_mm} mm.`}</p>}
            <div className="h-72"><ResponsiveContainer width="100%" height="100%"><LineChart data={series} margin={{top:15,right:25,left:15,bottom:15}}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="date" tick={{fontSize:11}} minTickGap={35}/><YAxis tick={{fontSize:11}} domain={[0,fc]} label={{value:'Soil water (mm)',angle:-90,position:'insideLeft'}}/><Tooltip/><Legend/><ReferenceLine y={wp} stroke="#b91c1c" strokeDasharray="4 4" label="Wilting point"/><ReferenceLine y={threshold} stroke="#a16207" strokeDasharray="4 4" label="Stress threshold"/><Line dataKey="baseline" name="Baseline, no irrigation" stroke="#047857" dot={false}/><Line dataKey="scenario" name="Scenario, no irrigation" stroke="#d97706" strokeDasharray="5 3" dot={false}/>{run.kind === 'optimisation' && <Line dataKey="plan" name="Scenario with irrigation" stroke="#2563eb" strokeWidth={3} dot={false}/>}</LineChart></ResponsiveContainer></div>
            <p className="text-xs">Baseline and scenario overlap when the weather factors equal 1 and temperature change equals 0.</p>
          </section>
          <section className={card}><h3 className="font-bold">Projected root-zone water · {runMode}</h3><p className="text-sm">{cursor?.date} · illustrative soil-water storage, not a measured aquifer or GIS map.</p>
            <div className="flex flex-wrap gap-8 justify-center">{(['baseline','scenario',...(run.kind === 'optimisation' ? ['plan'] : [])]).map(key => <div key={key} className="text-center"><div className="relative h-44 w-28 border-2 rounded-lg overflow-hidden bg-amber-100"><div className="absolute bottom-0 w-full bg-blue-500/70 transition-all duration-500" style={{height:`${Math.max(0,Math.min(100,Number(cursor?.[key] ?? 0)/fc*100))}%`}}/><div className="absolute w-full border-t-2 border-red-700" style={{bottom:`${wp/fc*100}%`}}/><div className="absolute w-full border-t-2 border-amber-700 border-dashed" style={{bottom:`${threshold/fc*100}%`}}/></div><p className="text-sm capitalize">{key}: {Number(cursor?.[key] ?? 0).toFixed(1)} mm</p></div>)}</div>
            <p className="text-xs">Top: field capacity {fc} mm · dashed: stress threshold {threshold.toFixed(1)} mm · red: wilting point {wp} mm</p>
            <div className="flex items-center gap-3"><button className={button} onClick={() => setPlaying(!playing)}>{playing ? 'Pause' : 'Play days'}</button><input aria-label="Projection day" className="flex-1" type="range" min={0} max={Math.max(0,series.length-1)} value={day} onChange={e => {setDay(Number(e.target.value));setPlaying(false);}}/><span>Day {day+1}</span></div>
          </section>
          <section className={card}><h3 className="font-bold">Saved evidence and export · {runMode}</h3>
            <p className="text-sm">{assumptions.forecast_provider ?? assumptions.weather_source} / {assumptions.forecast_model ?? ''} · retrieved {assumptions.forecast_retrieved_at ?? 'Unknown'}. Coverage {assumptions.forecast_coverage_start} to {assumptions.forecast_coverage_end}.</p>
            <p className="text-sm">{assumptions.input_provenance}. Model outputs have not established scientific predictive accuracy.</p>
            <div className="flex gap-2"><button className={button} onClick={() => download(`experiment-${run.kind}-${run.id}.json`,JSON.stringify(run,null,2),'application/json')}>Export full experiment (JSON)</button><button className={button} onClick={() => {const rows = series.map((r,i) => [runMode,r.date,r.baseline,r.scenario,r.plan ?? '',run.schedule?.[i]?.irrigation_mm ?? 0]); download(`experiment-${run.kind}-${run.id}.csv`,['Mode,Date,Baseline_mm,Scenario_mm,Planned_moisture_mm,Irrigation_mm',...rows.map(r => r.join(','))].join('\n'),'text/csv');}}>Export daily results (CSV)</button></div>
            <details><summary>Exact saved inputs and assumptions</summary><pre className="text-xs whitespace-pre-wrap max-h-72 overflow-auto">{JSON.stringify(assumptions,null,2)}</pre></details>
            {run.kind === 'optimisation' && <><div className="overflow-auto"><table className="w-full text-sm"><thead><tr><th>Date</th><th>Irrigation (mm)</th><th>End moisture (mm)</th><th>Stress</th></tr></thead><tbody>{run.schedule.map((r:Row) => <tr className="border-t text-center" key={r.date}><td>{r.date}</td><td>{r.irrigation_mm}</td><td>{r.soil_moisture_end_mm}</td><td>{r.stress ? 'Yes' : 'No'}</td></tr>)}</tbody></table></div>
              {runMode === 'field' ? <button className={button} disabled={!canReview || approve.isPending || run.is_approved} onClick={() => approve.mutate(run.id)}>{run.is_approved ? 'Approved' : 'Approve and create field tasks'}</button> : <p className="text-sm">Demonstration or legacy plan: operational approval unavailable.</p>}
              {approve.isError && <p role="alert">{approve.error.message}</p>}</>}
          </section>
        </>}
      </div>
    </div>
    <section className={card}><h3 className="font-bold">Saved experiments</h3>{saved.isError && <p role="alert">{saved.error.message}</p>}{saved.data?.length === 0 && <p>No saved experiments yet.</p>}<div className="grid md:grid-cols-2 gap-2">{saved.data?.map(r => <button className={button+' text-left'} key={`${r.kind}-${r.id}`} onClick={() => reopen(r)}>{r.scenario_name ?? r.run_name} · {r.assumptions.mode ?? 'legacy / unspecified'} · {r.kind}<span className="block text-xs">{r.created_at} · Open saved inputs and results</span></button>)}</div></section>
  </>;
}
