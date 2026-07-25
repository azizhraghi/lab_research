import { useState, useEffect, useRef, useCallback } from "react";
import {
  LayoutDashboard, FolderKanban, BookOpen, Users, GraduationCap,
  Eye, Bot, Cpu, Wifi, Map, Database, FileText, Calendar,
  Newspaper, Settings, ChevronLeft, ChevronRight, Search,
  Bell, Moon, Sun, User, Menu, X, TrendingUp, Activity,
  Zap, Globe, BarChart3, ArrowUpRight, ArrowDownRight,
  CheckCircle, AlertCircle, Clock, Play, Pause, RefreshCw,
  Download, Upload, Filter, Plus, Star, ExternalLink,
  Thermometer, Droplets, Wind, Gauge, MapPin, Layers,
  Brain, Network, Shield, Target, FlaskConical, Microscope,
  Award, BookMarked, ChevronDown, MoreHorizontal, Satellite,
  Radio, Server, GitBranch, Cpu as CpuIcon, LineChart,
  PieChart, Hash, Bookmark, Share2, MessageSquare, Send,
  Mic, Sparkles, Heart, Eye as EyeIcon, ChevronUp, UserPlus,
  Mail, Linkedin, SquareCode, GraduationCap as Scholar,
  Leaf, Droplet, ThermometerSun, SatelliteDish, BarChart2,
  BrainCircuit, Sprout, Waves, Globe2, Cpu as IoTIcon, LogIn
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, LineChart as ReLineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart as RePieChart, Pie, Cell, RadialBarChart, RadialBar
} from "recharts";
import { useAuth } from "../auth/AuthContext";
import type { Article } from "../api/types";
import { useArticles, useTriggerScrape } from "../api/veille";
import {
  useParcels,
  useParcel,
  useParcelForecast,
  useRefreshForecast,
  useRunTwinSimulation,
  useSimulationRuns,
  useOptimisationRuns,
} from "../api/digitaltwin";

// ─── Types ─────────────────────────────────────────────────────────────────
type Page =
  | "home" | "dashboard" | "projects" | "publications" | "researchers"
  | "theses" | "watch" | "twins" | "iot" | "gis"
  | "datasets" | "events" | "news" | "admin"
  | "visitor";

// ─── Typewriter Hook ────────────────────────────────────────────────────────
function useTypewriter(texts: string[], speed = 60, pause = 2200) {
  const [displayed, setDisplayed] = useState("");
  const [idx, setIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [cursor, setCursor] = useState(true);

  useEffect(() => {
    const cursorTimer = setInterval(() => setCursor(c => !c), 530);
    return () => clearInterval(cursorTimer);
  }, []);

  useEffect(() => {
    const current = texts[idx];
    if (!deleting && charIdx < current.length) {
      const t = setTimeout(() => {
        setDisplayed(current.slice(0, charIdx + 1));
        setCharIdx(c => c + 1);
      }, speed);
      return () => clearTimeout(t);
    }
    if (!deleting && charIdx === current.length) {
      const t = setTimeout(() => setDeleting(true), pause);
      return () => clearTimeout(t);
    }
    if (deleting && charIdx > 0) {
      const t = setTimeout(() => {
        setDisplayed(current.slice(0, charIdx - 1));
        setCharIdx(c => c - 1);
      }, speed / 2);
      return () => clearTimeout(t);
    }
    if (deleting && charIdx === 0) {
      setDeleting(false);
      setIdx(i => (i + 1) % texts.length);
    }
  }, [charIdx, deleting, idx, texts, speed, pause]);

  return { displayed, cursor };
}

// ─── Animated Counter ───────────────────────────────────────────────────────
function AnimatedCounter({ target, suffix = "", prefix = "" }: { target: number; suffix?: string; prefix?: string }) {
  const [val, setVal] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    let start = 0;
    const step = target / 60;
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setVal(target); clearInterval(timer); }
      else setVal(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [target]);
  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>;
}

// ─── Particle Canvas ────────────────────────────────────────────────────────
function ParticleCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    let w = canvas.width = canvas.offsetWidth;
    let h = canvas.height = canvas.offsetHeight;
    const particles = Array.from({ length: 70 }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 2 + 1, o: Math.random() * 0.5 + 0.1
    }));
    let raf: number;
    function draw() {
      ctx.clearRect(0, 0, w, h);
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(74,222,128,${p.o})`;
        ctx.fill();
      });
      particles.forEach((a, i) => particles.slice(i + 1).forEach(b => {
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 120) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(45,156,114,${0.15 * (1 - d / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }));
      raf = requestAnimationFrame(draw);
    }
    draw();
    const onResize = () => { w = canvas.width = canvas.offsetWidth; h = canvas.height = canvas.offsetHeight; };
    window.addEventListener("resize", onResize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", onResize); };
  }, []);
  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-60" />;
}

// ─── Nav Item ───────────────────────────────────────────────────────────────
function NavItem({ icon: Icon, label, page, current, collapsed, onClick }: {
  icon: React.ElementType; label: string; page: Page;
  current: Page; collapsed: boolean; onClick: (p: Page) => void;
}) {
  const active = current === page;
  return (
    <button
      onClick={() => onClick(page)}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative
        ${active
          ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
        }`}
    >
      <Icon size={18} className={`shrink-0 ${active ? "text-white" : ""}`} />
      {!collapsed && <span className="truncate">{label}</span>}
      {collapsed && (
        <div className="absolute left-full ml-2 px-2 py-1 bg-foreground text-background text-xs rounded-lg opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
          {label}
        </div>
      )}
      {active && !collapsed && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent" />}
    </button>
  );
}

