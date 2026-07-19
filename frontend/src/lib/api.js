import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function authenticatedHeaders(headers = {}) {
  const { data } = supabase ? await supabase.auth.getSession() : { data: {} };
  const token = data.session?.access_token;
  return {
    ...headers,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: await authenticatedHeaders({ "Content-Type": "application/json", ...options.headers }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export const veille = {
  listArticles: () => request("/veille/articles"),
  getArticle: (id) => request(`/veille/articles/${id}`),
  addSource: (data) => request("/veille/sources", { method: "POST", body: JSON.stringify(data) }),
  trigger: () => request("/veille/trigger", { method: "POST" }),
};

export const biblio = {
  listResearchers: () => request("/biblio/researchers"),
  addResearcher: (data) => request("/biblio/researchers", { method: "POST", body: JSON.stringify(data) }),
  syncResearcher: (id) => request(`/biblio/researchers/${id}/sync`, { method: "POST" }),
  downloadCV: async (id) => {
    const res = await fetch(`${API_BASE}/biblio/researchers/${id}/cv/pdf`, {
      headers: await authenticatedHeaders(),
    });
    if (!res.ok) {
      throw new Error(`API ${res.status}: ${await res.text()}`);
    }
    return {
      blob: await res.blob(),
      filename: `CV_researcher_${id}.pdf`,
    };
  },
};

export const health = () => fetch("http://localhost:8000/health").then((r) => r.json());

export const twin = {
  listParcels: () => request("/twin/parcels"),
  createParcel: (data) => request("/twin/parcels", { method: "POST", body: JSON.stringify(data) }),
  getParcel: (id) => request(`/twin/parcels/${id}`),
  listReadings: (parcelId, limit = 60) => request(`/twin/parcels/${parcelId}/readings?limit=${limit}`),
  addReading: (parcelId, data) => request(`/twin/parcels/${parcelId}/readings`, { method: "POST", body: JSON.stringify(data) }),
  recommend: (parcelId) => request(`/twin/parcels/${parcelId}/recommend`, { method: "POST" }),
  simulate: (parcelId, data) => request(`/twin/parcels/${parcelId}/simulate`, { method: "POST", body: JSON.stringify(data) }),
  listRecommendations: () => request("/twin/recommendations"),
};

export const simulation = {
  run: (parcelId, data) => request(`/simulation/parcels/${parcelId}/runs`, { method: "POST", body: JSON.stringify(data) }),
  listRuns: (parcelId, limit = 10) => request(`/simulation/parcels/${parcelId}/runs?limit=${limit}`),
  getRun: (runId) => request(`/simulation/runs/${runId}`),
};

export const optimisation = {
  run: (parcelId, data) => request(`/optimisation/parcels/${parcelId}/runs`, { method: "POST", body: JSON.stringify(data) }),
  listRuns: (parcelId, limit = 10) => request(`/optimisation/parcels/${parcelId}/runs?limit=${limit}`),
  getRun: (runId) => request(`/optimisation/runs/${runId}`),
};

export const fieldData = {
  listForecasts: (parcelId, days = 16) => request(`/twin/parcels/${parcelId}/forecasts?days=${days}`),
  refreshForecast: (parcelId) => request(`/twin/parcels/${parcelId}/forecasts/refresh`, { method: "POST" }),
  listIrrigationEvents: (parcelId, limit = 60) => request(`/twin/parcels/${parcelId}/irrigation-events?limit=${limit}`),
  addIrrigationEvent: (parcelId, data) => request(`/twin/parcels/${parcelId}/irrigation-events`, { method: "POST", body: JSON.stringify(data) }),
  listCalibrations: (parcelId, limit = 10) => request(`/twin/parcels/${parcelId}/calibrations?limit=${limit}`),
  runCalibration: (parcelId, data = {}) => request(`/twin/parcels/${parcelId}/calibrations/run`, { method: "POST", body: JSON.stringify(data) }),
  applyCalibration: (profileId, data) => request(`/twin/calibrations/${profileId}/apply`, { method: "POST", body: JSON.stringify(data) }),
  importReadings: (parcelId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return upload(`/twin/parcels/${parcelId}/readings/import`, formData);
  },
};

async function upload(path, formData) {
  const res = await fetch(API_BASE + path, {
    method: "POST",
    body: formData,
    headers: await authenticatedHeaders(),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}