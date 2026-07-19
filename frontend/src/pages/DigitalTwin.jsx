import React, { useEffect, useState } from "react";
import {
  Activity,
  ArrowLeft,
  CalendarClock,
  CheckCircle2,
  CloudSun,
  Droplets,
  FlaskConical,
  Gauge,
  Leaf,
  Map,
  Play,
  RefreshCw,
  ShieldCheck,
  Target,
  Thermometer,
  TriangleAlert,
  Upload,
  ChevronRight,
} from "lucide-react";
import {
  LineChart as ReLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { fieldData, simulation, twin } from "../lib/api";

const cropLabels = {
  wheat: "Wheat",
  olive: "Olive",
  citrus: "Citrus",
  vegetable: "Vegetable",
  forage: "Forage",
};

function fmt(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(1) + suffix;
}

function moistureStatus(reading, parcel) {
  if (!reading) return { label: "No data", className: "bg-slate-50 border-slate-200 text-slate-600" };
  const ratio = reading.soil_moisture_mm / parcel.field_capacity_mm;
  if (ratio >= 0.7) return { label: "Optimal", className: "bg-emerald-50 border-emerald-200 text-emerald-700" };
  if (ratio >= 0.45) return { label: "Watch", className: "bg-amber-50 border-amber-200 text-amber-700" };
  return { label: "Critical", className: "bg-red-50 border-red-200 text-red-700" };
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value + "T12:00:00").toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
  });
}