// ─── KPI Card ───────────────────────────────────────────────────────────────
function KPICard({ label, value, suffix = "", change, icon: Icon, color = "primary", trend }: {
  label: string; value: number; suffix?: string; change?: number;
  icon: React.ElementType; color?: string; trend?: number[];
}) {
  const colors: Record<string, string> = {
    primary: "from-primary/10 to-primary/5 border-primary/20",
    emerald: "from-emerald-50 to-emerald-50/50 border-emerald-200",
    amber: "from-amber-50 to-amber-50/50 border-amber-200",
    blue: "from-blue-50 to-blue-50/50 border-blue-200",
    purple: "from-purple-50 to-purple-50/50 border-purple-200",
  };
  const iconColors: Record<string, string> = {
    primary: "text-primary bg-primary/10",
    emerald: "text-emerald-600 bg-emerald-100",
    amber: "text-amber-600 bg-amber-100",
    blue: "text-blue-600 bg-blue-100",
    purple: "text-purple-600 bg-purple-100",
  };
  return (
    <div className={`bg-gradient-to-br ${colors[color]} border rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300`}>
      <div className="flex items-start justify-between mb-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${iconColors[color]}`}>
          <Icon size={20} />
        </div>
        {change !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full
            ${change >= 0 ? "text-emerald-700 bg-emerald-100" : "text-red-600 bg-red-100"}`}>
            {change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-foreground mb-1 font-jakarta">
        <AnimatedCounter target={value} suffix={suffix} />
      </div>
      <p className="text-sm text-muted-foreground">{label}</p>
      {trend && (
        <div className="mt-3 h-8">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trend.map((v, i) => ({ v, i }))}>
              <Area type="monotone" dataKey="v" stroke={color === "primary" ? "#0B6E4F" : color === "amber" ? "#F59E0B" : "#3B82F6"} fill={color === "primary" ? "rgba(11,110,79,0.1)" : color === "amber" ? "rgba(245,158,11,0.1)" : "rgba(59,130,246,0.1)"} strokeWidth={1.5} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// ─── Data ───────────────────────────────────────────────────────────────────
const activityData = [
  { month: "Jan", publications: 12, agents: 8, sensors: 142 },
  { month: "Feb", publications: 18, agents: 10, sensors: 156 },
  { month: "Mar", publications: 15, agents: 12, sensors: 168 },
  { month: "Apr", publications: 22, agents: 11, sensors: 174 },
  { month: "May", publications: 28, agents: 14, sensors: 189 },
  { month: "Jun", publications: 35, agents: 16, sensors: 201 },
  { month: "Jul", publications: 31, agents: 15, sensors: 198 },
];

const iotData = Array.from({ length: 24 }, (_, i) => ({
  h: `${i}:00`,
  temp: 22 + Math.sin(i / 3) * 4 + Math.random(),
  humidity: 58 + Math.cos(i / 4) * 8 + Math.random(),
  pressure: 1013 + Math.sin(i / 6) * 3,
  flow: 2.4 + Math.random() * 0.8,
}));

const agents = [
  { id: 1, name: "Scientific Watch Agent", icon: Eye, status: "active", task: "Scanning 847 new papers in Nature Climate", confidence: 94, executions: 1247, perf: 97 },
  { id: 2, name: "Bibliometric Agent", icon: BookOpen, status: "active", task: "Computing H-index for 23 researchers", confidence: 99, executions: 892, perf: 99 },
  { id: 3, name: "IoT Agent", icon: Wifi, status: "active", task: "Monitoring 312 sensors — 2 anomalies flagged", confidence: 88, executions: 45821, perf: 94 },
  { id: 4, name: "Simulation Agent", icon: Cpu, status: "running", task: "Monte Carlo simulation — iteration 4,820/10,000", confidence: 76, executions: 156, perf: 89 },
  { id: 5, name: "Optimization Agent", icon: Target, status: "idle", task: "Awaiting MODFLOW output — queue position 2", confidence: 82, executions: 334, perf: 91 },
  { id: 6, name: "MIS Agent", icon: Database, status: "active", task: "Generating Q2 dashboard reports", confidence: 96, executions: 2108, perf: 98 },
  { id: 7, name: "Quality Agent", icon: Shield, status: "active", task: "Validating dataset DS-2024-Q2-HYDRO", confidence: 91, executions: 678, perf: 95 },
  { id: 8, name: "Orchestrator Agent", icon: Network, status: "active", task: "Coordinating 7 sub-agents — 0 conflicts", confidence: 98, executions: 15203, perf: 99 },
];

const publications = [
  { id: 1, title: "Groundwater Recharge Dynamics Under Climate Change Scenarios in Semi-Arid Regions", authors: "El-Amine, K., Bouziane, A., Chakir, R.", journal: "Journal of Hydrology", year: 2024, citations: 47, impact: 6.2, tags: ["Climate", "Hydrology", "AI"], status: "published" },
  { id: 2, title: "Deep Learning for Real-Time Remote Sensing Data Fusion in Environmental Monitoring", authors: "Mansouri, L., Ouali, S., Benali, T.", journal: "Remote Sensing", year: 2024, citations: 31, impact: 5.8, tags: ["AI", "Remote Sensing", "IoT"], status: "published" },
  { id: 3, title: "Digital Twin Framework for Aquifer System Simulation and Predictive Governance", authors: "Bouziane, A., El-Amine, K., Alami, M.", journal: "Environmental Modelling & Software", year: 2024, citations: 18, impact: 4.9, tags: ["Digital Twins", "Simulation"], status: "published" },
  { id: 4, title: "Multi-Agent Reinforcement Learning for Adaptive Water Resource Allocation", authors: "Chakir, R., Mansouri, L.", journal: "Water Resources Research", year: 2024, citations: 9, impact: 5.4, tags: ["AI Agents", "Water"], status: "in-review" },
];

const projects = [
  { id: 1, title: "AquaPredict — AI-Powered Groundwater Forecasting", status: "active", progress: 68, budget: 2400000, spent: 1632000, team: 8, deadline: "Dec 2024", risk: "low", tags: ["AI", "Hydrology"] },
  { id: 2, title: "ClimateShield Digital Twin Platform", status: "active", progress: 41, budget: 3800000, spent: 1558000, team: 12, deadline: "Mar 2025", risk: "medium", tags: ["Digital Twins", "Climate"] },
  { id: 3, title: "SensorNet — National IoT Environmental Grid", status: "active", progress: 85, budget: 1900000, spent: 1615000, team: 6, deadline: "Sep 2024", risk: "low", tags: ["IoT", "Networks"] },
  { id: 4, title: "SOILS-AI Pedological Intelligence System", status: "planning", progress: 12, budget: 1200000, spent: 144000, team: 4, deadline: "Jun 2025", risk: "high", tags: ["AI", "Soil Science"] },
  { id: 5, title: "BioDiv Spatial Monitoring Observatory", status: "completed", progress: 100, budget: 980000, spent: 943000, team: 5, deadline: "Jul 2024", risk: "none", tags: ["Biodiversity", "GIS"] },
];

const researchers = [
  { id: 1, name: "Dr. Karim El-Amine", role: "Principal Investigator", field: "Hydrogeology & AI", h: 24, pubs: 87, citations: 2841, avatar: "KE", active: true },
  { id: 2, name: "Dr. Aicha Bouziane", role: "Senior Researcher", field: "Climate Modeling", h: 19, pubs: 62, citations: 1920, avatar: "AB", active: true },
  { id: 3, name: "Prof. Rachid Chakir", role: "Department Head", field: "Machine Learning", h: 31, pubs: 124, citations: 5673, avatar: "RC", active: true },
  { id: 4, name: "Dr. Leila Mansouri", role: "Researcher", field: "Remote Sensing", h: 14, pubs: 38, citations: 847, avatar: "LM", active: false },
];

const COLORS = ["#0B6E4F", "#2D9C72", "#4ADE80", "#F59E0B", "#3B82F6"];
const pubTypeData = [
  { name: "Journal Articles", value: 143 }, { name: "Conference Papers", value: 68 },
  { name: "Book Chapters", value: 24 }, { name: "Policy Briefs", value: 31 },
];

// ─── Sidebar ────────────────────────────────────────────────────────────────
function Sidebar({ page, setPage, collapsed, setCollapsed, dark }: {
  page: Page; setPage: (p: Page) => void;
  collapsed: boolean; setCollapsed: (v: boolean) => void; dark: boolean;
}) {
  const nav: { icon: React.ElementType; label: string; page: Page }[] = [
    { icon: LayoutDashboard, label: "Dashboard", page: "dashboard" },
    { icon: FolderKanban, label: "Research Projects", page: "projects" },
    { icon: BookOpen, label: "Publications", page: "publications" },
    { icon: Users, label: "Researchers", page: "researchers" },
    { icon: GraduationCap, label: "Theses & Masters", page: "theses" },
    { icon: Eye, label: "Scientific Watch", page: "watch" },
    { icon: Cpu, label: "Digital Twins", page: "twins" },
    { icon: Wifi, label: "IoT Monitoring", page: "iot" },
    { icon: Map, label: "GIS Maps", page: "gis" },
    { icon: Database, label: "Open Datasets", page: "datasets" },
    { icon: Globe, label: "Events", page: "events" },
    { icon: Newspaper, label: "News", page: "news" },
    { icon: Settings, label: "Administration", page: "admin" },
  ];

  return (
    <aside className={`flex flex-col h-full ${dark ? "bg-[#0A1F16]" : "bg-white"} border-r border-border transition-all duration-300 ${collapsed ? "w-16" : "w-60"} shrink-0 z-20`}>
      {/* Logo */}
      <div className={`flex items-center gap-3 px-3 py-5 border-b border-border ${collapsed ? "justify-center" : ""}`}>
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center shrink-0 shadow-lg shadow-primary/30">
          <FlaskConical size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div>
            <div className="font-bold text-sm text-foreground font-jakarta leading-tight">LabAI Research</div>
            <div className="text-[10px] text-muted-foreground">Ecosystem Platform</div>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden px-2 py-3 space-y-0.5 scrollbar-hide">
        <button
          onClick={() => setPage("home")}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group relative mb-2
            ${page === "home" ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "text-muted-foreground hover:bg-secondary hover:text-foreground"}`}
        >
          <Microscope size={18} className="shrink-0" />
          {!collapsed && <span>Home</span>}
        </button>
        {nav.map(n => (
          <NavItem key={n.page} {...n} current={page} collapsed={collapsed} onClick={setPage} />
        ))}
      </nav>

      {/* Visitor Portal shortcut */}
      <div className="p-2 border-t border-border">
        <button
          onClick={() => setPage("visitor")}
          className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold mb-2 transition-all
            ${page === "visitor"
              ? "bg-accent text-[#0F3D2E]"
              : "bg-gradient-to-r from-primary/15 to-primary/5 text-primary hover:from-primary hover:to-[#2D9C72] hover:text-white"}`}
        >
          <Globe2 size={15} className="shrink-0" />
          {!collapsed && <span>Public Portal</span>}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center py-2 rounded-xl hover:bg-secondary text-muted-foreground transition-colors"
        >
          {collapsed ? <ChevronRight size={16} /> : <><ChevronLeft size={16} /><span className="ml-2 text-xs">Collapse</span></>}
        </button>
      </div>
    </aside>
  );
}

// ─── Top Nav ────────────────────────────────────────────────────────────────
function TopNav({ dark, setDark, page, onSignOut }: { dark: boolean; setDark: (v: boolean) => void; page: Page; onSignOut: () => void }) {
  const [notifs, setNotifs] = useState(5);
  const labels: Record<Page, string> = {
    home: "Home", dashboard: "Dashboard", projects: "Research Projects",
    publications: "Publications", researchers: "Researchers", theses: "Theses & Masters",
    watch: "Scientific Watch", twins: "Digital Twins",
    iot: "IoT Monitoring", gis: "GIS Maps", datasets: "Open Datasets",
    events: "Events", news: "News & Updates", admin: "Administration", visitor: "Public Visitor Portal",
  };
  return (
    <header className={`h-14 flex items-center px-6 gap-4 border-b border-border ${dark ? "bg-[#0A1F16]" : "bg-white/80 backdrop-blur-md"} sticky top-0 z-10`}>
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Platform</span>
        <ChevronRight size={14} />
        <span className="text-foreground font-medium">{labels[page]}</span>
      </div>

      <div className="flex-1" />

      {/* Search */}
      <div className="relative hidden md:flex">
        <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
        <input
          placeholder="Search across platform..."
          className="w-64 pl-9 pr-4 py-1.5 text-sm bg-muted rounded-xl border border-border focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all"
        />
        <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] text-muted-foreground border border-border rounded px-1">⌘K</kbd>
      </div>

      {/* AI Btn */}
      <button className="flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-primary to-[#2D9C72] text-white text-xs font-semibold rounded-xl hover:shadow-lg hover:shadow-primary/25 transition-all">
        <Brain size={14} />
        <span className="hidden sm:inline">AI Assistant</span>
      </button>

      {/* Notifs */}
      <button className="relative p-2 rounded-xl hover:bg-secondary text-muted-foreground transition-colors" onClick={() => setNotifs(0)}>
        <Bell size={18} />
        {notifs > 0 && <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">{notifs}</span>}
      </button>

      {/* Dark mode */}
      <button onClick={() => setDark(!dark)} className="p-2 rounded-xl hover:bg-secondary text-muted-foreground transition-colors">
        {dark ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      {/* Profile */}
      <div className="flex items-center gap-2 pl-2">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white text-xs font-bold">KE</div>
        <div className="hidden md:block text-left">
          <div className="text-xs font-semibold text-foreground">Dr. El-Amine</div>
          <div className="text-[10px] text-muted-foreground">Principal Investigator</div>
        </div>
        <button
          onClick={onSignOut}
          title="Sign out"
          className="ml-1 p-1.5 rounded-xl hover:bg-red-50 text-muted-foreground hover:text-red-500 transition-colors"
        >
          <LogIn size={15} className="rotate-180" />
        </button>
      </div>
    </header>
  );
}

// ─── HOME PAGE ──────────────────────────────────────────────────────────────
function HomePage({ setPage }: { setPage: (p: Page) => void }) {
  const { displayed, cursor } = useTypewriter([
    "Advancing Science Through AI",
    "Pioneering Digital Twin Research",
    "Environmental Intelligence Platform",
    "World-Class Research Ecosystem",
  ]);

  const stats = [
    { label: "Active Projects", value: 47, suffix: "", icon: FolderKanban },
    { label: "Publications", value: 312, suffix: "+", icon: BookOpen },
    { label: "Researchers", value: 84, suffix: "", icon: Users },
    { label: "IoT Sensors", value: 1247, suffix: "", icon: Wifi },
    { label: "AI Agents Running", value: 8, suffix: "", icon: Bot },
    { label: "Datasets Published", value: 156, suffix: "+", icon: Database },
  ];

  const partners = ["CNRS", "MIT", "WHO", "UNEP", "UNESCO", "WMO", "IRD", "FAO"];

  return (
    <div className="overflow-y-auto h-full scrollbar-hide">
      {/* Hero */}
      <section className="relative min-h-[520px] bg-gradient-to-br from-[#0F3D2E] via-[#0B6E4F] to-[#1a7a5a] overflow-hidden flex items-center">
        <ParticleCanvas />
        {/* Decorative rings */}
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[600px] h-[600px] border border-white/5 rounded-full" />
        <div className="absolute right-20 top-1/2 -translate-y-1/2 w-[400px] h-[400px] border border-white/8 rounded-full" />
        <div className="absolute right-48 top-1/2 -translate-y-1/2 w-[200px] h-[200px] border border-white/10 rounded-full" />

        <div className="relative z-10 px-10 py-16 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/10 border border-white/20 rounded-full text-xs text-white/90 mb-6 backdrop-blur-sm">
            <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
            AI-Powered Research Laboratory Platform — v3.2.0
          </div>

          <h1 className="text-5xl lg:text-6xl font-extrabold text-white font-jakarta leading-tight mb-2">
            {displayed}
            <span className={`inline-block w-0.5 h-12 bg-accent ml-1 align-middle transition-opacity ${cursor ? "opacity-100" : "opacity-0"}`} />
          </h1>
          <p className="text-lg text-white/70 max-w-2xl mt-4 mb-8 leading-relaxed">
            An integrated research ecosystem combining AI agents, digital twins, IoT monitoring, and GIS intelligence to accelerate environmental science and sustainable development.
          </p>

          <div className="flex flex-wrap gap-3">
            <button onClick={() => setPage("dashboard")} className="flex items-center gap-2 px-6 py-3 bg-accent text-[#0F3D2E] font-bold rounded-xl hover:bg-accent/90 hover:shadow-xl hover:shadow-accent/20 transition-all">
              <LayoutDashboard size={18} />
              Open Dashboard
            </button>
            <button onClick={() => setPage("twins")} className="flex items-center gap-2 px-6 py-3 bg-white/10 text-white border border-white/20 font-semibold rounded-xl hover:bg-white/20 transition-all backdrop-blur-sm">
              <Cpu size={18} />
              Explore Digital Twins
            </button>
            <button onClick={() => setPage("agents")} className="flex items-center gap-2 px-6 py-3 bg-white/10 text-white border border-white/20 font-semibold rounded-xl hover:bg-white/20 transition-all backdrop-blur-sm">
              <Bot size={18} />
              AI Agents
            </button>
          </div>
        </div>

        {/* Floating metrics */}
        <div className="absolute right-8 top-1/2 -translate-y-1/2 hidden xl:flex flex-col gap-3">
          {[
            { label: "Papers Indexed Today", value: "847", color: "bg-white/10" },
            { label: "Sensor Readings/sec", value: "12.4K", color: "bg-accent/20" },
            { label: "Active Simulations", value: "3", color: "bg-white/10" },
          ].map(m => (
            <div key={m.label} className={`${m.color} backdrop-blur-sm border border-white/15 rounded-2xl p-4 text-white min-w-[160px]`}>
              <div className="text-2xl font-bold font-jakarta">{m.value}</div>
              <div className="text-xs text-white/70 mt-0.5">{m.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-white border-b border-border px-10 py-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {stats.map(s => (
            <div key={s.label} className="text-center group">
              <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mx-auto mb-2 group-hover:bg-primary group-hover:text-white transition-colors">
                <s.icon size={18} />
              </div>
              <div className="text-2xl font-extrabold text-foreground font-jakarta">
                <AnimatedCounter target={s.value} suffix={s.suffix} />
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="px-10 py-12">
        <h2 className="text-2xl font-bold text-foreground font-jakarta mb-2">Platform Capabilities</h2>
        <p className="text-muted-foreground mb-8">A complete scientific research ecosystem — from raw sensor data to AI-powered insights.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[
            { icon: Bot, title: "AI Agent Orchestra", desc: "8 specialized AI agents working in concert — from bibliometrics to simulation and quality control.", page: "agents" as Page, color: "from-primary/10 to-emerald-50" },
            { icon: Cpu, title: "Digital Twins", desc: "High-fidelity digital replicas of environmental systems with real-time synchronization.", page: "twins" as Page, color: "from-blue-50 to-indigo-50" },
            { icon: Wifi, title: "IoT Monitoring Grid", desc: "1,247 networked sensors streaming live environmental data across 23 monitoring stations.", page: "iot" as Page, color: "from-amber-50 to-orange-50" },
            { icon: Map, title: "GIS Intelligence", desc: "Spatial analytics and interactive mapping for geographic pattern discovery.", page: "gis" as Page, color: "from-teal-50 to-cyan-50" },
            { icon: BookOpen, title: "Publication Hub", desc: "312+ peer-reviewed publications with bibliometric analytics and citation tracking.", page: "publications" as Page, color: "from-purple-50 to-pink-50" },
            { icon: Database, title: "Open Data Portal", desc: "156 curated datasets with API access, notebook previews, and geospatial downloads.", page: "datasets" as Page, color: "from-rose-50 to-red-50" },
          ].map(f => (
            <button
              key={f.title}
              onClick={() => setPage(f.page)}
              className={`text-left bg-gradient-to-br ${f.color} border border-border rounded-2xl p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group`}
            >
              <div className="w-12 h-12 rounded-2xl bg-white shadow-sm flex items-center justify-center mb-4 group-hover:shadow-md transition-shadow">
                <f.icon size={22} className="text-primary" />
              </div>
              <h3 className="font-bold text-foreground font-jakarta mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              <div className="flex items-center gap-1 text-primary text-xs font-semibold mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                Explore <ArrowUpRight size={14} />
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* Partners */}
      <section className="px-10 py-10 bg-white border-t border-border">
        <p className="text-center text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-6">International Partners & Networks</p>
        <div className="flex flex-wrap justify-center gap-8">
          {partners.map(p => (
            <div key={p} className="px-6 py-3 border border-border rounded-xl text-sm font-semibold text-muted-foreground hover:text-primary hover:border-primary/30 hover:bg-primary/5 transition-all cursor-pointer">
              {p}
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0F3D2E] text-white/70 px-10 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {[
            { title: "Research", links: ["Projects", "Publications", "Datasets", "Theses"] },
            { title: "Technology", links: ["AI Agents", "Digital Twins", "IoT Grid", "GIS Maps"] },
            { title: "Community", links: ["Researchers", "Events", "Training", "News"] },
            { title: "Legal", links: ["Open Data", "Privacy Policy", "Accessibility", "Contact"] },
          ].map(col => (
            <div key={col.title}>
              <h4 className="text-white text-sm font-semibold mb-3">{col.title}</h4>
              <ul className="space-y-2">
                {col.links.map(l => <li key={l} className="text-xs hover:text-white cursor-pointer transition-colors">{l}</li>)}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-white/10 pt-6 flex items-center justify-between text-xs">
          <span>© 2024 LabAI Research Institute — All rights reserved</span>
          <span>Built with AI · Open Science · Environmental Excellence</span>
        </div>
      </footer>
    </div>
  );
}

// ─── DASHBOARD PAGE ─────────────────────────────────────────────────────────
function DashboardPage() {
  const kpis = [
    { label: "Active Projects", value: 47, change: 12, icon: FolderKanban, color: "primary", trend: [8, 14, 11, 18, 22, 19, 25, 28, 31, 35] },
    { label: "Researchers", value: 84, change: 4, icon: Users, color: "emerald", trend: [70, 72, 74, 75, 78, 80, 80, 82, 83, 84] },
    { label: "Publications (2024)", value: 312, change: 18, icon: BookOpen, color: "blue", trend: [210, 230, 245, 258, 270, 280, 292, 300, 308, 312] },
    { label: "IoT Sensors Online", value: 1247, change: -2, icon: Wifi, color: "amber", trend: [1180, 1200, 1220, 1238, 1242, 1255, 1248, 1250, 1249, 1247] },
    { label: "AI Executions Today", value: 8432, change: 31, icon: Bot, color: "purple", trend: [3000, 4200, 5100, 5800, 6400, 7000, 7400, 7900, 8200, 8432] },
    { label: "Datasets Published", value: 156, change: 8, icon: Database, color: "primary", trend: [110, 118, 124, 130, 136, 141, 146, 150, 153, 156] },
  ];

  const deadlines = [
    { project: "AquaPredict Deliverable D3", date: "Sep 15, 2024", days: 12, status: "urgent" },
    { project: "IoT Grid Q3 Report", date: "Sep 30, 2024", days: 27, status: "normal" },
    { project: "ClimateShield Paper Submission", date: "Oct 10, 2024", days: 37, status: "normal" },
    { project: "SOILS-AI Kick-off Meeting", date: "Oct 20, 2024", days: 47, status: "low" },
  ];

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full scrollbar-hide">
      {/* KPIs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-foreground font-jakarta">Platform Overview</h2>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
            Live — Updated 2s ago
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          {kpis.map(k => <KPICard key={k.label} {...k} />)}
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Activity chart */}
        <div className="lg:col-span-2 bg-card border border-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-foreground font-jakarta">Research Activity</h3>
              <p className="text-xs text-muted-foreground">Publications, AI executions & sensor readings</p>
            </div>
            <select className="text-xs border border-border rounded-lg px-2 py-1 bg-background text-muted-foreground">
              <option>Last 7 months</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={activityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="none" />
              <YAxis tick={{ fontSize: 11 }} stroke="none" />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid var(--border)", fontSize: 12 }} />
              <Area type="monotone" dataKey="publications" name="Publications" stroke="#0B6E4F" fill="rgba(11,110,79,0.1)" strokeWidth={2} />
              <Area type="monotone" dataKey="agents" name="AI Agents" stroke="#4ADE80" fill="rgba(74,222,128,0.08)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Publications by type */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-1">Publication Types</h3>
          <p className="text-xs text-muted-foreground mb-4">2024 breakdown</p>
          <ResponsiveContainer width="100%" height={180}>
            <RePieChart>
              <Pie data={pubTypeData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                {pubTypeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 12, fontSize: 12 }} />
            </RePieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {pubTypeData.map((d, i) => (
              <div key={d.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: COLORS[i] }} />
                  <span className="text-muted-foreground">{d.name}</span>
                </div>
                <span className="font-semibold text-foreground">{d.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Activity Feed */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Activity Feed</h3>
          <div className="space-y-3">
            {[
              { icon: BookOpen, text: "New publication submitted to Nature Hydrology", time: "2m ago", color: "bg-primary/10 text-primary" },
              { icon: Bot, text: "Bibliometric Agent completed H-index update for 23 researchers", time: "14m ago", color: "bg-accent/20 text-emerald-700" },
              { icon: Wifi, text: "Sensor SN-142 anomaly detected — temperature spike 4.2°C", time: "28m ago", color: "bg-amber-100 text-amber-700" },
              { icon: Cpu, text: "Digital Twin Simulation #4820 completed successfully", time: "1h ago", color: "bg-blue-100 text-blue-700" },
              { icon: Users, text: "Dr. Mansouri added to ClimateShield project team", time: "3h ago", color: "bg-purple-100 text-purple-700" },
            ].map((a, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${a.color}`}>
                  <a.icon size={13} />
                </div>
                <div>
                  <p className="text-xs text-foreground leading-snug">{a.text}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{a.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Deadlines */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Upcoming Deadlines</h3>
          <div className="space-y-3">
            {deadlines.map((d, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-muted rounded-xl">
                <div className={`w-10 h-10 rounded-xl flex flex-col items-center justify-center text-xs font-bold shrink-0
                  ${d.status === "urgent" ? "bg-red-100 text-red-600" : d.status === "normal" ? "bg-amber-100 text-amber-700" : "bg-secondary text-primary"}`}>
                  <span className="text-base leading-none">{d.days}</span>
                  <span className="text-[9px] font-normal">days</span>
                </div>
                <div>
                  <p className="text-xs font-medium text-foreground leading-snug">{d.project}</p>
                  <p className="text-[10px] text-muted-foreground">{d.date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Publications */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-foreground font-jakarta">Recent Publications</h3>
            <span className="text-xs text-primary font-semibold cursor-pointer">View all →</span>
          </div>
          <div className="space-y-3">
            {publications.slice(0, 3).map(p => (
              <div key={p.id} className="border-l-2 border-primary/30 pl-3">
                <p className="text-xs font-medium text-foreground leading-snug line-clamp-2">{p.title}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{p.journal} · {p.year} · {p.citations} citations</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── PROJECTS PAGE ──────────────────────────────────────────────────────────
function ProjectsPage() {
  const [view, setView] = useState<"kanban" | "timeline">("kanban");
  const statusCols = ["planning", "active", "completed"];
  const statusLabels: Record<string, string> = { planning: "Planning", active: "Active", completed: "Completed" };
  const statusColors: Record<string, string> = {
    planning: "bg-amber-100 text-amber-700 border-amber-200",
    active: "bg-emerald-100 text-emerald-700 border-emerald-200",
    completed: "bg-blue-100 text-blue-700 border-blue-200",
  };
  const riskColors: Record<string, string> = {
    low: "text-emerald-600", medium: "text-amber-600", high: "text-red-500", none: "text-muted-foreground",
  };

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Research Projects</h2>
          <p className="text-sm text-muted-foreground mt-0.5">47 projects · 8 active · MAD 12.4M total budget</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-muted rounded-xl p-1 gap-1">
            {(["kanban", "timeline"] as const).map(v => (
              <button key={v} onClick={() => setView(v)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize
                ${view === v ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
                {v}
              </button>
            ))}
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl hover:bg-primary/90 transition-colors">
            <Plus size={14} /> New Project
          </button>
        </div>
      </div>

      {view === "kanban" && (
        <div className="grid grid-cols-3 gap-5">
          {statusCols.map(status => (
            <div key={status}>
              <div className="flex items-center justify-between mb-3">
                <div className={`px-3 py-1 text-xs font-semibold rounded-full border ${statusColors[status]}`}>
                  {statusLabels[status]}
                </div>
                <span className="text-xs text-muted-foreground">{projects.filter(p => p.status === status).length}</span>
              </div>
              <div className="space-y-3">
                {projects.filter(p => p.status === status).map(proj => (
                  <div key={proj.id} className="bg-card border border-border rounded-2xl p-4 hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-sm font-semibold text-foreground leading-tight pr-2 group-hover:text-primary transition-colors">{proj.title}</h4>
                      <MoreHorizontal size={16} className="text-muted-foreground shrink-0 mt-0.5" />
                    </div>
                    <div className="flex flex-wrap gap-1 mb-3">
                      {proj.tags.map(t => <span key={t} className="px-2 py-0.5 bg-primary/8 text-primary text-[10px] font-medium rounded-full">{t}</span>)}
                    </div>
                    {/* Progress */}
                    <div className="mb-3">
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="font-semibold text-foreground">{proj.progress}%</span>
                      </div>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-primary to-[#2D9C72] rounded-full transition-all" style={{ width: `${proj.progress}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                      <div className="flex items-center gap-1"><Users size={11} />{proj.team} members</div>
                      <div className="flex items-center gap-1"><Clock size={11} />{proj.deadline}</div>
                      <div className={`font-semibold ${riskColors[proj.risk]}`}>Risk: {proj.risk}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {view === "timeline" && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-border">
            <h3 className="font-bold text-foreground font-jakarta">Project Timeline — 2024</h3>
          </div>
          <div className="overflow-x-auto">
            <div className="p-5 min-w-[800px]">
              {projects.map((proj, i) => (
                <div key={proj.id} className="flex items-center gap-4 mb-4">
                  <div className="w-56 shrink-0">
                    <p className="text-xs font-medium text-foreground truncate">{proj.title}</p>
                  </div>
                  <div className="flex-1 h-8 bg-muted rounded-xl relative overflow-hidden">
                    <div
                      className="absolute top-1 bottom-1 rounded-lg bg-gradient-to-r from-primary to-[#2D9C72] flex items-center px-2"
                      style={{ left: `${i * 5}%`, width: `${proj.progress / 100 * (80 - i * 5)}%` }}
                    >
                      <span className="text-[10px] text-white font-semibold truncate">{proj.progress}%</span>
                    </div>
                  </div>
                  <div className="w-24 text-xs text-muted-foreground shrink-0 text-right">{proj.deadline}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── PUBLICATIONS PAGE ───────────────────────────────────────────────────────
function PublicationsPage() {
  const [filter, setFilter] = useState("all");
  const tags = ["All", "AI", "Hydrology", "Climate", "Remote Sensing", "Digital Twins", "IoT"];

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Publications</h2>
          <p className="text-sm text-muted-foreground">312 publications · 14,832 total citations · 5.6 avg impact factor</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl">
          <Download size={14} /> Export BibTeX
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "H-Index (Lab)", value: "38", icon: Award, color: "text-primary" },
          { label: "Total Citations", value: "14,832", icon: Star, color: "text-amber-600" },
          { label: "Avg Impact Factor", value: "5.6", icon: TrendingUp, color: "text-blue-600" },
          { label: "Open Access", value: "74%", icon: Globe, color: "text-emerald-600" },
        ].map(s => (
          <div key={s.label} className="bg-card border border-border rounded-2xl p-4 flex items-center gap-3">
            <s.icon size={22} className={s.color} />
            <div>
              <div className="text-xl font-bold text-foreground font-jakarta">{s.value}</div>
              <div className="text-xs text-muted-foreground">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        {tags.map(t => (
          <button key={t} onClick={() => setFilter(t.toLowerCase())}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors
              ${filter === t.toLowerCase() ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-secondary hover:text-foreground"}`}>
            {t}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-2">
          <div className="relative">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input placeholder="Search publications..." className="pl-8 pr-3 py-1.5 text-xs bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 w-52" />
          </div>
        </div>
      </div>

      {/* Publication cards */}
      <div className="space-y-4">
        {publications.map(pub => (
          <div key={pub.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md hover:border-primary/20 transition-all group">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full
                    ${pub.status === "published" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                    {pub.status === "published" ? "Published" : "In Review"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">{pub.year}</span>
                </div>
                <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors mb-1 leading-snug">{pub.title}</h3>
                <p className="text-xs text-muted-foreground mb-2">{pub.authors}</p>
                <p className="text-xs font-semibold text-primary">{pub.journal}</p>
              </div>
              <div className="shrink-0 text-right">
                <div className="text-2xl font-extrabold text-foreground font-jakarta">{pub.citations}</div>
                <div className="text-[10px] text-muted-foreground">citations</div>
                <div className="mt-2 text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">IF {pub.impact}</div>
              </div>
            </div>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
              <div className="flex gap-1">
                {pub.tags.map(t => <span key={t} className="px-2 py-0.5 bg-primary/8 text-primary text-[10px] rounded-full">{t}</span>)}
              </div>
              <div className="flex items-center gap-3 text-muted-foreground">
                <button className="flex items-center gap-1 text-[10px] hover:text-primary transition-colors"><Download size={12} /> PDF</button>
                <button className="flex items-center gap-1 text-[10px] hover:text-primary transition-colors"><ExternalLink size={12} /> DOI</button>
                <button className="flex items-center gap-1 text-[10px] hover:text-primary transition-colors"><Bookmark size={12} /> Save</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── RESEARCHERS PAGE ────────────────────────────────────────────────────────
function ResearchersPage() {
  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Research Team</h2>
          <p className="text-sm text-muted-foreground">84 researchers · 12 departments · 6 countries</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl"><Plus size={14} />Add Researcher</button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-5">
        {researchers.map(r => (
          <div key={r.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all group">
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white font-bold text-lg shrink-0 shadow-md">
                {r.avatar}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <h3 className="font-bold text-foreground font-jakarta group-hover:text-primary transition-colors">{r.name}</h3>
                  <div className={`w-2 h-2 rounded-full ${r.active ? "bg-accent" : "bg-muted-foreground"}`} />
                </div>
                <p className="text-xs text-primary font-semibold mb-0.5">{r.role}</p>
                <p className="text-xs text-muted-foreground">{r.field}</p>
              </div>
              <div className="flex gap-2">
                <button className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center text-muted-foreground hover:bg-primary hover:text-white transition-colors">
                  <ExternalLink size={13} />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-border">
              <div className="text-center">
                <div className="text-xl font-bold text-foreground font-jakarta">{r.h}</div>
                <div className="text-[10px] text-muted-foreground">H-Index</div>
              </div>
              <div className="text-center border-x border-border">
                <div className="text-xl font-bold text-foreground font-jakarta">{r.pubs}</div>
                <div className="text-[10px] text-muted-foreground">Publications</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold text-foreground font-jakarta">{r.citations.toLocaleString()}</div>
                <div className="text-[10px] text-muted-foreground">Citations</div>
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button className="flex-1 py-1.5 bg-primary/8 text-primary text-xs font-semibold rounded-xl hover:bg-primary hover:text-white transition-colors">View Profile</button>
              <button className="flex-1 py-1.5 bg-muted text-muted-foreground text-xs font-semibold rounded-xl hover:bg-secondary transition-colors">Download CV</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── AI AGENTS PAGE ──────────────────────────────────────────────────────────
function AgentsPage() {
  const [selected, setSelected] = useState<number | null>(null);
  const statusConfig: Record<string, { color: string; dot: string; label: string }> = {
    active: { color: "bg-emerald-100 text-emerald-700", dot: "bg-emerald-500 animate-pulse", label: "Active" },
    running: { color: "bg-blue-100 text-blue-700", dot: "bg-blue-500 animate-pulse", label: "Running" },
    idle: { color: "bg-amber-100 text-amber-700", dot: "bg-amber-500", label: "Idle" },
  };

  return (
    <div className="p-6 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">AI Agents Control Center</h2>
          <p className="text-sm text-muted-foreground">8 specialized agents · 6 active · 45,821 executions today</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-2 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700 font-semibold">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            Orchestrator Online
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl">
            <RefreshCw size={14} /> Sync All
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {agents.map(agent => {
          const sc = statusConfig[agent.status];
          const isSelected = selected === agent.id;
          return (
            <div
              key={agent.id}
              onClick={() => setSelected(isSelected ? null : agent.id)}
              className={`bg-card border rounded-2xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5
                ${isSelected ? "border-primary shadow-lg shadow-primary/10 ring-1 ring-primary/20" : "border-border"}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center`}>
                  <agent.icon size={20} className="text-primary" />
                </div>
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-semibold ${sc.color}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                  {sc.label}
                </div>
              </div>

              <h4 className="text-xs font-bold text-foreground font-jakarta mb-2 leading-snug">{agent.name}</h4>
              <p className="text-[10px] text-muted-foreground leading-snug mb-3 line-clamp-2">{agent.task}</p>

              {/* Confidence bar */}
              <div className="mb-3">
                <div className="flex justify-between text-[10px] mb-1">
                  <span className="text-muted-foreground">Confidence</span>
                  <span className="font-semibold text-foreground">{agent.confidence}%</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${agent.confidence >= 90 ? "bg-accent" : agent.confidence >= 75 ? "bg-amber-400" : "bg-red-400"}`}
                    style={{ width: `${agent.confidence}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>{agent.executions.toLocaleString()} runs</span>
                <span className="text-emerald-600 font-semibold">{agent.perf}% perf</span>
              </div>

              {isSelected && (
                <div className="mt-3 pt-3 border-t border-border">
                  <div className="flex gap-2">
                    <button className="flex-1 py-1.5 bg-primary text-white text-[10px] font-semibold rounded-lg flex items-center justify-center gap-1 hover:bg-primary/90 transition-colors">
                      <Play size={10} /> Run
                    </button>
                    <button className="flex-1 py-1.5 bg-amber-100 text-amber-700 text-[10px] font-semibold rounded-lg flex items-center justify-center gap-1">
                      <Pause size={10} /> Pause
                    </button>
                    <button className="py-1.5 px-2 bg-muted text-muted-foreground text-[10px] rounded-lg hover:bg-secondary">
                      <Activity size={10} />
                    </button>
                  </div>
                  <div className="mt-2 p-2 bg-muted rounded-xl">
                    <p className="text-[9px] text-muted-foreground font-mono leading-relaxed">
                      [2024-09-03 14:32:11] Agent initialized<br />
                      [2024-09-03 14:32:14] Fetching data sources<br />
                      [2024-09-03 14:32:18] Processing batch 847/1200
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── DIGITAL TWINS PAGE ──────────────────────────────────────────────────────
function DigitalTwinsPage() {
  const [scenario, setScenario] = useState("baseline");
  const [timeSlider, setTimeSlider] = useState(50);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: parcels, isLoading: parcelsLoading } = useParcels();
  const effectiveId = selectedId ?? (parcels && parcels.length ? parcels[0].id : null);
  const { data: parcel, isLoading: parcelLoading } = useParcel(effectiveId);
  const { data: forecast } = useParcelForecast(effectiveId);
  const refreshForecast = useRefreshForecast();
  const runSim = useRunTwinSimulation();
  const { data: simRuns } = useSimulationRuns(effectiveId);
  const { data: optRuns } = useOptimisationRuns(effectiveId);

  const simData = Array.from({ length: 12 }, (_, i) => ({
    month: ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i],
    baseline: 85 + Math.sin(i / 2) * 15,
    rcp45: 80 + Math.sin(i / 2) * 18 - i * 0.5,
    rcp85: 72 + Math.sin(i / 2) * 22 - i * 1.2,
  }));

  if (parcelsLoading) {
    return (
      <div className="h-full overflow-y-auto scrollbar-hide p-6">
        <div className="animate-pulse bg-card border border-border rounded-2xl h-40" />
      </div>
    );
  }

  if (!parcels || parcels.length === 0) {
    return (
      <div className="h-full overflow-y-auto scrollbar-hide p-6">
        <div className="bg-card border border-border rounded-2xl p-8 text-center">
          <h2 className="text-xl font-bold text-foreground font-jakarta">Digital Twins</h2>
          <p className="text-sm text-muted-foreground mt-2">
            No parcels configured yet. Create one via the API (POST /api/twin/parcels) to start simulating.
          </p>
        </div>
      </div>
    );
  }

  const sensorRows = parcel ? [
    { label: "Crop Type", value: parcel.crop_type, status: "normal" },
    { label: "Area", value: `${parcel.area_ha} ha`, status: "normal" },
    { label: "Soil Type", value: parcel.soil_type, status: "normal" },
    { label: "Field Capacity", value: `${parcel.field_capacity_mm} mm`, status: "normal" },
    { label: "Wilting Point", value: `${parcel.wilting_point_mm} mm`, status: "normal" },
    { label: "Coordinates", value: `${parcel.latitude.toFixed(3)}, ${parcel.longitude.toFixed(3)}`, status: "normal" },
  ] : [];
  const totalPrecip = forecast?.reduce((n, f) => n + f.precipitation_mm, 0) ?? 0;

  return (
    <div className="h-full overflow-y-auto scrollbar-hide">
      <div className="p-6 pb-4">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
          <div>
            <h2 className="text-xl font-bold text-foreground font-jakarta">
              Digital Twin — {parcel?.name ?? "Loading…"}
            </h2>
            <p className="text-sm text-muted-foreground">
              {parcel
                ? `${parcel.code} · ${parcel.crop_type} · ${forecast?.length ?? 0}-day forecast (${totalPrecip.toFixed(0)} mm precip)`
                : "Real-time digital replica"}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <select
              value={effectiveId ?? ""}
              onChange={e => setSelectedId(Number(e.target.value))}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-muted text-foreground border border-border focus:outline-none focus:ring-2 focus:ring-primary/30"
            >
              {parcels.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <button
              onClick={() => effectiveId && refreshForecast.mutate(effectiveId)}
              disabled={refreshForecast.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-muted text-foreground hover:bg-secondary disabled:opacity-60 transition-colors"
            >
              <RefreshCw size={13} className={refreshForecast.isPending ? "animate-spin" : ""} /> Refresh forecast
            </button>
            {["baseline", "rcp45", "rcp85"].map(s => (
              <button key={s} onClick={() => setScenario(s)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors uppercase
                  ${scenario === s ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-secondary"}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="px-6 pb-6 grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* GIS Map placeholder */}
        <div className="xl:col-span-1 bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground font-jakarta">Spatial View</h3>
            <Map size={16} className="text-muted-foreground" />
          </div>
          <div className="relative h-64 bg-gradient-to-br from-[#0F3D2E] to-[#1a5c3a] overflow-hidden">
            {/* Simulated map grid */}
            <svg viewBox="0 0 300 200" className="w-full h-full opacity-30">
              {Array.from({ length: 8 }, (_, i) => (
                <line key={`h${i}`} x1="0" y1={i * 25} x2="300" y2={i * 25} stroke="#4ADE80" strokeWidth="0.5" />
              ))}
              {Array.from({ length: 12 }, (_, i) => (
                <line key={`v${i}`} x1={i * 25} y1="0" x2={i * 25} y2="200" stroke="#4ADE80" strokeWidth="0.5" />
              ))}
              <ellipse cx="150" cy="100" rx="80" ry="50" fill="rgba(74,222,128,0.15)" stroke="#4ADE80" strokeWidth="1.5" strokeDasharray="5,3" />
              <ellipse cx="150" cy="100" rx="50" ry="30" fill="rgba(74,222,128,0.2)" stroke="#4ADE80" strokeWidth="1" />
              <circle cx="120" cy="90" r="5" fill="#4ADE80" />
              <circle cx="160" cy="110" r="4" fill="#4ADE80" />
              <circle cx="180" cy="85" r="5" fill="#4ADE80" />
              <circle cx="140" cy="120" r="3" fill="#F59E0B" />
            </svg>
            <div className="absolute inset-0 flex items-end p-3">
              <div className="flex gap-3 text-[10px] text-white/80">
                <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-accent/70" />Sensors</div>
                <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-amber-400/70" />Anomaly</div>
                <div className="flex items-center gap-1"><div className="w-3 h-3 border border-accent/70 rounded-sm" />Aquifer</div>
              </div>
            </div>
          </div>
          {/* Sensor readings (live parcel data) */}
          <div className="p-4 space-y-2">
            {parcelLoading && <p className="text-xs text-muted-foreground">Loading parcel…</p>}
            {sensorRows.map(s => (
              <div key={s.label} className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{s.label}</span>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground font-mono">{s.value}</span>
                  <div className={`w-2 h-2 rounded-full ${s.status === "normal" ? "bg-accent" : "bg-amber-400"}`} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 3D Twin Viewer */}
        <div className="xl:col-span-1 bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground font-jakarta">3D Twin Viewer</h3>
            <div className="flex items-center gap-1.5 text-[10px] text-accent font-semibold">
              <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />Live
            </div>
          </div>
          <div className="relative h-64 bg-gradient-to-b from-[#e8f4f8] to-[#c8e6f4] flex items-center justify-center overflow-hidden">
            {/* SVG geological cross-section */}
            <svg viewBox="0 0 280 180" className="w-full h-full">
              {/* Sky */}
              <rect x="0" y="0" width="280" height="60" fill="#E0F2FE" />
              {/* Terrain */}
              <path d="M0,60 Q40,40 80,55 Q120,70 160,48 Q200,30 240,52 Q260,60 280,50 L280,70 Q240,72 200,62 Q160,55 120,80 Q80,88 40,72 L0,75 Z" fill="#8B7355" />
              {/* Soil layer */}
              <path d="M0,75 Q40,72 80,88 Q120,100 160,85 Q200,72 240,82 L280,72 L280,110 L0,110 Z" fill="#A0845A" />
              {/* Rock layer */}
              <rect x="0" y="110" width="280" height="30" fill="#7A7A8A" />
              {/* Aquifer */}
              <path d="M0,130 L280,130 L280,170 L0,170 Z" fill="rgba(74,222,128,0.3)" stroke="#4ADE80" strokeWidth="1" />
              <text x="120" y="155" fill="#0B6E4F" fontSize="10" fontWeight="bold">AQUIFER ZONE</text>
              {/* Water level indicator */}
              <line x1="0" y1="135" x2="280" y2="135" stroke="#2D9C72" strokeWidth="1.5" strokeDasharray="6,3" />
              {/* Bore holes */}
              <rect x="80" y="50" width="4" height="95" fill="#555" />
              <rect x="180" y="44" width="4" height="95" fill="#555" />
              {/* Sensor dots */}
              <circle cx="82" cy="135" r="5" fill="#4ADE80" />
              <circle cx="182" cy="135" r="5" fill="#4ADE80" />
              <circle cx="82" cy="50" r="4" fill="#F59E0B" />
              <circle cx="182" cy="44" r="4" fill="#F59E0B" />
            </svg>
          </div>
          {/* Timeline slider */}
          <div className="p-4">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-muted-foreground">Simulation Timeline</span>
              <span className="font-mono font-semibold text-foreground">2024 → {2024 + Math.round(timeSlider / 5)}</span>
            </div>
            <input
              type="range" min={0} max={100} value={timeSlider}
              onChange={e => setTimeSlider(+e.target.value)}
              className="w-full accent-primary cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
              <span>2024</span><span>2029</span><span>2034</span><span>2044</span>
            </div>
          </div>
        </div>

        {/* Simulation Controls & Charts */}
        <div className="xl:col-span-1 space-y-4">
          {/* Scenario chart */}
          <div className="bg-card border border-border rounded-2xl p-4">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-1">Scenario Comparison</h3>
            <p className="text-[10px] text-muted-foreground mb-3">Groundwater level (m) — 2024–2044 projection</p>
            <ResponsiveContainer width="100%" height={160}>
              <ReLineChart data={simData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="month" tick={{ fontSize: 9 }} stroke="none" />
                <YAxis tick={{ fontSize: 9 }} stroke="none" domain={[50, 110]} />
                <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                <Line dataKey="baseline" name="Baseline" stroke="#0B6E4F" strokeWidth={2} dot={false} />
                <Line dataKey="rcp45" name="RCP 4.5" stroke="#F59E0B" strokeWidth={2} dot={false} strokeDasharray="4,2" />
                <Line dataKey="rcp85" name="RCP 8.5" stroke="#EF4444" strokeWidth={2} dot={false} strokeDasharray="2,2" />
              </ReLineChart>
            </ResponsiveContainer>
          </div>

          {/* Controls */}
          <div className="bg-card border border-border rounded-2xl p-4">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-3">Simulation Controls</h3>
            <div className="space-y-3">
              {[
                { label: "Recharge Rate", value: 2.8, unit: "mm/day", min: 0, max: 10 },
                { label: "Extraction", value: 4.2, unit: "Mm³/yr", min: 0, max: 15 },
                { label: "Permeability", value: 6, unit: "m/day", min: 0, max: 20 },
              ].map(c => (
                <div key={c.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{c.label}</span>
                    <span className="font-mono font-semibold text-foreground">{c.value} {c.unit}</span>
                  </div>
                  <input type="range" min={c.min} max={c.max} defaultValue={c.value} className="w-full accent-primary" />
                </div>
              ))}
              <button
                onClick={() => effectiveId && runSim.mutate(effectiveId)}
                disabled={runSim.isPending}
                className="w-full py-2 bg-gradient-to-r from-primary to-[#2D9C72] text-white text-xs font-bold rounded-xl hover:shadow-lg hover:shadow-primary/20 transition-all mt-2 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                <Play size={13} /> {runSim.isPending ? "Running…" : "Run Simulation"}
              </button>
              {runSim.isError && <p className="text-[10px] text-red-600 mt-1">{(runSim.error as Error).message}</p>}
            </div>
          </div>

          {/* Recent runs */}
          <div className="bg-card border border-border rounded-2xl p-4">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-3">Recent Runs</h3>
            <div className="space-y-3 text-xs">
              <div>
                <p className="font-semibold text-foreground mb-1">Simulation</p>
                {simRuns && simRuns.length > 0 ? (
                  <ul className="space-y-1">
                    {simRuns.slice(0, 3).map(r => (
                      <li key={r.id} className="flex justify-between text-muted-foreground">
                        <span className="truncate pr-2">{r.scenario_name}</span>
                        <span className="font-mono">{new Date(r.created_at).toLocaleDateString()}</span>
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-muted-foreground">No runs yet.</p>}
              </div>
              <div>
                <p className="font-semibold text-foreground mb-1">Optimisation</p>
                {optRuns && optRuns.length > 0 ? (
                  <ul className="space-y-1">
                    {optRuns.slice(0, 3).map(r => (
                      <li key={r.id} className="flex justify-between text-muted-foreground">
                        <span className="truncate pr-2">{r.run_name}</span>
                        <span className="font-mono">{new Date(r.created_at).toLocaleDateString()}</span>
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-muted-foreground">No runs yet.</p>}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── IOT PAGE ────────────────────────────────────────────────────────────────
function IoTPage() {
  const metrics = [
    { label: "Avg Temperature", value: "24.3°C", change: "+1.2°C", icon: Thermometer, color: "text-orange-500", bg: "bg-orange-50" },
    { label: "Avg Humidity", value: "61.4%", change: "+3.1%", icon: Droplets, color: "text-blue-500", bg: "bg-blue-50" },
    { label: "Avg Pressure", value: "1013 hPa", change: "-0.3 hPa", icon: Gauge, color: "text-purple-500", bg: "bg-purple-50" },
    { label: "Water Flow", value: "2.7 m³/s", change: "+0.4 m³/s", icon: Wind, color: "text-cyan-500", bg: "bg-cyan-50" },
    { label: "Sensors Online", value: "1,241/1,247", change: "99.5%", icon: Radio, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Alerts Active", value: "3", change: "!medium", icon: AlertCircle, color: "text-red-500", bg: "bg-red-50" },
  ];

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">IoT Monitoring Dashboard</h2>
          <p className="text-sm text-muted-foreground">1,247 sensors across 23 stations · Real-time streaming</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-emerald-700 font-semibold bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-xl">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          Live Stream Active
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {metrics.map(m => (
          <div key={m.label} className={`${m.bg} border border-border rounded-2xl p-4`}>
            <m.icon size={20} className={`${m.color} mb-2`} />
            <div className="text-xl font-bold text-foreground font-jakarta">{m.value}</div>
            <div className="text-[10px] text-muted-foreground mt-0.5">{m.label}</div>
            <div className="text-[10px] font-semibold mt-1 text-muted-foreground">{m.change}</div>
          </div>
        ))}
      </div>

      {/* Time series charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Temperature & Humidity (24h)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={iotData.slice(0, 24)}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="h" tick={{ fontSize: 9 }} stroke="none" interval={3} />
              <YAxis tick={{ fontSize: 9 }} stroke="none" />
              <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              <Area type="monotone" dataKey="temp" name="Temp (°C)" stroke="#F97316" fill="rgba(249,115,22,0.1)" strokeWidth={2} />
              <Area type="monotone" dataKey="humidity" name="Humidity (%)" stroke="#3B82F6" fill="rgba(59,130,246,0.08)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Water Flow Rate (24h)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={iotData.slice(0, 24)}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="h" tick={{ fontSize: 9 }} stroke="none" interval={3} />
              <YAxis tick={{ fontSize: 9 }} stroke="none" />
              <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
              <Bar dataKey="flow" name="Flow (m³/s)" fill="#0B6E4F" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <h3 className="font-bold text-foreground font-jakarta mb-4">Active Alerts</h3>
        <div className="space-y-3">
          {[
            { id: "SN-142", type: "Temperature Spike", msg: "Temperature exceeded threshold by 4.2°C at Station Marrakech-Nord", severity: "high", time: "28m ago" },
            { id: "SN-089", type: "Data Gap", msg: "No reading received for 47 minutes — possible connectivity issue", severity: "medium", time: "1h ago" },
            { id: "SN-231", type: "Battery Low", msg: "Battery at 8% — scheduled replacement needed within 48h", severity: "low", time: "3h ago" },
          ].map(a => (
            <div key={a.id} className={`flex items-start gap-3 p-3 rounded-xl border
              ${a.severity === "high" ? "bg-red-50 border-red-200" : a.severity === "medium" ? "bg-amber-50 border-amber-200" : "bg-blue-50 border-blue-200"}`}>
              <AlertCircle size={16} className={a.severity === "high" ? "text-red-500 mt-0.5" : a.severity === "medium" ? "text-amber-500 mt-0.5" : "text-blue-500 mt-0.5"} />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-bold text-foreground">{a.type}</span>
                  <span className="text-[10px] text-muted-foreground">Sensor {a.id}</span>
                  <span className="text-[10px] text-muted-foreground ml-auto">{a.time}</span>
                </div>
                <p className="text-xs text-muted-foreground">{a.msg}</p>
              </div>
              <button className="text-[10px] font-semibold text-primary bg-white border border-border px-2 py-1 rounded-lg hover:bg-primary hover:text-white transition-colors shrink-0">
                Resolve
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── SCIENTIFIC WATCH PAGE ───────────────────────────────────────────────────
function WatchPage() {
  const { data: articles, isLoading, error, refetch } = useArticles();
  const trigger = useTriggerScrape();

  const formatDate = (iso?: string | null) =>
    iso ? new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—";
  const hostOf = (url?: string | null) => {
    if (!url) return "Source";
    try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return "Source"; }
  };
  const relevanceOf = (a: Article) => {
    const c = a.tags[0]?.confidence;
    return typeof c === "number" ? Math.round(c * 100) : a.tags.length * 20 + 40;
  };
  const summaryOf = (a: Article) => a.summaries[0]?.summary_text || a.abstract || "No summary available yet.";

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Scientific Watch</h2>
          <p className="text-sm text-muted-foreground">
            {articles ? `${articles.length} article${articles.length === 1 ? "" : "s"} · AI-curated scientific watch` : "AI-curated scientific watch"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => trigger.mutate()}
            disabled={trigger.isPending}
            className="flex items-center gap-1.5 text-xs font-semibold bg-primary text-white px-3 py-1.5 rounded-xl hover:bg-primary/90 disabled:opacity-60 transition-colors"
          >
            <RefreshCw size={13} className={trigger.isPending ? "animate-spin" : ""} />
            {trigger.isPending ? "Collecting…" : "Trigger scrape"}
          </button>
          <div className="flex items-center gap-2 text-xs text-primary font-semibold bg-primary/8 px-3 py-1.5 rounded-xl">
            <Eye size={14} /> Live feed
          </div>
        </div>
      </div>

      {/* Trending topics */}
      <div className="bg-gradient-to-br from-[#0F3D2E] to-[#0B6E4F] rounded-2xl p-5 text-white">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-3">AI-Detected Trending Topics — This Week</p>
        <div className="flex flex-wrap gap-2">
          {["Foundation Models for Climate", "Digital Twin Calibration", "GRACE-FO Groundwater", "Transformer-based Hydrology", "Federated IoT Learning", "Scenario-Based Risk", "LLM for Scientific Literature"].map(t => (
            <span key={t} className="px-3 py-1.5 bg-white/10 border border-white/15 rounded-full text-xs font-medium backdrop-blur-sm hover:bg-white/20 cursor-pointer transition-colors">
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Articles */}
      <div className="space-y-4">
        {isLoading && (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-card border border-border rounded-2xl p-5 animate-pulse">
              <div className="h-3 w-24 bg-muted rounded-full mb-3" />
              <div className="h-4 w-3/4 bg-muted rounded mb-2" />
              <div className="h-3 w-full bg-muted rounded" />
            </div>
          ))
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-5 text-sm text-red-700">
            <p className="font-semibold">Could not load the watch feed.</p>
            <p className="text-xs mt-1">{(error as Error).message}</p>
            <button onClick={() => refetch()} className="mt-3 text-xs font-semibold underline">Retry</button>
          </div>
        )}

        {!isLoading && !error && articles && articles.length === 0 && (
          <div className="bg-card border border-border rounded-2xl p-8 text-center">
            <p className="text-sm font-semibold text-foreground">No articles collected yet</p>
            <p className="text-xs text-muted-foreground mt-1 mb-4">Trigger a scrape to populate the scientific watch feed.</p>
            <button onClick={() => trigger.mutate()} disabled={trigger.isPending}
              className="inline-flex items-center gap-1.5 text-xs font-semibold bg-primary text-white px-4 py-2 rounded-xl hover:bg-primary/90 disabled:opacity-60">
              <RefreshCw size={13} className={trigger.isPending ? "animate-spin" : ""} /> Trigger scrape
            </button>
          </div>
        )}

        {!isLoading && !error && articles?.map(a => {
          const relevance = relevanceOf(a);
          return (
            <div key={a.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md hover:border-primary/20 transition-all group">
              <div className="flex items-start gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <span className="text-[10px] font-bold text-primary bg-primary/8 px-2 py-0.5 rounded-full">{hostOf(a.url)}</span>
                    <span className="text-[10px] text-muted-foreground">{formatDate(a.published_at ?? a.collected_at)}</span>
                    {a.tags.map(t => <span key={t.tag} className="text-[10px] bg-muted text-muted-foreground px-2 py-0.5 rounded-full">{t.tag}</span>)}
                  </div>
                  <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors mb-2">{a.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">{summaryOf(a)}</p>
                  {a.authors && a.authors.length > 0 && (
                    <p className="text-[10px] text-muted-foreground mt-2">{a.authors.join(", ")}</p>
                  )}
                </div>
                <div className="shrink-0 text-center">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-lg font-extrabold font-jakarta
                    ${relevance >= 95 ? "bg-emerald-100 text-emerald-700" : relevance >= 88 ? "bg-amber-100 text-amber-700" : "bg-blue-100 text-blue-700"}`}>
                    {relevance}
                  </div>
                  <div className="text-[9px] text-muted-foreground mt-1">Relevance</div>
                </div>
              </div>
              <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border">
                {a.url && (
                  <a href={a.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors">
                    <ExternalLink size={12} /> Full Paper
                  </a>
                )}
                {a.summaries.length > 0 && (
                  <span className="flex items-center gap-1 text-[10px] text-muted-foreground"><Brain size={11} /> AI Summary</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── AI ASSISTANT PANEL ─────────────────────────────────────────────────────
function AIAssistantPanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello! I'm your AI Research Assistant. Ask me to find publications, summarize papers, recommend datasets, or explain scientific concepts." },
  ]);
  const suggestions = [
    "Summarize the latest groundwater research",
    "Find researchers working on Digital Twins",
    "What datasets are available for climate modeling?",
    "Recommend papers on AI in hydrology",
  ];
  const send = () => {
    if (!input.trim()) return;
    const q = input;
    setMessages(m => [...m, { role: "user", text: q }, { role: "ai", text: `Searching across 312 publications, 84 researchers, and 156 datasets for: "${q}"… Here are the top results relevant to your query. I found 8 highly-cited papers, 3 active projects, and 2 researchers specializing in this domain.` }]);
    setInput("");
  };
  if (!open) return null;
  return (
    <div className="fixed bottom-24 right-6 w-80 bg-card border border-border rounded-2xl shadow-2xl shadow-primary/10 z-50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-300" style={{ maxHeight: "480px" }}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-primary to-[#2D9C72]">
        <div className="flex items-center gap-2 text-white">
          <Brain size={16} />
          <span className="text-sm font-bold">AI Research Assistant</span>
          <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
        </div>
        <button onClick={onClose} className="text-white/70 hover:text-white transition-colors"><X size={16} /></button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-hide" style={{ minHeight: 0, maxHeight: "300px" }}>
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            {m.role === "ai" && (
              <div className="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center mr-2 shrink-0 mt-0.5">
                <Brain size={12} className="text-primary" />
              </div>
            )}
            <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed
              ${m.role === "user" ? "bg-primary text-white rounded-br-sm" : "bg-muted text-foreground rounded-bl-sm"}`}>
              {m.text}
            </div>
          </div>
        ))}
      </div>
      {messages.length === 1 && (
        <div className="px-4 pb-2 space-y-1.5">
          {suggestions.map(s => (
            <button key={s} onClick={() => { setInput(s); }} className="w-full text-left text-[10px] text-muted-foreground bg-muted hover:bg-secondary hover:text-foreground px-3 py-1.5 rounded-lg transition-colors">
              {s}
            </button>
          ))}
        </div>
      )}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-2 bg-muted rounded-xl px-3 py-2">
          <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Ask anything..." className="flex-1 bg-transparent text-xs text-foreground placeholder:text-muted-foreground focus:outline-none" />
          <button onClick={send} className="w-6 h-6 bg-primary rounded-lg flex items-center justify-center hover:bg-primary/90 transition-colors">
            <Send size={11} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── VISITOR PORTAL PAGE ─────────────────────────────────────────────────────
function VisitorPortalPage({ onAdminLogin }: { onAdminLogin?: () => void } = {}) {
  const { signIn, signUp } = useAuth();
  const [authModal, setAuthModal] = useState<"login" | "signup" | null>(null);
  const [loggedIn, setLoggedIn] = useState(false);
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState<string | null>(null);
  const [authBusy, setAuthBusy] = useState(false);
  const [feedFilter, setFeedFilter] = useState("latest");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [selectedResearcher, setSelectedResearcher] = useState<number | null>(null);
  const [carouselIdx, setCarouselIdx] = useState(0);
  const [likedPosts, setLikedPosts] = useState<Set<number>>(new Set());
  const [savedPosts, setSavedPosts] = useState<Set<number>>(new Set());

  const searchSuggestions = [
    "Find irrigation optimization research",
    "Water resource management AI models",
    "Digital Twin aquifer simulation",
    "Researchers working on climate change",
    "EPANET hydraulic network publications",
    "Machine learning for flood prediction",
  ];
  const trending = ["Foundation Models for Climate", "GRACE-FO Groundwater", "Federated IoT Learning", "LLMs in Hydrogeology", "Smart Irrigation AI", "Remote Sensing Fusion"];

  const feedItems = [
    { id: 1, title: "How AI is Revolutionizing Groundwater Management in North Africa", summary: "A new deep learning framework trained on 30 years of piezometric data achieves 94% accuracy in predicting seasonal aquifer recharge, outperforming classical MODFLOW models by 38%.", author: "Dr. Karim El-Amine", date: "Sep 3, 2024", readTime: "8 min", tags: ["AI", "Groundwater"], likes: 247, views: 3420, img: "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=600&h=300&fit=crop&auto=format", type: "article" },
    { id: 2, title: "Digital Twins for Climate Adaptation: From Theory to Practice", summary: "Three operational case studies — Tensift watershed, Souss Massa plain, and Moulouya basin — demonstrate how real-time digital twins reduce water stress management response time by 67%.", author: "Dr. Aicha Bouziane", date: "Sep 1, 2024", readTime: "12 min", tags: ["Digital Twins", "Climate"], likes: 189, views: 2891, img: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=600&h=300&fit=crop&auto=format", type: "research" },
    { id: 3, title: "1,247 Sensors, 23 Stations: Inside Our National IoT Environmental Grid", summary: "A behind-the-scenes look at the architecture, challenges, and lessons learned from deploying Morocco's largest environmental IoT network over 18 months.", author: "Dr. Leila Mansouri", date: "Aug 30, 2024", readTime: "6 min", tags: ["IoT", "Infrastructure"], likes: 134, views: 1987, img: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=300&fit=crop&auto=format", type: "insight" },
    { id: 4, title: "Open Data Release: Tensift Basin Hydro-Meteorological Dataset 2000–2024", summary: "We are releasing 24 years of daily hydro-meteorological observations from 47 stations in the Tensift Basin, freely available under CC-BY 4.0 with full API access.", author: "Research Data Team", date: "Aug 28, 2024", readTime: "3 min", tags: ["Open Data", "Hydrology"], likes: 312, views: 5640, img: "https://images.unsplash.com/photo-1611273426858-450d8e3c9fce?w=600&h=300&fit=crop&auto=format", type: "dataset" },
  ];

  const featuredProjects = [
    { id: 1, title: "AquaPredict", desc: "AI-powered groundwater level forecasting for 12 Moroccan aquifers using transformer models and satellite data fusion.", funder: "OCP Foundation", progress: 68, team: 8, img: "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=400&h=220&fit=crop&auto=format" },
    { id: 2, title: "ClimateShield DT", desc: "High-fidelity digital twin for climate adaptation planning integrating CMIP6 downscaling with socioeconomic vulnerability indices.", funder: "World Bank", progress: 41, team: 12, img: "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=400&h=220&fit=crop&auto=format" },
    { id: 3, title: "SensorNet Morocco", desc: "National-scale IoT environmental monitoring grid covering 23 hydrological stations with edge AI anomaly detection.", funder: "Ministry of Water", progress: 85, team: 6, img: "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=220&fit=crop&auto=format" },
    { id: 4, title: "SOILS-AI", desc: "Pedological intelligence system mapping soil carbon stocks and texture across Morocco using hyperspectral remote sensing.", funder: "FAO / IFAD", progress: 12, team: 4, img: "https://images.unsplash.com/photo-1464226184884-fa280b87c399?w=400&h=220&fit=crop&auto=format" },
  ];

  const categories = [
    { label: "Agriculture", icon: Sprout, color: "from-emerald-100 to-green-50 border-emerald-200", iconColor: "text-emerald-700", count: 78 },
    { label: "Water Resources", icon: Waves, color: "from-blue-100 to-cyan-50 border-blue-200", iconColor: "text-blue-600", count: 94 },
    { label: "Climate Change", icon: ThermometerSun, color: "from-orange-100 to-amber-50 border-orange-200", iconColor: "text-orange-600", count: 67 },
    { label: "Artificial Intelligence", icon: BrainCircuit, color: "from-violet-100 to-purple-50 border-violet-200", iconColor: "text-violet-600", count: 112 },
    { label: "Remote Sensing", icon: SatelliteDish, color: "from-indigo-100 to-blue-50 border-indigo-200", iconColor: "text-indigo-600", count: 45 },
    { label: "Data Science", icon: BarChart2, color: "from-teal-100 to-emerald-50 border-teal-200", iconColor: "text-teal-600", count: 83 },
    { label: "Machine Learning", icon: Brain, color: "from-pink-100 to-rose-50 border-pink-200", iconColor: "text-pink-600", count: 91 },
    { label: "IoT & Sensors", icon: Wifi, color: "from-cyan-100 to-sky-50 border-cyan-200", iconColor: "text-cyan-600", count: 38 },
    { label: "GIS & Spatial", icon: Map, color: "from-amber-100 to-yellow-50 border-amber-200", iconColor: "text-amber-700", count: 56 },
    { label: "Irrigation", icon: Droplet, color: "from-sky-100 to-blue-50 border-sky-200", iconColor: "text-sky-600", count: 29 },
    { label: "Watersheds", icon: Leaf, color: "from-green-100 to-lime-50 border-green-200", iconColor: "text-green-700", count: 41 },
    { label: "Hydraulic Eng.", icon: Gauge, color: "from-slate-100 to-gray-50 border-slate-200", iconColor: "text-slate-600", count: 33 },
  ];

  const conferences = [
    { name: "International Hydrology Conference 2024", location: "Marrakech, Morocco", date: "Oct 14–17, 2024", days: 41, speakers: 48, registered: 620, deadline: "Sep 30" },
    { name: "AI for Environmental Science Summit", location: "Paris, France", date: "Nov 5–7, 2024", days: 63, speakers: 32, registered: 890, deadline: "Oct 20" },
    { name: "Digital Twins in Water Management", location: "Dubai, UAE", date: "Dec 3–5, 2024", days: 91, speakers: 24, registered: 340, deadline: "Nov 15" },
  ];

  const datasets = [
    { name: "Tensift Basin Hydro-Met 2000–2024", format: "CSV / NetCDF", size: "4.2 GB", downloads: 1847, license: "CC-BY 4.0", tags: ["Hydrology", "Climate"] },
    { name: "Morocco DEM 10m Resolution", format: "GeoTIFF", size: "8.7 GB", downloads: 3201, license: "CC-BY 4.0", tags: ["GIS", "Terrain"] },
    { name: "NDVI Time Series 2015–2024", format: "NetCDF", size: "12.1 GB", downloads: 923, license: "CC-0", tags: ["Remote Sensing", "Agriculture"] },
  ];

  const researcherProfiles = researchers.map(r => ({
    ...r,
    institution: "LabAI Research Institute",
    country: "Morocco",
    skills: ["Python", "MODFLOW", "GIS", "Machine Learning", "R"],
    interests: r.field.split(" & "),
    following: false,
  }));

  const selectedR = researcherProfiles.find(r => r.id === selectedResearcher);

  const typeLabels: Record<string, { label: string; color: string }> = {
    article: { label: "Article", color: "bg-emerald-100 text-emerald-700" },
    research: { label: "Research", color: "bg-blue-100 text-blue-700" },
    insight: { label: "Insight", color: "bg-amber-100 text-amber-700" },
    dataset: { label: "Dataset", color: "bg-purple-100 text-purple-700" },
  };

  return (
    <div className="h-full overflow-y-auto scrollbar-hide bg-background">

      {/* ── Public Top Bar ── */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center">
              <FlaskConical size={14} className="text-white" />
            </div>
            <span className="font-extrabold text-sm text-foreground font-jakarta">LabAI</span>
            <span className="text-[10px] font-semibold px-2 py-0.5 bg-primary/10 text-primary rounded-full">Public Portal</span>
          </div>
          <nav className="hidden md:flex items-center gap-1 ml-4">
            {["Research", "Publications", "Researchers", "Datasets", "Events"].map(n => (
              <button key={n} className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors">{n}</button>
            ))}
          </nav>
          <div className="flex-1" />
          {loggedIn ? (
            <div className="flex items-center gap-2">
              <button className="p-2 rounded-xl hover:bg-muted text-muted-foreground"><Bell size={16} /></button>
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white text-xs font-bold">AH</div>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <button onClick={() => onAdminLogin ? onAdminLogin() : setAuthModal("login")} className="px-4 py-1.5 text-xs font-semibold text-foreground hover:bg-muted rounded-xl transition-colors">Log In</button>
              <button onClick={() => setAuthModal("signup")} className="px-4 py-1.5 text-xs font-bold bg-primary text-white rounded-xl hover:bg-primary/90 transition-colors">Sign Up Free</button>
            </div>
          )}
        </div>
      </header>

      {/* ── Auth Modal ── */}
      {authModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setAuthModal(null)}>
          <div className="bg-card rounded-3xl p-8 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="text-center mb-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center mx-auto mb-3">
                <FlaskConical size={22} className="text-white" />
              </div>
              <h2 className="text-xl font-extrabold text-foreground font-jakarta">{authModal === "login" ? "Welcome back" : "Join LabAI Portal"}</h2>
              <p className="text-xs text-muted-foreground mt-1">{authModal === "login" ? "Sign in to your research account" : "Access world-class research for free"}</p>
            </div>
            <div className="space-y-3">
              {authModal === "signup" && (
                <div>
                  <label className="text-xs font-semibold text-foreground mb-1 block">Full Name</label>
                  <input placeholder="Dr. Ahmed Hassan" className="w-full px-3 py-2.5 text-sm bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30" />
                </div>
              )}
              <div>
                <label className="text-xs font-semibold text-foreground mb-1 block">Email</label>
                <input value={authEmail} onChange={e => setAuthEmail(e.target.value)} placeholder="researcher@institution.edu" className="w-full px-3 py-2.5 text-sm bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30" />
              </div>
              <div>
                <label className="text-xs font-semibold text-foreground mb-1 block">Password</label>
                <input type="password" value={authPassword} onChange={e => setAuthPassword(e.target.value)} placeholder="••••••••" className="w-full px-3 py-2.5 text-sm bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30" />
              </div>
              {authError && (
                <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-xl px-3 py-2">{authError}</p>
              )}
              <button onClick={async () => {
                  setAuthError(null);
                  setAuthBusy(true);
                  try {
                    if (authModal === "signup") {
                      await signUp(authEmail, authPassword);
                      setLoggedIn(true);
                      setAuthModal(null);
                      return;
                    }
                    await signIn(authEmail, authPassword);
                    if (onAdminLogin) { onAdminLogin(); } else { setLoggedIn(true); setAuthModal(null); }
                  } catch (e) {
                    setAuthError(e instanceof Error ? e.message : "Authentication failed");
                  } finally {
                    setAuthBusy(false);
                  }
                }}
                disabled={authBusy}
                className="w-full py-3 bg-gradient-to-r from-primary to-[#2D9C72] text-white font-bold rounded-xl hover:shadow-lg hover:shadow-primary/20 transition-all text-sm disabled:opacity-60">
                {authBusy ? "Please wait…" : authModal === "login" ? "Sign In" : "Create Account"}
              </button>
              <div className="relative my-3">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-border" /></div>
                <div className="relative flex justify-center"><span className="bg-card px-3 text-xs text-muted-foreground">or continue with</span></div>
              </div>
              <button className="w-full py-2.5 border border-border rounded-xl text-sm font-medium text-foreground hover:bg-muted transition-colors flex items-center justify-center gap-2">
                <Globe size={15} /> Google / ORCID
              </button>
            </div>
            <p className="text-center text-xs text-muted-foreground mt-4">
              {authModal === "login" ? "No account? " : "Already have one? "}
              <button className="text-primary font-semibold" onClick={() => setAuthModal(authModal === "login" ? "signup" : "login")}>
                {authModal === "login" ? "Sign Up Free" : "Log In"}
              </button>
            </p>
          </div>
        </div>
      )}

      {/* ── Researcher Profile Modal ── */}
      {selectedR && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 flex items-center justify-center p-4" onClick={() => setSelectedResearcher(null)}>
          <div className="bg-card rounded-3xl w-full max-w-2xl max-h-[88vh] overflow-y-auto scrollbar-hide shadow-2xl" onClick={e => e.stopPropagation()}>
            {/* Header banner */}
            <div className="h-32 bg-gradient-to-br from-[#0F3D2E] via-[#0B6E4F] to-[#1a7a5a] relative rounded-t-3xl">
              <ParticleCanvas />
              <button onClick={() => setSelectedResearcher(null)} className="absolute top-3 right-3 w-7 h-7 bg-white/20 rounded-full flex items-center justify-center text-white hover:bg-white/30 transition-colors">
                <X size={14} />
              </button>
            </div>
            <div className="px-6 pb-6">
              <div className="flex items-end gap-4 -mt-8 mb-4">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white text-2xl font-extrabold shadow-xl border-4 border-card shrink-0">
                  {selectedR.avatar}
                </div>
                <div className="pb-1 flex-1 min-w-0">
                  <h2 className="text-xl font-extrabold text-foreground font-jakarta truncate">{selectedR.name}</h2>
                  <p className="text-sm text-primary font-semibold">{selectedR.role}</p>
                  <p className="text-xs text-muted-foreground">{selectedR.institution} · {selectedR.country}</p>
                </div>
                <div className="flex gap-2 pb-1">
                  <button className="px-4 py-2 bg-primary text-white text-xs font-bold rounded-xl hover:bg-primary/90 transition-colors flex items-center gap-1.5"><UserPlus size={13} /> Follow</button>
                  <button className="px-4 py-2 bg-muted text-foreground text-xs font-semibold rounded-xl hover:bg-secondary transition-colors flex items-center gap-1.5"><Mail size={13} /> Contact</button>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 mb-5">
                {[
                  { label: "H-Index", value: selectedR.h },
                  { label: "Publications", value: selectedR.pubs },
                  { label: "Citations", value: selectedR.citations.toLocaleString() },
                ].map(s => (
                  <div key={s.label} className="bg-muted rounded-2xl p-3 text-center">
                    <div className="text-2xl font-extrabold text-foreground font-jakarta">{s.value}</div>
                    <div className="text-[10px] text-muted-foreground">{s.label}</div>
                  </div>
                ))}
              </div>

              {/* Research Interests */}
              <div className="mb-4">
                <h3 className="text-xs font-bold text-foreground mb-2">Research Interests</h3>
                <div className="flex flex-wrap gap-1.5">
                  {selectedR.interests.map(i => <span key={i} className="px-2.5 py-1 bg-primary/8 text-primary text-xs rounded-full font-medium">{i}</span>)}
                  <span className="px-2.5 py-1 bg-muted text-muted-foreground text-xs rounded-full">AI & Deep Learning</span>
                  <span className="px-2.5 py-1 bg-muted text-muted-foreground text-xs rounded-full">Remote Sensing</span>
                </div>
              </div>

              {/* Skills */}
              <div className="mb-4">
                <h3 className="text-xs font-bold text-foreground mb-2">Technical Skills</h3>
                <div className="flex flex-wrap gap-1.5">
                  {selectedR.skills.map(s => <span key={s} className="px-2.5 py-1 bg-muted border border-border text-foreground text-xs rounded-full font-mono">{s}</span>)}
                </div>
              </div>

              {/* Citation trend */}
              <div className="mb-4">
                <h3 className="text-xs font-bold text-foreground mb-2">Citation Trend</h3>
                <div className="bg-muted rounded-2xl p-3 h-24">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={[180,220,310,420,580,720,890,1100,1480,selectedR.citations].map((v, i) => ({ y: v, x: 2015 + i }))}>
                      <Area type="monotone" dataKey="y" stroke="#0B6E4F" fill="rgba(11,110,79,0.1)" strokeWidth={2} dot={false} />
                      <XAxis dataKey="x" tick={{ fontSize: 9 }} stroke="none" />
                      <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Social links */}
              <div className="flex gap-2">
                <button className="flex-1 py-2 bg-muted text-xs font-semibold text-muted-foreground rounded-xl hover:bg-secondary flex items-center justify-center gap-1.5 transition-colors"><Globe size={12} /> ORCID</button>
                <button className="flex-1 py-2 bg-muted text-xs font-semibold text-muted-foreground rounded-xl hover:bg-secondary flex items-center justify-center gap-1.5 transition-colors"><BookOpen size={12} /> Scholar</button>
                <button className="flex-1 py-2 bg-muted text-xs font-semibold text-muted-foreground rounded-xl hover:bg-secondary flex items-center justify-center gap-1.5 transition-colors"><Download size={12} /> Download CV</button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6">

        {/* ── Welcome Hero ── */}
        <section className="relative py-14 text-center overflow-hidden">
          {/* Decorative blobs */}
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-8 right-1/4 w-72 h-72 bg-accent/8 rounded-full blur-3xl pointer-events-none" />
          {loggedIn ? (
            <>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/8 border border-primary/20 rounded-full text-xs text-primary font-semibold mb-4">
                <div className="w-2 h-2 bg-accent rounded-full animate-pulse" /> Personalized for you
              </div>
              <h1 className="text-4xl font-extrabold text-foreground font-jakarta mb-2">Welcome back, Ahmed 👋</h1>
              <p className="text-muted-foreground text-lg">Discover the latest research, publications and innovations.</p>
            </>
          ) : (
            <>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/8 border border-primary/20 rounded-full text-xs text-primary font-semibold mb-4">
                <Sparkles size={12} /> AI-Powered Scientific Discovery
              </div>
              <h1 className="text-5xl font-extrabold text-foreground font-jakarta mb-3 leading-tight">
                Explore World-Class<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-[#2D9C72]">Environmental Research</span>
              </h1>
              <p className="text-muted-foreground text-lg mb-6 max-w-xl mx-auto">Access 312+ publications, connect with 84 researchers, and explore AI-powered scientific insights.</p>
              <div className="flex items-center justify-center gap-3">
                <button onClick={() => setAuthModal("signup")} className="px-6 py-3 bg-primary text-white font-bold rounded-xl hover:shadow-lg hover:shadow-primary/20 transition-all text-sm">Get Started Free</button>
                <button className="px-6 py-3 bg-white border border-border text-foreground font-semibold rounded-xl hover:bg-muted transition-colors text-sm">Browse as Guest</button>
              </div>
            </>
          )}

          {/* AI Search Bar */}
          <div className="relative max-w-2xl mx-auto mt-8">
            <div className={`bg-white border-2 rounded-2xl shadow-lg transition-all duration-200 ${searchFocused ? "border-primary shadow-xl shadow-primary/10" : "border-border"}`}>
              <div className="flex items-center gap-3 px-5 py-4">
                <Search size={20} className={`shrink-0 transition-colors ${searchFocused ? "text-primary" : "text-muted-foreground"}`} />
                <input
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  onFocus={() => setSearchFocused(true)}
                  onBlur={() => setTimeout(() => setSearchFocused(false), 150)}
                  placeholder="Search publications, researchers, datasets or ask an AI question..."
                  className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none"
                />
                <button className="p-2 rounded-xl hover:bg-muted text-muted-foreground transition-colors"><Mic size={18} /></button>
                <button className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-[#2D9C72] text-white text-xs font-bold rounded-xl hover:shadow-md transition-all">
                  <Brain size={14} /> AI Search
                </button>
              </div>
              {searchFocused && (
                <div className="border-t border-border px-5 py-3 space-y-4">
                  <div>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Suggested Searches</p>
                    <div className="flex flex-wrap gap-1.5">
                      {searchSuggestions.map(s => (
                        <button key={s} onClick={() => setSearchQuery(s)} className="px-2.5 py-1 bg-muted hover:bg-primary hover:text-white text-xs text-muted-foreground rounded-full transition-colors">{s}</button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">🔥 Trending Now</p>
                    <div className="flex flex-wrap gap-1.5">
                      {trending.slice(0, 4).map(t => (
                        <button key={t} onClick={() => setSearchQuery(t)} className="px-2.5 py-1 bg-accent/15 text-emerald-700 text-xs rounded-full font-medium hover:bg-accent/30 transition-colors">{t}</button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ── Scientific Categories ── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-foreground font-jakarta">Scientific Domains</h2>
            <button className="text-xs text-primary font-semibold">View all →</button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6 gap-3">
            {categories.map(c => (
              <button key={c.label} className={`bg-gradient-to-br ${c.color} border rounded-2xl p-4 text-left hover:shadow-md hover:-translate-y-0.5 transition-all group`}>
                <c.icon size={22} className={`${c.iconColor} mb-2`} />
                <p className="text-xs font-bold text-foreground leading-tight mb-1">{c.label}</p>
                <p className="text-[10px] text-muted-foreground">{c.count} publications</p>
              </button>
            ))}
          </div>
        </section>

        {/* ── Featured Research Carousel ── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-foreground font-jakarta">Featured Research Projects</h2>
            <div className="flex items-center gap-2">
              <button onClick={() => setCarouselIdx(i => Math.max(0, i - 1))} className="w-8 h-8 rounded-xl border border-border hover:bg-muted flex items-center justify-center text-muted-foreground transition-colors"><ChevronLeft size={16} /></button>
              <button onClick={() => setCarouselIdx(i => Math.min(featuredProjects.length - 1, i + 1))} className="w-8 h-8 rounded-xl border border-border hover:bg-muted flex items-center justify-center text-muted-foreground transition-colors"><ChevronRight size={16} /></button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {featuredProjects.map((p, i) => (
              <div key={p.id} className={`bg-card border border-border rounded-2xl overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all group ${i < carouselIdx ? "opacity-40" : "opacity-100"}`}>
                <div className="relative h-36 bg-gray-100 overflow-hidden">
                  <img src={p.img} alt={p.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <div className="absolute bottom-2 left-3">
                    <span className="text-[10px] font-semibold text-white/90 bg-white/20 backdrop-blur-sm px-2 py-0.5 rounded-full">{p.funder}</span>
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="font-bold text-foreground font-jakarta text-sm mb-1.5 group-hover:text-primary transition-colors">{p.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-3 line-clamp-2">{p.desc}</p>
                  <div className="mb-2">
                    <div className="flex justify-between text-[10px] mb-1">
                      <span className="text-muted-foreground">Progress</span>
                      <span className="font-semibold text-foreground">{p.progress}%</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-primary to-[#2D9C72] rounded-full" style={{ width: `${p.progress}%` }} />
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <div className="flex items-center gap-1"><Users size={11} />{p.team} researchers</div>
                    <button className="text-primary font-semibold hover:underline">Read More →</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Main Content: Feed + Sidebar ── */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 mb-12">

          {/* Feed */}
          <div className="xl:col-span-2">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-foreground font-jakarta">Research Feed</h2>
              <div className="flex bg-muted rounded-xl p-1 gap-1">
                {["latest", "trending", "cited", "ai-picks"].map(f => (
                  <button key={f} onClick={() => setFeedFilter(f)}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-semibold transition-colors capitalize
                      ${feedFilter === f ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
                    {f === "ai-picks" ? "AI Picks" : f === "cited" ? "Most Cited" : f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-5">
              {feedItems.map(item => {
                const tl = typeLabels[item.type];
                const liked = likedPosts.has(item.id);
                const saved = savedPosts.has(item.id);
                return (
                  <article key={item.id} className="bg-card border border-border rounded-2xl overflow-hidden hover:shadow-lg hover:border-primary/15 transition-all group cursor-pointer">
                    <div className="relative h-44 bg-gray-100 overflow-hidden">
                      <img src={item.img} alt={item.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                      <div className="absolute top-3 left-3">
                        <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${tl.color}`}>{tl.label}</span>
                      </div>
                      <div className="absolute top-3 right-3 flex gap-2">
                        {item.tags.map(t => <span key={t} className="text-[10px] bg-white/90 text-foreground px-2 py-0.5 rounded-full font-medium">{t}</span>)}
                      </div>
                    </div>
                    <div className="p-5">
                      <h3 className="text-base font-bold text-foreground font-jakarta mb-2 group-hover:text-primary transition-colors leading-snug">{item.title}</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed mb-4">{item.summary}</p>
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-[10px] font-bold shrink-0">
                          {item.author.split(" ").map(w => w[0]).slice(-2).join("")}
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-foreground">{item.author}</p>
                          <p className="text-[10px] text-muted-foreground">{item.date} · {item.readTime} read</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between pt-3 border-t border-border">
                        <div className="flex items-center gap-4">
                          <button onClick={e => { e.stopPropagation(); setLikedPosts(s => { const n = new Set(s); liked ? n.delete(item.id) : n.add(item.id); return n; }); }}
                            className={`flex items-center gap-1.5 text-xs transition-colors ${liked ? "text-red-500" : "text-muted-foreground hover:text-red-400"}`}>
                            <Heart size={14} fill={liked ? "currentColor" : "none"} /> {item.likes + (liked ? 1 : 0)}
                          </button>
                          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                            <EyeIcon size={14} /> {item.views.toLocaleString()}
                          </div>
                          <button onClick={e => { e.stopPropagation(); setSavedPosts(s => { const n = new Set(s); saved ? n.delete(item.id) : n.add(item.id); return n; }); }}
                            className={`flex items-center gap-1.5 text-xs transition-colors ${saved ? "text-primary" : "text-muted-foreground hover:text-primary"}`}>
                            <Bookmark size={14} fill={saved ? "currentColor" : "none"} /> {saved ? "Saved" : "Save"}
                          </button>
                          <button className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
                            <Share2 size={14} /> Share
                          </button>
                        </div>
                        <button className="text-xs font-bold text-primary hover:underline">Read More →</button>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Trending Topics */}
            <div className="bg-card border border-border rounded-2xl p-5">
              <h3 className="font-bold text-foreground font-jakarta mb-4 flex items-center gap-2"><TrendingUp size={16} className="text-primary" /> Trending Topics</h3>
              <div className="space-y-2">
                {trending.map((t, i) => (
                  <div key={t} className="flex items-center gap-3 py-1.5 cursor-pointer group">
                    <span className="text-sm font-bold text-muted-foreground w-5 shrink-0">#{i + 1}</span>
                    <span className="text-xs text-foreground group-hover:text-primary transition-colors font-medium flex-1">{t}</span>
                    <ArrowUpRight size={12} className="text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                  </div>
                ))}
              </div>
            </div>

            {/* Upcoming Conferences */}
            <div className="bg-card border border-border rounded-2xl p-5">
              <h3 className="font-bold text-foreground font-jakarta mb-4 flex items-center gap-2"><Calendar size={16} className="text-primary" /> Upcoming Conferences</h3>
              <div className="space-y-4">
                {conferences.map(c => (
                  <div key={c.name} className="border border-border rounded-xl p-3 hover:border-primary/30 hover:bg-muted/50 transition-all cursor-pointer group">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className="text-xs font-bold text-foreground leading-snug group-hover:text-primary transition-colors">{c.name}</h4>
                      <div className="shrink-0 text-center bg-primary/8 rounded-lg px-2 py-1">
                        <div className="text-sm font-extrabold text-primary font-jakarta">{c.days}</div>
                        <div className="text-[8px] text-muted-foreground">days</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground mb-2">
                      <MapPin size={10} /> {c.location} · {c.date}
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">{c.speakers} speakers · {c.registered} registered</span>
                      <button className="text-primary font-bold hover:underline">Register</button>
                    </div>
                    <div className="mt-2 text-[9px] text-amber-600 font-semibold bg-amber-50 rounded-lg px-2 py-1">⏰ Abstract deadline: {c.deadline}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Open Datasets */}
            <div className="bg-card border border-border rounded-2xl p-5">
              <h3 className="font-bold text-foreground font-jakarta mb-4 flex items-center gap-2"><Database size={16} className="text-primary" /> Open Datasets</h3>
              <div className="space-y-3">
                {datasets.map(d => (
                  <div key={d.name} className="p-3 bg-muted rounded-xl hover:bg-secondary transition-colors cursor-pointer group">
                    <p className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors mb-1 leading-snug">{d.name}</p>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-2">
                      <span>{d.format}</span><span>·</span><span>{d.size}</span><span>·</span><span>{d.downloads.toLocaleString()} downloads</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">{d.license}</span>
                      <div className="flex gap-1.5">
                        <button className="text-[10px] text-primary font-semibold hover:underline flex items-center gap-1"><SquareCode size={10} /> API</button>
                        <button className="text-[10px] text-primary font-semibold hover:underline flex items-center gap-1"><Download size={10} /> Get</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── Discover Researchers ── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-foreground font-jakarta">Discover Researchers</h2>
            <button className="text-xs text-primary font-semibold">View all 84 →</button>
          </div>
          {/* Filter bar */}
          <div className="flex flex-wrap gap-2 mb-5">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input placeholder="Search by expertise, name, institution..." className="pl-9 pr-4 py-2 text-xs bg-white border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 w-64" />
            </div>
            {["Hydrology", "AI", "Climate", "Machine Learning", "IoT", "GIS"].map(f => (
              <button key={f} className="px-3 py-2 bg-muted text-xs font-medium text-muted-foreground rounded-xl hover:bg-primary hover:text-white transition-colors">{f}</button>
            ))}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {researcherProfiles.map(r => (
              <div key={r.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all group cursor-pointer" onClick={() => setSelectedResearcher(r.id)}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white font-extrabold text-lg shadow-md">
                    {r.avatar}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <h3 className="text-sm font-bold text-foreground font-jakarta truncate group-hover:text-primary transition-colors">{r.name}</h3>
                      {r.active && <div className="w-2 h-2 bg-accent rounded-full shrink-0" />}
                    </div>
                    <p className="text-[10px] text-primary font-semibold truncate">{r.role}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{r.field}</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  {[["H-idx", r.h], ["Pubs", r.pubs], ["Cited", r.citations > 999 ? (r.citations / 1000).toFixed(1) + "K" : r.citations]].map(([l, v]) => (
                    <div key={l as string} className="bg-muted rounded-xl p-2 text-center">
                      <div className="text-sm font-bold text-foreground">{v}</div>
                      <div className="text-[9px] text-muted-foreground">{l}</div>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <button className="flex-1 py-2 bg-primary/8 text-primary text-[10px] font-bold rounded-xl hover:bg-primary hover:text-white transition-colors">View Profile</button>
                  <button className="py-2 px-3 bg-muted text-muted-foreground text-[10px] rounded-xl hover:bg-secondary flex items-center gap-1 transition-colors"><UserPlus size={11} /> Follow</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Latest Publications ── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-foreground font-jakarta">Latest Publications</h2>
            <button className="text-xs text-primary font-semibold">See all 312 →</button>
          </div>
          <div className="space-y-4">
            {publications.map(pub => (
              <div key={pub.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md hover:border-primary/20 transition-all group">
                <div className="flex items-start gap-5">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full ${pub.status === "published" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
                        {pub.status === "published" ? "Published" : "In Review"}
                      </span>
                      <span className="text-[10px] font-bold text-primary">{pub.journal}</span>
                      <span className="text-[10px] text-muted-foreground">{pub.year}</span>
                    </div>
                    <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors mb-1.5 leading-snug">{pub.title}</h3>
                    <p className="text-xs text-muted-foreground mb-3">{pub.authors}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {pub.tags.map(t => <span key={t} className="px-2 py-0.5 bg-primary/8 text-primary text-[10px] rounded-full font-medium">{t}</span>)}
                    </div>
                  </div>
                  <div className="text-center shrink-0 space-y-2">
                    <div>
                      <div className="text-2xl font-extrabold text-foreground font-jakarta">{pub.citations}</div>
                      <div className="text-[9px] text-muted-foreground">citations</div>
                    </div>
                    <div className="px-2 py-1 bg-blue-50 rounded-lg">
                      <div className="text-sm font-bold text-blue-700">{pub.impact}</div>
                      <div className="text-[9px] text-blue-500">Impact Factor</div>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border">
                  <button className="flex items-center gap-1.5 text-[10px] font-semibold text-white bg-primary px-3 py-1.5 rounded-lg hover:bg-primary/90 transition-colors"><Brain size={11} /> AI Summary</button>
                  <button className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"><Download size={12} /> PDF</button>
                  <button className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"><ExternalLink size={12} /> DOI</button>
                  <button className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"><Bookmark size={12} /> Save</button>
                  <button className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"><Share2 size={12} /> Share</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── CTA Banner ── */}
        {!loggedIn && (
          <section className="mb-12">
            <div className="relative bg-gradient-to-br from-[#0F3D2E] via-[#0B6E4F] to-[#1a7a5a] rounded-3xl p-10 text-center overflow-hidden">
              <ParticleCanvas />
              <div className="relative z-10">
                <h2 className="text-3xl font-extrabold text-white font-jakarta mb-3">Join 2,400+ Researchers Worldwide</h2>
                <p className="text-white/70 text-sm mb-6 max-w-md mx-auto">Get personalized research recommendations, save papers, follow researchers, and access AI-powered scientific insights — completely free.</p>
                <button onClick={() => setAuthModal("signup")} className="px-8 py-3.5 bg-accent text-[#0F3D2E] font-extrabold rounded-2xl hover:shadow-xl hover:shadow-accent/20 transition-all text-sm">
                  Create Free Account
                </button>
              </div>
            </div>
          </section>
        )}

      </div>
    </div>
  );
}

// ─── WELCOME / ENTRY PAGE ────────────────────────────────────────────────────
function WelcomePage({ onGuest, onAdmin }: { onGuest: () => void; onAdmin: () => void }) {
  const [adminMode, setAdminMode] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { displayed, cursor } = useTypewriter([
    "Environmental Intelligence",
    "AI-Powered Research",
    "Digital Twin Science",
    "IoT Monitoring Grid",
    "Scientific Excellence",
  ], 55, 2000);

  const handleAdminLogin = () => {
    setError("");
    if (!email || !password) { setError("Please enter your credentials."); return; }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      if (password === "admin" || email.includes("@")) {
        onAdmin();
      } else {
        setError("Invalid credentials. Try any email + any password.");
      }
    }, 1200);
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-[#0A1A12] flex relative" style={{ fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif" }}>
      <ParticleCanvas />

      {/* Decorative rings */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-[900px] h-[900px] border border-white/4 rounded-full" />
        <div className="absolute w-[650px] h-[650px] border border-white/6 rounded-full" />
        <div className="absolute w-[420px] h-[420px] border border-white/8 rounded-full" />
        <div className="absolute w-[200px] h-[200px] bg-primary/10 rounded-full blur-2xl" />
      </div>

      {/* Gradient blobs */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-primary/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-[#2D9C72]/15 rounded-full blur-[100px] pointer-events-none" />

      {/* Content — two-column */}
      <div className="relative z-10 flex w-full h-full">

        {/* LEFT — Brand panel */}
        <div className="hidden lg:flex flex-col justify-between flex-1 px-16 py-12">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center shadow-xl shadow-primary/40">
              <FlaskConical size={20} className="text-white" />
            </div>
            <div>
              <div className="text-white font-extrabold text-lg font-jakarta leading-none">LabAI Research</div>
              <div className="text-white/40 text-[10px] mt-0.5">Ecosystem Platform · v3.2.0</div>
            </div>
          </div>

          {/* Hero text */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/8 border border-white/12 rounded-full text-xs text-white/70 mb-8">
              <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
              World-Class Scientific Ecosystem
            </div>
            <h1 className="text-5xl xl:text-6xl font-extrabold text-white font-jakarta leading-tight mb-4">
              Advancing<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#4ADE80] to-[#2D9C72]">
                {displayed}
              </span>
              <span className={`inline-block w-0.5 h-12 bg-accent ml-1 align-middle ${cursor ? "opacity-100" : "opacity-0"} transition-opacity`} />
            </h1>
            <p className="text-white/50 text-lg max-w-md leading-relaxed">
              An integrated research ecosystem combining AI agents, digital twins, IoT monitoring, and GIS intelligence to accelerate environmental science.
            </p>

            {/* Stats */}
            <div className="flex gap-8 mt-10">
              {[
                { value: "312+", label: "Publications" },
                { value: "84", label: "Researchers" },
                { value: "1,247", label: "IoT Sensors" },
                { value: "8", label: "AI Agents" },
              ].map(s => (
                <div key={s.label}>
                  <div className="text-2xl font-extrabold text-white font-jakarta">{s.value}</div>
                  <div className="text-xs text-white/40 mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom features */}
          <div className="flex gap-3">
            {[
              { icon: Bot, label: "8 AI Agents" },
              { icon: Cpu, label: "Digital Twins" },
              { icon: Wifi, label: "Live IoT Grid" },
              { icon: Map, label: "GIS Maps" },
            ].map(f => (
              <div key={f.label} className="flex items-center gap-2 px-3 py-2 bg-white/6 border border-white/10 rounded-xl text-white/60 text-xs">
                <f.icon size={13} className="text-accent" />
                {f.label}
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT — Entry card */}
        <div className="flex items-center justify-center w-full lg:w-[480px] shrink-0 px-6 py-12">
          <div className="w-full max-w-sm">

            {/* Mobile logo */}
            <div className="flex items-center gap-3 mb-10 lg:hidden">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center">
                <FlaskConical size={20} className="text-white" />
              </div>
              <div className="text-white font-extrabold text-lg font-jakarta">LabAI Research</div>
            </div>

            {!adminMode ? (
              /* ── Mode chooser ── */
              <div className="bg-white/6 backdrop-blur-xl border border-white/12 rounded-3xl p-8 shadow-2xl">
                <div className="text-center mb-8">
                  <h2 className="text-2xl font-extrabold text-white font-jakarta mb-2">Welcome</h2>
                  <p className="text-white/50 text-sm">How would you like to access the platform?</p>
                </div>

                <div className="space-y-3">
                  {/* Guest option */}
                  <button
                    onClick={onGuest}
                    className="w-full group relative bg-white/5 hover:bg-white/10 border border-white/10 hover:border-accent/40 rounded-2xl p-5 text-left transition-all duration-200 hover:shadow-lg hover:shadow-accent/5"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#4ADE80]/20 to-[#2D9C72]/20 border border-[#4ADE80]/25 flex items-center justify-center shrink-0 group-hover:from-accent/30 group-hover:to-[#2D9C72]/30 transition-all">
                        <Globe2 size={22} className="text-accent" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-bold text-sm font-jakarta">Continue as Guest</div>
                        <div className="text-white/45 text-xs mt-0.5">Browse publications, researchers & datasets publicly</div>
                      </div>
                      <ChevronRight size={16} className="text-white/30 group-hover:text-accent group-hover:translate-x-0.5 transition-all shrink-0" />
                    </div>
                    <div className="flex gap-1.5 mt-3 pl-16">
                      {["Publications", "Researchers", "Datasets", "Events"].map(t => (
                        <span key={t} className="text-[9px] px-1.5 py-0.5 bg-white/8 text-white/50 rounded-md">{t}</span>
                      ))}
                    </div>
                  </button>

                  {/* Divider */}
                  <div className="flex items-center gap-3 py-1">
                    <div className="flex-1 h-px bg-white/10" />
                    <span className="text-white/30 text-xs">or</span>
                    <div className="flex-1 h-px bg-white/10" />
                  </div>

                  {/* Admin option */}
                  <button
                    onClick={() => setAdminMode(true)}
                    className="w-full group relative bg-gradient-to-br from-primary/20 to-[#2D9C72]/15 hover:from-primary/30 hover:to-[#2D9C72]/25 border border-primary/30 hover:border-primary/50 rounded-2xl p-5 text-left transition-all duration-200 hover:shadow-lg hover:shadow-primary/15"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary/40 to-[#2D9C72]/30 border border-primary/40 flex items-center justify-center shrink-0">
                        <Shield size={22} className="text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-white font-bold text-sm font-jakarta">Admin / Researcher Login</div>
                        <div className="text-white/45 text-xs mt-0.5">Full platform access — AI agents, dashboards & management</div>
                      </div>
                      <ChevronRight size={16} className="text-white/30 group-hover:text-white/70 group-hover:translate-x-0.5 transition-all shrink-0" />
                    </div>
                    <div className="flex gap-1.5 mt-3 pl-16">
                      {["Dashboard", "AI Agents", "Digital Twins", "IoT", "Admin"].map(t => (
                        <span key={t} className="text-[9px] px-1.5 py-0.5 bg-white/10 text-white/50 rounded-md">{t}</span>
                      ))}
                    </div>
                  </button>
                </div>

                <p className="text-center text-[10px] text-white/25 mt-6 leading-relaxed">
                  By entering, you agree to our Terms of Service and Privacy Policy.<br />
                  LabAI Research Institute · Open Science Initiative
                </p>
              </div>
            ) : (
              /* ── Admin login form ── */
              <div className="bg-white/6 backdrop-blur-xl border border-white/12 rounded-3xl p-8 shadow-2xl">
                <button
                  onClick={() => { setAdminMode(false); setError(""); }}
                  className="flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 mb-6 transition-colors"
                >
                  <ChevronLeft size={14} /> Back
                </button>

                <div className="flex items-center gap-3 mb-6">
                  <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center shadow-lg shadow-primary/40">
                    <Shield size={18} className="text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-extrabold text-white font-jakarta leading-tight">Admin Login</h2>
                    <p className="text-white/40 text-xs">Restricted — authorized personnel only</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-white/60 mb-1.5 block">Institutional Email</label>
                    <div className="relative">
                      <Mail size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
                      <input
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleAdminLogin()}
                        placeholder="admin@labai-research.org"
                        className="w-full pl-10 pr-4 py-3 bg-white/8 border border-white/12 text-white placeholder:text-white/25 text-sm rounded-xl focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all"
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="text-xs font-semibold text-white/60">Password</label>
                      <button className="text-[10px] text-accent/70 hover:text-accent transition-colors">Forgot password?</button>
                    </div>
                    <div className="relative">
                      <Shield size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/30" />
                      <input
                        type="password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        onKeyDown={e => e.key === "Enter" && handleAdminLogin()}
                        placeholder="••••••••••"
                        className="w-full pl-10 pr-4 py-3 bg-white/8 border border-white/12 text-white placeholder:text-white/25 text-sm rounded-xl focus:outline-none focus:border-primary/60 focus:ring-1 focus:ring-primary/30 transition-all"
                      />
                    </div>
                  </div>

                  {error && (
                    <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 border border-red-500/20 px-3 py-2 rounded-xl">
                      <AlertCircle size={13} /> {error}
                    </div>
                  )}

                  <button
                    onClick={handleAdminLogin}
                    disabled={loading}
                    className="w-full py-3.5 bg-gradient-to-r from-primary to-[#2D9C72] text-white font-bold rounded-xl hover:shadow-xl hover:shadow-primary/25 transition-all text-sm flex items-center justify-center gap-2 disabled:opacity-70"
                  >
                    {loading ? (
                      <><RefreshCw size={16} className="animate-spin" /> Authenticating…</>
                    ) : (
                      <><LogIn size={16} /> Sign In to Platform</>
                    )}
                  </button>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-white/10" /></div>
                    <div className="relative flex justify-center"><span className="bg-transparent px-3 text-[10px] text-white/25">or use SSO</span></div>
                  </div>

                  <button className="w-full py-2.5 border border-white/12 rounded-xl text-sm font-medium text-white/50 hover:bg-white/8 transition-colors flex items-center justify-center gap-2">
                    <Globe size={14} /> Sign in with Google Workspace
                  </button>
                </div>

                <div className="mt-5 p-3 bg-accent/8 border border-accent/15 rounded-xl">
                  <p className="text-[10px] text-accent/80 leading-relaxed text-center">
                    <span className="font-bold text-accent">Demo tip:</span> Enter any email + any password to access the full admin platform.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── GENERIC PLACEHOLDER PAGE ─────────────────────────────────────────────────
function PlaceholderPage({ title, desc, icon: Icon }: { title: string; desc: string; icon: React.ElementType }) {
  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="text-center">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center mx-auto mb-5">
          <Icon size={36} className="text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground font-jakarta mb-2">{title}</h2>
        <p className="text-muted-foreground max-w-xs mx-auto text-sm leading-relaxed">{desc}</p>
        <div className="mt-6 px-6 py-3 bg-primary text-white rounded-xl text-sm font-semibold inline-flex items-center gap-2 cursor-pointer hover:bg-primary/90 transition-colors">
          <Play size={14} /> Explore Module
        </div>
      </div>
    </div>
  );
}

// ─── APP ROOT ────────────────────────────────────────────────────────────────
export default function App() {
  const auth = useAuth();
  const [entry, setEntry] = useState<"welcome" | "guest" | "admin">("welcome");
  const [page, setPage] = useState<Page>("home");
  const [collapsed, setCollapsed] = useState(false);
  const [dark, setDark] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  const renderPage = useCallback(() => {
    switch (page) {
      case "home": return <HomePage setPage={setPage} />;
      case "dashboard": return <DashboardPage />;
      case "projects": return <ProjectsPage />;
      case "publications": return <PublicationsPage />;
      case "researchers": return <ResearchersPage />;
      case "twins": return <DigitalTwinsPage />;
      case "iot": return <IoTPage />;
      case "watch": return <WatchPage />;
      case "theses": return <PlaceholderPage title="Theses & Masters" desc="Track PhD and master's theses, progress, supervisors, and defense calendars." icon={GraduationCap} />;
      case "gis": return <PlaceholderPage title="GIS Maps & Spatial Analytics" desc="Interactive spatial mapping, geographic pattern analysis, and environmental overlay layers." icon={Map} />;
      case "datasets": return <PlaceholderPage title="Open Data Portal" desc="156 curated datasets with API access, Jupyter notebook previews, and geospatial downloads." icon={Database} />;
      case "events": return <PlaceholderPage title="Events & Conferences" desc="Scientific events timeline, photo gallery, registration, and post-event archives." icon={Globe} />;
      case "news": return <PlaceholderPage title="News & Updates" desc="Magazine-style layout featuring featured articles, lab announcements, and media coverage." icon={Newspaper} />;
      case "admin": return <PlaceholderPage title="Administration" desc="User management, access control, system configuration, and audit logs." icon={Settings} />;
      default: return <DashboardPage />;
    }
  }, [page]);

  const FAB = (
    <button
      onClick={() => setAiOpen(o => !o)}
      className={`fixed bottom-6 right-6 w-14 h-14 text-white rounded-2xl shadow-xl shadow-primary/30 flex items-center justify-center hover:scale-110 transition-all z-50
        ${aiOpen ? "bg-foreground rotate-12" : "bg-gradient-to-br from-primary to-[#2D9C72]"}`}
    >
      {aiOpen ? <X size={22} /> : <Brain size={22} />}
    </button>
  );

  if (entry === "welcome") {
    return (
      <WelcomePage
        onGuest={() => setEntry("guest")}
        onAdmin={() => { setEntry("admin"); setPage("home"); }}
      />
    );
  }

  if (entry === "guest") {
    return (
      <div style={{ fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif" }}>
        <VisitorPortalPage onAdminLogin={() => { setEntry("admin"); setPage("home"); }} />
        <AIAssistantPanel open={aiOpen} onClose={() => setAiOpen(false)} />
        {FAB}
      </div>
    );
  }

  return (
    <div className={`h-screen flex overflow-hidden bg-background font-sans ${dark ? "dark" : ""}`}
      style={{ fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif" }}>
      <Sidebar page={page} setPage={setPage} collapsed={collapsed} setCollapsed={setCollapsed} dark={dark} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopNav dark={dark} setDark={setDark} page={page} onSignOut={() => { void auth.signOut(); setEntry("welcome"); }} />
        <main className="flex-1 overflow-hidden">
          {renderPage()}
        </main>
      </div>

      <AIAssistantPanel open={aiOpen} onClose={() => setAiOpen(false)} />
      {FAB}
    </div>
  );
}
