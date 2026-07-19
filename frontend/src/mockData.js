import { Eye, BookOpen, Wifi, Cpu, Target, Database, Shield, Network } from "lucide-react";

export const activityData = [
  { month: "Jan", publications: 12, agents: 8, sensors: 142 },
  { month: "Feb", publications: 18, agents: 10, sensors: 156 },
  { month: "Mar", publications: 15, agents: 12, sensors: 168 },
  { month: "Apr", publications: 22, agents: 11, sensors: 174 },
  { month: "May", publications: 28, agents: 14, sensors: 189 },
  { month: "Jun", publications: 35, agents: 16, sensors: 201 },
  { month: "Jul", publications: 31, agents: 15, sensors: 198 },
];

export const iotData = Array.from({ length: 24 }, (_, i) => ({
  h: `${i}:00`,
  temp: 22 + Math.sin(i / 3) * 4 + Math.random(),
  humidity: 58 + Math.cos(i / 4) * 8 + Math.random(),
  pressure: 1013 + Math.sin(i / 6) * 3,
  flow: 2.4 + Math.random() * 0.8,
}));

export const agents = [
  { id: 1, name: "Scientific Watch Agent", icon: Eye, status: "active", task: "Scanning 847 new papers in Nature Climate", confidence: 94, executions: 1247, perf: 97 },
  { id: 2, name: "Bibliometric Agent", icon: BookOpen, status: "active", task: "Computing H-index for 23 researchers", confidence: 99, executions: 892, perf: 99 },
  { id: 3, name: "IoT Agent", icon: Wifi, status: "active", task: "Monitoring 312 sensors — 2 anomalies flagged", confidence: 88, executions: 45821, perf: 94 },
  { id: 4, name: "Simulation Agent", icon: Cpu, status: "running", task: "Monte Carlo simulation — iteration 4,820/10,000", confidence: 76, executions: 156, perf: 89 },
  { id: 5, name: "Optimization Agent", icon: Target, status: "idle", task: "Awaiting MODFLOW output — queue position 2", confidence: 82, executions: 334, perf: 91 },
  { id: 6, name: "MIS Agent", icon: Database, status: "active", task: "Generating Q2 dashboard reports", confidence: 96, executions: 2108, perf: 98 },
  { id: 7, name: "Quality Agent", icon: Shield, status: "active", task: "Validating dataset DS-2024-Q2-HYDRO", confidence: 91, executions: 678, perf: 95 },
  { id: 8, name: "Orchestrator Agent", icon: Network, status: "active", task: "Coordinating 7 sub-agents — 0 conflicts", confidence: 98, executions: 15203, perf: 99 },
];

export const publications = [
  { id: 1, title: "Groundwater Recharge Dynamics Under Climate Change Scenarios in Semi-Arid Regions", authors: "El-Amine, K., Bouziane, A., Chakir, R.", journal: "Journal of Hydrology", year: 2024, citations: 47, impact: 6.2, tags: ["Climate", "Hydrology", "AI"], status: "published" },
  { id: 2, title: "Deep Learning for Real-Time Remote Sensing Data Fusion in Environmental Monitoring", authors: "Mansouri, L., Ouali, S., Benali, T.", journal: "Remote Sensing", year: 2024, citations: 31, impact: 5.8, tags: ["AI", "Remote Sensing", "IoT"], status: "published" },
  { id: 3, title: "Digital Twin Framework for Aquifer System Simulation and Predictive Governance", authors: "Bouziane, A., El-Amine, K., Alami, M.", journal: "Environmental Modelling & Software", year: 2024, citations: 18, impact: 4.9, tags: ["Digital Twins", "Simulation"], status: "published" },
  { id: 4, title: "Multi-Agent Reinforcement Learning for Adaptive Water Resource Allocation", authors: "Chakir, R., Mansouri, L.", journal: "Water Resources Research", year: 2024, citations: 9, impact: 5.4, tags: ["AI Agents", "Water"], status: "in-review" },
];

export const projects = [
  { id: 1, title: "AquaPredict — AI-Powered Groundwater Forecasting", status: "active", progress: 68, budget: 2400000, spent: 1632000, team: 8, deadline: "Dec 2024", risk: "low", tags: ["AI", "Hydrology"] },
  { id: 2, title: "ClimateShield Digital Twin Platform", status: "active", progress: 41, budget: 3800000, spent: 1558000, team: 12, deadline: "Mar 2025", risk: "medium", tags: ["Digital Twins", "Climate"] },
  { id: 3, title: "SensorNet — National IoT Environmental Grid", status: "active", progress: 85, budget: 1900000, spent: 1615000, team: 6, deadline: "Sep 2024", risk: "low", tags: ["IoT", "Networks"] },
  { id: 4, title: "SOILS-AI Pedological Intelligence System", status: "planning", progress: 12, budget: 1200000, spent: 144000, team: 4, deadline: "Jun 2025", risk: "high", tags: ["AI", "Soil Science"] },
  { id: 5, title: "BioDiv Spatial Monitoring Observatory", status: "completed", progress: 100, budget: 980000, spent: 943000, team: 5, deadline: "Jul 2024", risk: "none", tags: ["Biodiversity", "GIS"] },
];

export const researchers = [
  { id: 1, name: "Dr. Karim El-Amine", role: "Principal Investigator", field: "Hydrogeology & AI", h: 24, pubs: 87, citations: 2841, avatar: "KE", active: true },
  { id: 2, name: "Dr. Aicha Bouziane", role: "Senior Researcher", field: "Climate Modeling", h: 19, pubs: 62, citations: 1920, avatar: "AB", active: true },
  { id: 3, name: "Prof. Rachid Chakir", role: "Department Head", field: "Machine Learning", h: 31, pubs: 124, citations: 5673, avatar: "RC", active: true },
  { id: 4, name: "Dr. Leila Mansouri", role: "Researcher", field: "Remote Sensing", h: 14, pubs: 38, citations: 847, avatar: "LM", active: false },
];