function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DigitalTwin() {
  const [parcels, setParcels] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  const [forecasts, setForecasts] = useState([]);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastNotice, setForecastNotice] = useState(null);

  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simForm, setSimForm] = useState({
    scenario_name: "Forecast scenario",
    horizon_days: 14,
    rainfall_factor: 1,
    et_factor: 1,
    temperature_delta_c: 0,
  });

  const [irrigationForm, setIrrigationForm] = useState({
    occurred_at: new Date().toISOString().slice(0, 16),
    amount_mm: "",
    method: "drip",
    recorded_by: "",
  });
  const [irrigationEvents, setIrrigationEvents] = useState([]);
  const [irrigationLoading, setIrrigationLoading] = useState(false);
  const [readingFile, setReadingFile] = useState(null);
  const [readingImportLoading, setReadingImportLoading] = useState(false);
  const [readingImportSummary, setReadingImportSummary] = useState(null);

  const [calibrations, setCalibrations] = useState([]);
  const [calibrationLoading, setCalibrationLoading] = useState(false);
  const [calibrationError, setCalibrationError] = useState(null);
  const [reviewer, setReviewer] = useState("");
  const [applyLoading, setApplyLoading] = useState(false);

  useEffect(() => {
    twin.listParcels()
      .then(setParcels)
      .catch((requestError) => setError(requestError.message))
      .finally(() => setLoading(false));
  }, []);

  const loadOperationalData = async (parcelId) => {
    const [forecastResult, irrigationResult, calibrationResult] = await Promise.all([
      fieldData.listForecasts(parcelId),
      fieldData.listIrrigationEvents(parcelId),
      fieldData.listCalibrations(parcelId),
    ]);
    setForecasts(forecastResult);
    setIrrigationEvents(irrigationResult);
    setCalibrations(calibrationResult);
  };

  const openParcel = async (parcelId) => {
    setDetailLoading(true);
    setError(null);
    setCalibrationError(null);
    setSimResult(null);
    setForecastNotice(null);
    try {
      const parcel = await twin.getParcel(parcelId);
      setSelected(parcel);
      await loadOperationalData(parcelId);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const refreshForecast = async () => {
    if (!selected) return;
    setForecastLoading(true);
    setError(null);
    try {
      const result = await fieldData.refreshForecast(selected.id);
      setForecastNotice(
        result.forecast_days + " daily values retrieved at " + formatDateTime(result.retrieved_at)
      );
      setForecasts(await fieldData.listForecasts(selected.id));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setForecastLoading(false);
    }
  };

  const runSimulation = async () => {
    if (!selected) return;
    setSimLoading(true);
    setError(null);
    try {
      const result = await simulation.run(selected.id, {
        ...simForm,
        horizon_days: Number(simForm.horizon_days),
        rainfall_factor: Number(simForm.rainfall_factor),
        et_factor: Number(simForm.et_factor),
        temperature_delta_c: Number(simForm.temperature_delta_c),
      });
      setSimResult(result);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSimLoading(false);
    }
  };

  const addIrrigationEvent = async (event) => {
    event.preventDefault();
    if (!selected) return;
    setIrrigationLoading(true);
    setError(null);
    try {
      const item = await fieldData.addIrrigationEvent(selected.id, {
        occurred_at: new Date(irrigationForm.occurred_at).toISOString(),
        amount_mm: Number(irrigationForm.amount_mm),
        method: irrigationForm.method,
        recorded_by: irrigationForm.recorded_by,
      });
      setIrrigationEvents((current) => [item, ...current]);
      setIrrigationForm((current) => ({ ...current, amount_mm: "" }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setIrrigationLoading(false);
    }
  };

  const importFieldReadings = async () => {
    if (!selected || !readingFile) return;
    setReadingImportLoading(true);
    setError(null);
    try {
      const result = await fieldData.importReadings(selected.id, readingFile);
      setReadingImportSummary(result);
      setSelected(await twin.getParcel(selected.id));
      setReadingFile(null);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setReadingImportLoading(false);
    }
  };


  const runCalibration = async () => {
    if (!selected) return;
    setCalibrationLoading(true);
    setCalibrationError(null);
    try {
      const profile = await fieldData.runCalibration(selected.id);
      setCalibrations((current) => [profile, ...current]);
    } catch (requestError) {
      setCalibrationError(requestError.message);
    } finally {
      setCalibrationLoading(false);
    }
  };

  const applyCalibration = async (profileId) => {
    if (!reviewer.trim()) {
      setCalibrationError("A named laboratory reviewer is required to apply a calibration.");
      return;
    }
    setApplyLoading(true);
    setCalibrationError(null);
    try {
      const applied = await fieldData.applyCalibration(profileId, { reviewed_by: reviewer.trim() });
      setCalibrations((current) => current.map((profile) => (
        profile.id === applied.id ? applied : profile
      )));
      setSelected(await twin.getParcel(selected.id));
    } catch (requestError) {
      setCalibrationError(requestError.message);
    } finally {
      setApplyLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity size={32} className="animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading digital twin...</span>
      </div>
    );
  }

  if (!selected) {
    return (
      <div className="p-6 h-full overflow-y-auto scrollbar-hide space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-foreground font-jakarta">Digital Twins</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Forecast-aware parcel state, simulations, and reviewed calibrations.
          </p>
        </div>
        {error && <ErrorBanner message={error} />}
        {parcels.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-muted-foreground bg-card border border-dashed border-border rounded-2xl">
            <Droplets size={40} className="mb-3 opacity-20" />
            <h3 className="font-bold text-lg mb-1 text-foreground">No parcels found</h3>
            <p className="text-sm">Create a parcel before retrieving forecast data.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {parcels.map((parcel) => (
              <button
                key={parcel.id}
                onClick={() => openParcel(parcel.id)}
                className="bg-card border border-border rounded-2xl p-5 text-left hover:border-primary/50 hover:shadow-md transition-all group"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                    <Leaf size={18} />
                  </div>
                  <ChevronRight size={18} className="text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <div className="text-xs font-bold text-muted-foreground mb-1">{parcel.code}</div>
                <h3 className="text-lg font-bold text-foreground font-jakarta mb-2">{parcel.name}</h3>
                <p className="text-sm text-muted-foreground">
                  {cropLabels[parcel.crop_type] || parcel.crop_type} · {parcel.area_ha} ha · {parcel.soil_type}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }

  const latestReading = selected.latest_readings?.[0];
  const status = moistureStatus(latestReading, selected);
  const activeCalibration = calibrations.find((item) => item.status === "applied");
  const candidateCalibration = calibrations.find((item) => item.status === "candidate");
  const chartData = simResult
    ? simResult.time_series.map((row) => ({
      day: "D" + row.day,
      baseline: row.baseline.soil_moisture_end_mm,
      scenario: row.scenario.soil_moisture_end_mm,
      capacity: selected.field_capacity_mm,
    }))
    : [];

  return (
    <div className="h-full overflow-y-auto scrollbar-hide p-6 space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <button
            className="flex items-center gap-1 text-sm text-primary font-semibold hover:underline mb-2"
            onClick={() => setSelected(null)}
          >
            <ArrowLeft size={16} /> Back to parcels
          </button>
          <h2 className="text-2xl font-bold text-foreground font-jakarta flex items-center gap-2">
            <Leaf className="text-primary" /> Digital Twin: {selected.name}
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            {selected.code} · {cropLabels[selected.crop_type] || selected.crop_type} · {selected.area_ha} ha · {selected.soil_type} soil
          </p>
        </div>
        <div className={"px-4 py-2 rounded-xl border " + status.className}>
          <div className="text-xs font-semibold uppercase">{status.label}</div>
          <div className="text-[10px]">Current root-zone moisture</div>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <section className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground font-jakarta">Parcel State</h3>
            <Map size={16} className="text-muted-foreground" />
          </div>
          <div className="relative h-40 bg-gradient-to-br from-[#0F3D2E] to-[#1a5c3a] overflow-hidden">
            <svg viewBox="0 0 300 160" className="w-full h-full opacity-35" aria-hidden="true">
              {Array.from({ length: 7 }, (_, index) => <line key={"h" + index} x1="0" y1={index * 25} x2="300" y2={index * 25} stroke="#4ADE80" strokeWidth="0.5" />)}
              {Array.from({ length: 12 }, (_, index) => <line key={"v" + index} x1={index * 25} y1="0" x2={index * 25} y2="160" stroke="#4ADE80" strokeWidth="0.5" />)}
              <ellipse cx="150" cy="82" rx="80" ry="45" fill="rgba(74,222,128,0.15)" stroke="#4ADE80" strokeWidth="1.5" strokeDasharray="5,3" />
            </svg>
          </div>
          <div className="p-4 space-y-3">
            <ReadingRow icon={Droplets} label="Moisture" value={latestReading ? fmt(latestReading.soil_moisture_mm, " mm") : "-"} />
            <ReadingRow icon={CloudSun} label="Measured rain" value={latestReading ? fmt(latestReading.rainfall_mm, " mm") : "-"} />
            <ReadingRow icon={Thermometer} label="Temperature" value={latestReading?.temperature_c != null ? fmt(latestReading.temperature_c, " °C") : "-"} />
            <ReadingRow icon={Gauge} label="Field capacity" value={fmt(selected.field_capacity_mm, " mm")} />
            <div className="pt-2 border-t border-border text-[10px] text-muted-foreground">
              Latest reading origin: {latestReading?.data_origin || "unknown"}
            </div>
          </div>
        </section>

        <section className="bg-card border border-border rounded-2xl overflow-hidden flex flex-col">
          <div className="p-4 border-b border-border flex items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-foreground font-jakarta">Forecast Inputs</h3>
              <p className="text-[10px] text-muted-foreground mt-0.5">Open-Meteo FAO ET0 and precipitation</p>
            </div>
            <button
              onClick={refreshForecast}
              disabled={forecastLoading}
              title="Refresh parcel forecast"
              className="w-8 h-8 rounded-lg border border-border text-primary hover:bg-primary/10 inline-flex items-center justify-center disabled:opacity-60"
            >
              <RefreshCw size={15} className={forecastLoading ? "animate-spin" : ""} />
            </button>
          </div>
          <div className="p-4 flex-1">
            {forecastNotice && (
              <div className="mb-3 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
                {forecastNotice}
              </div>
            )}
            {forecasts.length ? (
              <div className="space-y-2">
                {forecasts.slice(0, 6).map((forecast) => (
                  <div key={forecast.id} className="grid grid-cols-[58px_1fr_1fr] items-center gap-2 text-xs">
                    <span className="font-semibold text-foreground">{formatDate(forecast.forecast_date)}</span>
                    <span className="text-muted-foreground">{fmt(forecast.precipitation_mm, " mm rain")}</span>
                    <span className="text-muted-foreground">{fmt(forecast.et0_fao_mm, " mm ET0")}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-full min-h-40 flex flex-col items-center justify-center text-center text-muted-foreground">
                <CloudSun size={28} className="mb-2 opacity-35" />
                <p className="text-xs">No stored forecast.</p>
                <p className="text-[10px] mt-1">Refresh before running a forecast-backed model.</p>
              </div>
            )}
          </div>
          <div className="p-3 border-t border-border text-[10px] text-muted-foreground flex items-center gap-1.5">
            <ShieldCheck size={12} className="text-primary" /> Forecast history remains stored for audit.
          </div>
        </section>

        <div className="space-y-5">
          <section className="bg-card border border-border rounded-2xl p-4 h-[238px] flex flex-col">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-1">Scenario Comparison</h3>
            <p className="text-[10px] text-muted-foreground mb-2">Forecast-driven root-zone water balance</p>
            <div className="flex-1">
              {simResult ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ReLineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="day" tick={{ fontSize: 9 }} stroke="none" />
                    <YAxis tick={{ fontSize: 9 }} stroke="none" domain={[0, "auto"]} />
                    <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                    <Line dataKey="baseline" name="Forecast baseline" stroke="#0B6E4F" strokeWidth={2} dot={false} />
                    <Line dataKey="scenario" name="Scenario" stroke="#F59E0B" strokeWidth={2} dot={false} />
                    <Line dataKey="capacity" name="Capacity" stroke="#3B82F6" strokeDasharray="3 3" dot={false} strokeWidth={1} />
                  </ReLineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-muted-foreground bg-muted/50 rounded-xl border border-dashed border-border">
                  Refresh forecast, then run a simulation.
                </div>
              )}
            </div>
          </section>

          <section className="bg-card border border-border rounded-2xl p-4">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-3">Simulation Controls</h3>
            <div className="space-y-3">
              <RangeControl
                label="Forecast horizon"
                value={simForm.horizon_days}
                min="3"
                max="16"
                suffix=" days"
                onChange={(value) => setSimForm({ ...simForm, horizon_days: value })}
              />
              <RangeControl
                label="Rainfall scenario"
                value={simForm.rainfall_factor}
                min="0"
                max="2"
                step="0.1"
                suffix="x"
                onChange={(value) => setSimForm({ ...simForm, rainfall_factor: value })}
              />
              <RangeControl
                label="Temperature delta"
                value={simForm.temperature_delta_c}
                min="-5"
                max="5"
                step="0.5"
                suffix=" °C"
                onChange={(value) => setSimForm({ ...simForm, temperature_delta_c: value })}
              />
              <button
                onClick={runSimulation}
                disabled={simLoading || !forecasts.length}
                className="w-full py-2 mt-2 bg-gradient-to-r from-primary to-[#2D9C72] text-white text-xs font-bold rounded-xl hover:shadow-lg hover:shadow-primary/20 transition-all flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <Play size={13} /> {simLoading ? "Running..." : "Run forecast scenario"}
              </button>
            </div>
          </section>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <section className="bg-card border border-border rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h3 className="text-sm font-bold text-foreground font-jakarta">Field Irrigation Log</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Record actual applications in mm. These records are part of calibration evidence.
              </p>
            </div>
            <Upload size={17} className="text-primary shrink-0" />
          </div>
          <form className="grid grid-cols-1 sm:grid-cols-2 gap-3" onSubmit={addIrrigationEvent}>
            <label className="grid gap-1 text-xs text-muted-foreground">
              Applied at
              <input
                type="datetime-local"
                required
                value={irrigationForm.occurred_at}
                onChange={(event) => setIrrigationForm({ ...irrigationForm, occurred_at: event.target.value })}
                className="h-9 rounded-lg border border-border px-2 text-foreground bg-background"
              />
            </label>
            <label className="grid gap-1 text-xs text-muted-foreground">
              Amount (mm)
              <input
                type="number"
                min="0.1"
                step="0.1"
                required
                value={irrigationForm.amount_mm}
                onChange={(event) => setIrrigationForm({ ...irrigationForm, amount_mm: event.target.value })}
                className="h-9 rounded-lg border border-border px-2 text-foreground bg-background"
              />
            </label>
            <label className="grid gap-1 text-xs text-muted-foreground">
              Method
              <select
                value={irrigationForm.method}
                onChange={(event) => setIrrigationForm({ ...irrigationForm, method: event.target.value })}
                className="h-9 rounded-lg border border-border px-2 text-foreground bg-background"
              >
                <option value="drip">Drip</option>
                <option value="sprinkler">Sprinkler</option>
                <option value="surface">Surface</option>
                <option value="other">Other</option>
              </select>
            </label>
            <label className="grid gap-1 text-xs text-muted-foreground">
              Recorded by
              <input
                required
                minLength="2"
                value={irrigationForm.recorded_by}
                onChange={(event) => setIrrigationForm({ ...irrigationForm, recorded_by: event.target.value })}
                className="h-9 rounded-lg border border-border px-2 text-foreground bg-background"
              />
            </label>
            <button
              type="submit"
              disabled={irrigationLoading}
              className="sm:col-span-2 h-9 rounded-lg border border-primary/20 bg-primary/10 text-primary text-xs font-bold hover:bg-primary/15 disabled:opacity-60"
            >
              {irrigationLoading ? "Saving application..." : "Record irrigation application"}
            </button>
          </form>
          <div className="mt-4 border-t border-border pt-3">
            <div className="flex flex-col sm:flex-row gap-2 mb-3">
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => setReadingFile(event.target.files?.[0] || null)}
                className="min-w-0 flex-1 text-xs text-muted-foreground file:mr-2 file:h-8 file:border-0 file:rounded-lg file:bg-muted file:px-3 file:text-xs file:font-semibold file:text-foreground"
                title="CSV requires recorded_at, soil_moisture_mm, rainfall_mm, and evapotranspiration_mm."
              />
              <button
                type="button"
                onClick={importFieldReadings}
                disabled={!readingFile || readingImportLoading}
                className="h-9 px-3 rounded-lg border border-primary/20 bg-primary/10 text-primary text-xs font-bold disabled:opacity-60"
              >
                {readingImportLoading ? "Importing..." : "Import readings"}
              </button>
            </div>
            {readingImportSummary && (
              <div className="mb-3 text-[11px] text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
                Imported {readingImportSummary.created} new and updated {readingImportSummary.updated} field readings.
                {readingImportSummary.rejected ? " Rejected " + readingImportSummary.rejected + " row(s)." : ""}
              </div>
            )}
            {irrigationEvents.length ? irrigationEvents.slice(0, 4).map((item) => (
              <div key={item.id} className="flex justify-between text-xs py-1.5">
                <span className="text-muted-foreground">{formatDateTime(item.occurred_at)} · {item.method}</span>
                <span className="font-semibold text-foreground">{fmt(item.amount_mm, " mm")}</span>
              </div>
            )) : (
              <p className="text-xs text-muted-foreground">No irrigation applications have been recorded yet.</p>
            )}
          </div>
        </section>

        <section className="bg-card border border-border rounded-2xl p-5">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div>
              <h3 className="text-sm font-bold text-foreground font-jakarta">Calibration Review</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Candidates are fitted from quality-checked field data and require named approval.
              </p>
            </div>
            <Target size={17} className="text-primary shrink-0" />
          </div>

          {calibrationError && <ErrorBanner message={calibrationError} compact />}
          {activeCalibration ? (
            <div className="mb-3 bg-emerald-50 border border-emerald-100 rounded-xl p-3 text-xs text-emerald-800">
              <div className="font-bold flex items-center gap-1"><CheckCircle2 size={14} /> Applied profile</div>
              <div className="mt-1">
                Kc {activeCalibration.parameters.crop_coefficient} · FC {fmt(activeCalibration.parameters.field_capacity_mm, " mm")} · reviewed by {activeCalibration.reviewed_by}
              </div>
            </div>
          ) : (
            <div className="mb-3 bg-amber-50 border border-amber-100 rounded-xl p-3 text-xs text-amber-800 flex gap-2">
              <TriangleAlert size={15} className="shrink-0 mt-0.5" />
              <span>No calibration is active. Default crop and soil parameters are being used.</span>
            </div>
          )}

          {candidateCalibration ? (
            <div className="border border-border rounded-xl p-3">
              <div className="flex justify-between text-xs">
                <span className="font-bold text-foreground">Review candidate #{candidateCalibration.id}</span>
                <span className="text-muted-foreground">RMSE {fmt(candidateCalibration.metrics.rmse_mm, " mm")}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-2 text-xs text-muted-foreground">
                <span>Kc: <b className="text-foreground">{candidateCalibration.parameters.crop_coefficient}</b></span>
                <span>FC: <b className="text-foreground">{fmt(candidateCalibration.parameters.field_capacity_mm, " mm")}</b></span>
              </div>
              <div className="flex gap-2 mt-3">
                <input
                  value={reviewer}
                  onChange={(event) => setReviewer(event.target.value)}
                  placeholder="Laboratory reviewer"
                  className="min-w-0 flex-1 h-8 rounded-lg border border-border px-2 text-xs bg-background"
                />
                <button
                  onClick={() => applyCalibration(candidateCalibration.id)}
                  disabled={applyLoading}
                  className="h-8 px-3 rounded-lg bg-primary text-white text-xs font-bold disabled:opacity-60"
                >
                  {applyLoading ? "Applying..." : "Apply"}
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={runCalibration}
              disabled={calibrationLoading}
              className="w-full h-10 rounded-lg border border-primary/20 bg-primary/10 text-primary text-xs font-bold hover:bg-primary/15 disabled:opacity-60 flex items-center justify-center gap-2"
            >
              <FlaskConical size={14} /> {calibrationLoading ? "Assessing field data..." : "Create calibration candidate"}
            </button>
          )}

          <div className="mt-3 text-[10px] text-muted-foreground flex items-start gap-1.5">
            <CalendarClock size={12} className="shrink-0 mt-0.5" />
            Calibration requires at least 14 daily root-zone readings marked as field data; demo and unknown data are excluded.
          </div>
        </section>
      </div>

      {detailLoading && <LoadingOverlay />}
    </div>
  );
}

function ReadingRow({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground flex items-center gap-2"><Icon size={14} /> {label}</span>
      <span className="font-semibold font-mono">{value}</span>
    </div>
  );
}

function RangeControl({ label, value, min, max, step = "1", suffix, onChange }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono font-semibold text-foreground">{value}{suffix}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full accent-primary"
      />
    </div>
  );
}

function ErrorBanner({ message, compact = false }) {
  return (
    <div className={(compact ? "mb-3 " : "") + "p-3 bg-red-50 border border-red-100 text-red-700 rounded-xl text-xs"}>
      {message}
    </div>
  );
}

function LoadingOverlay() {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
      <Activity size={40} className="animate-spin text-primary mb-4" />
      <p className="font-semibold">Loading parcel data...</p>
    </div>
  );
}