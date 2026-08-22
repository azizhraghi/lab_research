
import { useState, useEffect, useRef, useCallback } from "react";
import {
  LayoutDashboard, FolderKanban, BookOpen, Users, GraduationCap,
  Eye, Bot, Cpu, Wifi, Map, Database, Calendar,
  Newspaper, Settings, ChevronLeft, ChevronRight, Search,
  Bell, Moon, Sun, X, TrendingUp, Activity,
  Globe, ArrowUpRight, ArrowDownRight,
  AlertCircle, Clock, Play, RefreshCw, Info,
  Download, ExternalLink,
  Thermometer, Droplets, Wind, Gauge, MapPin,
  Brain, Network, Shield, Target, FlaskConical, Microscope,
  MoreHorizontal,
  Bookmark, Share2, Send,
  Mic, Sparkles,
  Mail, SquareCode,
  Leaf, Droplet, ThermometerSun, SatelliteDish, BarChart2,
  BrainCircuit, Sprout, Waves, Globe2, Radio, LogIn,
  Plus, Loader2, CheckCircle2, Trash2, Upload, Pencil
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, LineChart as ReLineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";
import { useAuth } from "../auth/AuthContext";
import type { Article, Researcher as ApiResearcher, HistoriqueEvenement, Projet, Personnel, Equipement, Parcel, ParcelDetail, SensorReadingFull, CalibrationProfile, Alerte, IrrigationEvent, Recommendation, PlanningTask } from "../api/types";
import { API_BASE_URL } from "../lib/apiClient";
import { useArticles, useTriggerScrape, useSources, useCreateSource, useDeleteSource } from "../api/veille";
import {
  useResearchers,
  useSyncResearcher,
  useCreateResearcher,
  useUpdateResearcher,
  useDeleteResearcher,
  useResearcherPublications,
  useSyncPublications,
  useSyncScholarPublications,
} from "../api/biblio";
import { useProjets, useCreateProjet, usePersonnels, useEquipements, useBudgets,
         useCreatePersonnel, useCreateEquipement, useCreateBudget, useDeleteProjet } from "../api/mis";
import { useQualiteStatus, useRapports, useValiderEntite, type QualiteEntite } from "../api/qualite";
import { useOrchestratorStatus, useAlertes, useHistorique, useResolveAlerte, useTriggerEvent, usePlanningTasks, usePlanningProposals, useCreatePlanningTask, useGeneratePlanningProposal, useApprovePlanningProposal } from "../api/orchestrateur";
import {
  useParcels,
  useParcel,
  useParcelForecast,
  useRefreshForecast,
  useRunSimulation,
  useSimulationRuns,
  useOptimisationRuns,
  useRunOptimisation,
  useCreateParcel,
  useReadings,
  useCreateReading,
  useImportReadings,
  useApplyCalibration,
  useCalibrations,
  useDeleteReading,
  useRunCalibration,
  useIrrigationEvents,
  useRecordIrrigation,
  useRecommend,
  useApproveRecommendation,
} from "../api/digitaltwin";
import type { SensorReadingDeleteResult } from "../api/digitaltwin";

// ─── Types ─────────────────────────────────────────────────────────────────
type Page =
  | "home" | "dashboard" | "projects" | "publications" | "researchers"
  | "theses" | "watch" | "twins" | "iot" | "gis"
  | "datasets" | "events" | "news" | "admin"
  | "agents" | "visitor";

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

// ─── Form primitives ────────────────────────────────────────────────────────
// Small shared building blocks for the "create" dialogs. Every form in this app
// posts to a real endpoint; these components only handle presentation, and the
// error strip renders whatever FastAPI put in `detail` (apiFetch copies it onto
// ApiError.message) so a 403 from a role guard or a 422 from a schema mismatch
// is shown to the user verbatim instead of being swallowed.

function Modal({ open, onClose, title, subtitle, children }: {
  open: boolean; onClose: () => void; title: string;
  subtitle?: string; children: React.ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-start justify-between gap-4 p-5 border-b border-border">
          <div>
            <h3 className="text-base font-bold text-foreground font-jakarta">{title}</h3>
            {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors shrink-0">
            <X size={18} />
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

function Field({ label, hint, required, children }: {
  label: string; hint?: string; required?: boolean; children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold text-foreground">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
      </span>
      {hint && <span className="block text-[11px] text-muted-foreground mb-1">{hint}</span>}
      <div className={hint ? "" : "mt-1"}>{children}</div>
    </label>
  );
}

const inputCls =
  "w-full px-3 py-2 text-sm bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 transition-all";

/** Compact labelled figure for read-only result grids. */
function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</div>
      <div className="text-sm font-bold text-foreground font-mono">{value}</div>
      {sub && <div className="text-[10px] text-muted-foreground">{sub}</div>}
    </div>
  );
}

function FormError({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : String(error);
  return (
    <div className="flex items-start gap-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
      <AlertCircle size={14} className="shrink-0 mt-0.5" />
      <span className="break-words">{message}</span>
    </div>
  );
}

function SubmitButton({ pending, label }: { pending: boolean; label: string }) {
  return (
    <button type="submit" disabled={pending}
      className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 transition-all duration-200">
      {pending ? <Loader2 size={15} className="animate-spin" /> : <Plus size={15} />}
      {pending ? "Saving…" : label}
    </button>
  );
}

// ─── Data ───────────────────────────────────────────────────────────────────
// The eight backend agents. `key` is each agent's own `name` attribute (see
// agents/<dir>/agent.py) — that value travels on every event as `source_agent`,
// so it is how we match live orchestrator telemetry to a card. Note that
// digital_twin uses an underscore while its directory is `digitaltwin` and its
// API prefix is /api/twin. Descriptions state what the agent actually does; the
// numbers on each card come from the orchestrator's event history at runtime.
const agents: {
  id: number; key: string; name: string; icon: React.ElementType;
  desc: string; endpoint: string; page: Page;
}[] = [
  { id: 1, key: "veille", name: "Scientific Watch Agent", icon: Eye, endpoint: "/api/veille", page: "watch",
    desc: "Fetches RSS/Atom and PubMed sources, embeds and de-duplicates articles, then tags and summarises them." },
  { id: 2, key: "bibliometrie", name: "Bibliometric Agent", icon: BookOpen, endpoint: "/api/biblio", page: "researchers",
    desc: "Resolves researcher metrics via Google Scholar → Semantic Scholar → OpenAlex and regenerates CV PDFs." },
  { id: 3, key: "digital_twin", name: "Digital Twin / IoT Agent", icon: Wifi, endpoint: "/api/twin", page: "iot",
    desc: "Ingests parcel sensor readings, flags data-quality issues, pulls forecasts and issues irrigation advice." },
  { id: 4, key: "simulation", name: "Simulation Agent", icon: Cpu, endpoint: "/api/simulation", page: "twins",
    desc: "Runs baseline-versus-scenario water-balance projections over a configurable day horizon." },
  { id: 5, key: "optimisation", name: "Optimization Agent", icon: Target, endpoint: "/api/optimisation", page: "twins",
    desc: "Computes irrigation schedules under daily-maximum and total-quota constraints." },
  { id: 6, key: "mis", name: "MIS Agent", icon: Database, endpoint: "/api/mis", page: "projects",
    desc: "Manages projects, staff, equipment and budgets, emitting an event on every change." },
  { id: 7, key: "qualite", name: "Quality Agent", icon: Shield, endpoint: "/api/qualite", page: "admin",
    desc: "Validates MIS entities for completeness and GDPR compliance, producing conformity reports." },
  { id: 8, key: "orchestrateur", name: "Orchestrator Agent", icon: Network, endpoint: "/api/orchestrateur", page: "agents",
    desc: "Routes every event through its rule table, raises alerts and keeps the shared event history." },
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
    { icon: Bot, label: "AI Agents", page: "agents" },
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
  const { user } = useAuth();
  const { data: navAlertes } = useAlertes();
  const [notifsRead, setNotifsRead] = useState(false);
  const notifs = notifsRead ? 0 : (navAlertes?.length ?? 0);

  // Supabase gives us an email and a role claim, not a display name.
  const displayName = user?.email ? user.email.split("@")[0].replace(/[._-]+/g, " ") : "Signed out";
  const roleLabel = user ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : "—";

  const labels: Record<Page, string> = {
    home: "Home", dashboard: "Dashboard", projects: "Research Projects",
    publications: "Publications", researchers: "Researchers", theses: "Theses & Masters",
    watch: "Scientific Watch", twins: "Digital Twins",
    iot: "IoT Monitoring", gis: "GIS Maps", datasets: "Open Datasets",
    events: "Events", news: "News & Updates", admin: "Administration", agents: "AI Agents", visitor: "Public Visitor Portal",
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
      <button
        className="relative p-2 rounded-xl hover:bg-secondary text-muted-foreground transition-colors"
        title={notifs > 0 ? `${notifs} active alert${notifs === 1 ? "" : "s"}` : "No active alerts"}
        onClick={() => setNotifsRead(true)}
      >
        <Bell size={18} />
        {notifs > 0 && <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">{notifs}</span>}
      </button>

      {/* Dark mode */}
      <button onClick={() => setDark(!dark)} className="p-2 rounded-xl hover:bg-secondary text-muted-foreground transition-colors">
        {dark ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      {/* Profile */}
      <div className="flex items-center gap-2 pl-2">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white text-xs font-bold">
          {initialsOf(displayName)}
        </div>
        <div className="hidden md:block text-left">
          <div className="text-xs font-semibold text-foreground capitalize">{displayName}</div>
          <div className="text-[10px] text-muted-foreground">{roleLabel}</div>
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
  const { data: projets } = useProjets();
  const { data: hpResearchers } = useResearchers();
  const { data: hpArticles } = useArticles();
  const { data: hpParcels } = useParcels();
  const { data: hpAlertes } = useAlertes();
  const { data: hpSources } = useSources();

  const stats = [
    { label: "Active Projects", value: projets?.filter(p => p.statut === "en_cours").length ?? 0, suffix: "", icon: FolderKanban },
    { label: "Publications", value: hpArticles?.length ?? 0, suffix: "", icon: BookOpen },
    { label: "Researchers", value: hpResearchers?.length ?? 0, suffix: "", icon: Users },
    { label: "Digital Twin Parcels", value: hpParcels?.length ?? 0, suffix: "", icon: Cpu },
    // Not "running" — this is how many agent modules the gateway mounts. Live
    // per-agent activity is on the Agents page, from orchestrator event history.
    { label: "Agent Modules", value: agents.length, suffix: "", icon: Bot },
    { label: "Total Projects", value: projets?.length ?? 0, suffix: "", icon: Database },
  ];

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
            AI-Powered Research Laboratory Platform
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
            { label: "Articles Collected", value: String(hpArticles?.length ?? 0), color: "bg-white/10" },
            { label: "Monitored Parcels", value: String(hpParcels?.length ?? 0), color: "bg-accent/20" },
            { label: "Active Alerts", value: String(hpAlertes?.length ?? 0), color: "bg-white/10" },
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
            { icon: Wifi, title: "IoT Monitoring Grid", desc: `${hpParcels?.length ?? 0} monitored parcels streaming soil-moisture, rainfall and evapotranspiration readings.`, page: "iot" as Page, color: "from-amber-50 to-orange-50" },
            { icon: Map, title: "GIS Intelligence", desc: "Spatial analytics and interactive mapping for geographic pattern discovery.", page: "gis" as Page, color: "from-teal-50 to-cyan-50" },
            { icon: BookOpen, title: "Publication Hub", desc: `${hpArticles?.length ?? 0} collected publications with bibliometric analytics and citation tracking.`, page: "publications" as Page, color: "from-purple-50 to-pink-50" },
            { icon: Database, title: "Open Data Portal", desc: "Curated datasets with API access, notebook previews, and geospatial downloads.", page: "datasets" as Page, color: "from-rose-50 to-red-50" },
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

      {/* Monitored sources — real feeds the watch agent polls. Replaced a
          hardcoded "international partners" logo wall that named institutions
          the platform has no relationship with. */}
      <section className="px-10 py-10 bg-white border-t border-border">
        <p className="text-center text-xs font-semibold text-muted-foreground uppercase tracking-widest mb-6">
          Literature Sources Monitored by the Watch Agent
        </p>
        {hpSources && hpSources.length > 0 ? (
          <div className="flex flex-wrap justify-center gap-4">
            {hpSources.map(s => (
              <div key={s.id} className="px-5 py-3 border border-border rounded-xl text-center hover:border-primary/30 hover:bg-primary/5 transition-all">
                <div className="text-sm font-semibold text-foreground">{s.name}</div>
                <div className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">
                  {s.type} · {s.active ? "active" : "paused"}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-sm text-muted-foreground">
            No sources registered yet — add one via <span className="font-mono">POST /api/veille/sources</span>.
          </p>
        )}
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
function DashboardPage({ onNavigate }: { onNavigate: (page: Page) => void }) {
  const [setupAlert, setSetupAlert] = useState<Alerte | null>(null);
  const { data: projets } = useProjets();
  const { data: dbResearchers } = useResearchers();
  const { data: articles } = useArticles();
  const { data: parcels } = useParcels();
  const { data: historique } = useHistorique();
  const { data: alertes } = useAlertes();
  const resolveAlerte = useResolveAlerte();
  const setupProjectName = typeof setupAlert?.context.project_name === "string"
    ? setupAlert.context.project_name
    : "Project";

  const projectCount = projets?.length ?? 0;
  const activeProjects = projets?.filter(p => p.statut === "en_cours").length ?? 0;
  const researcherCount = dbResearchers?.length ?? 0;
  const articleCount = articles?.length ?? 0;
  const parcelCount = parcels?.length ?? 0;
  const alertCount = alertes?.length ?? 0;

  const kpis = [
    { label: "Active Projects", value: activeProjects, change: 0, icon: FolderKanban, color: "primary" as const, trend: [] as number[] },
    { label: "Researchers", value: researcherCount, change: 0, icon: Users, color: "emerald" as const, trend: [] as number[] },
    { label: "Articles Collected", value: articleCount, change: 0, icon: BookOpen, color: "blue" as const, trend: [] as number[] },
    { label: "Digital Twin Parcels", value: parcelCount, change: 0, icon: Cpu, color: "amber" as const, trend: [] as number[] },
    { label: "Active Alerts", value: alertCount, change: 0, icon: Bell, color: "purple" as const, trend: [] as number[] },
    { label: "Total Projects", value: projectCount, change: 0, icon: Database, color: "primary" as const, trend: [] as number[] },
  ];

  // The orchestrator appends to its history in arrival order, so the newest
  // events sit at the end — reverse before taking the top five.
  const recentEvents = [...(historique ?? [])].reverse().slice(0, 5);

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full scrollbar-hide">
      {/* KPIs */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-foreground font-jakarta">Platform Overview</h2>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
            Live
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
          {kpis.map(k => <KPICard key={k.label} {...k} />)}
        </div>
      </div>

      <Modal
        open={setupAlert !== null}
        onClose={() => !resolveAlerte.isPending && setSetupAlert(null)}
        title="Set up Digital Twin parcel"
        subtitle={`Complete the field profile for ${setupProjectName}. The task closes only after the parcel is created.`}
      >
        <NewParcelForm
          initialName={`${setupProjectName} parcel`}
          projectId={typeof setupAlert?.context.project_id === "string" ? setupAlert.context.project_id : undefined}
          onDone={() => setSetupAlert(null)}
          onCreated={() => {
            if (setupAlert) {
              resolveAlerte.mutate(setupAlert.id, { onSuccess: () => setSetupAlert(null) });
            }
          }}
        />
        <FormError error={resolveAlerte.error} />
      </Modal>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Activity Feed from orchestrator */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Recent Events</h3>
          {recentEvents.length === 0 && (
            <p className="text-xs text-muted-foreground">No events recorded yet.</p>
          )}
          <div className="space-y-3">
            {recentEvents.map((evt) => (
              <div key={evt.id} className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-primary/10 text-primary">
                  <Activity size={13} />
                </div>
                <div>
                  <p className="text-xs text-foreground leading-snug">{evt.type_evenement} from <span className="font-semibold">{evt.source_agent}</span></p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">{new Date(evt.timestamp).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Active Alerts */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <h3 className="font-bold text-foreground font-jakarta mb-4">Active Alerts</h3>
          {(!alertes || alertes.length === 0) && (
            <p className="text-xs text-muted-foreground">No active alerts.</p>
          )}
          <div className="space-y-3">
            {(alertes ?? []).slice(0, 5).map((a) => {
              const color = a.niveau === "critique" ? "bg-red-100 text-red-600" : a.niveau === "rouge" ? "bg-red-50 text-red-500" : a.niveau === "orange" ? "bg-amber-100 text-amber-700" : "bg-blue-50 text-blue-600";
              return (
                <div key={a.id} className="flex items-center gap-3 p-3 bg-muted rounded-xl">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 ${color}`}>
                    <AlertCircle size={16} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-foreground leading-snug">{a.message}</p>
                    <p className="text-[10px] text-muted-foreground">{a.niveau} · {new Date(a.timestamp).toLocaleString()}</p>
                  </div>
                  {a.context.task_type === "parcel_setup" && (
                    <button
                      onClick={() => setSetupAlert(a)}
                      className="shrink-0 px-2.5 py-1.5 text-[10px] font-semibold text-primary border border-primary/30 rounded-lg hover:bg-primary/10 transition-colors"
                    >
                      Set up parcel
                    </button>
                  )}
                  {a.context.task_type === "irrigation_review" && (
                    <button
                      onClick={() => {
                        const parcelId = a.context.parcel_id;
                        if (typeof parcelId === "number") window.sessionStorage.setItem("lrste.iot.parcelId", String(parcelId));
                        onNavigate("iot");
                      }}
                      className="shrink-0 px-2.5 py-1.5 text-[10px] font-semibold text-primary border border-primary/30 rounded-lg hover:bg-primary/10 transition-colors"
                    >
                      Review irrigation
                    </button>
                  )}
                  {a.context.task_type !== "parcel_setup" && a.context.task_type !== "irrigation_review" && (
                    <button
                      onClick={() => resolveAlerte.mutate(a.id)}
                      disabled={resolveAlerte.isPending}
                      className="shrink-0 px-2.5 py-1.5 text-[10px] font-semibold text-primary border border-primary/30 rounded-lg hover:bg-primary/10 disabled:opacity-50 transition-colors"
                    >
                      {resolveAlerte.isPending ? "Resolving…" : "Resolve"}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Articles from veille */}
        <div className="bg-card border border-border rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-foreground font-jakarta">Recent Articles</h3>
          </div>
          {(!articles || articles.length === 0) && (
            <p className="text-xs text-muted-foreground">No articles collected yet. Trigger a scrape from the Watch page.</p>
          )}
          <div className="space-y-3">
            {(articles ?? []).slice(0, 4).map(a => (
              <div key={a.id} className="border-l-2 border-primary/30 pl-3">
                <p className="text-xs font-medium text-foreground leading-snug line-clamp-2">{a.title}</p>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {a.authors?.slice(0, 2).join(", ")}
                  {a.published_at ? ` · ${new Date(a.published_at).getFullYear()}` : ""}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── PROJECTS PAGE ──────────────────────────────────────────────────────────

// POST /api/mis/projets/ takes a ProjetSchema (agents/mis/schemas.py). `id` is
// server-generated (uuid4 default) so the form omits it. `statut` is a Literal —
// only the four values below are accepted, anything else is a 422.
function NewProjectForm({ onDone }: { onDone: () => void }) {
  const create = useCreateProjet();
  const [nom, setNom] = useState("");
  const [description, setDescription] = useState("");
  const [statut, setStatut] = useState<Projet["statut"]>("planifie");
  const [dateDebut, setDateDebut] = useState(new Date().toISOString().slice(0, 10));
  const [dateFin, setDateFin] = useState("");
  const [budget, setBudget] = useState("0");
  const [responsable, setResponsable] = useState("");

  return (
    <form
      className="space-y-4"
      onSubmit={e => {
        e.preventDefault();
        create.mutate(
          {
            nom: nom.trim(),
            description: description.trim() || null,
            statut,
            date_debut: dateDebut,
            date_fin_prevue: dateFin || null,
            budget_alloue: Number(budget) || 0,
            responsable: responsable.trim(),
          },
          { onSuccess: onDone },
        );
      }}
    >
      <Field label="Project name" required>
        <input className={inputCls} value={nom} onChange={e => setNom(e.target.value)} required placeholder="Water-stress modelling of durum wheat" />
      </Field>
      <Field label="Description">
        <textarea className={inputCls} rows={3} value={description} onChange={e => setDescription(e.target.value)} />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Lead researcher" required>
          <input className={inputCls} value={responsable} onChange={e => setResponsable(e.target.value)} required />
        </Field>
        <Field label="Status">
          <select className={inputCls} value={statut} onChange={e => setStatut(e.target.value as Projet["statut"])}>
            <option value="planifie">Planning</option>
            <option value="en_cours">Active</option>
            <option value="termine">Completed</option>
            <option value="suspendu">Suspended</option>
          </select>
        </Field>
        <Field label="Start date" required>
          <input type="date" className={inputCls} value={dateDebut} onChange={e => setDateDebut(e.target.value)} required />
        </Field>
        <Field label="Planned end">
          <input type="date" className={inputCls} value={dateFin} onChange={e => setDateFin(e.target.value)} />
        </Field>
      </div>
      <Field label="Allocated budget">
        <input type="number" min="0" step="any" className={inputCls} value={budget} onChange={e => setBudget(e.target.value)} />
      </Field>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-all duration-200">
          Cancel
        </button>
        <SubmitButton pending={create.isPending} label="Create project" />
      </div>
    </form>
  );
}

function ProjectsPage() {
  const [view, setView] = useState<"kanban" | "timeline">("kanban");
  const [creating, setCreating] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState<Projet | null>(null);
  const { data: projets, isLoading, error } = useProjets();
  const deleteProjet = useDeleteProjet();

  const statusCols = ["planifie", "en_cours", "termine"] as const;
  const statusLabels: Record<string, string> = { planifie: "Planning", en_cours: "Active", termine: "Completed", suspendu: "Suspended" };
  const statusColors: Record<string, string> = {
    planifie: "bg-amber-100 text-amber-700 border-amber-200",
    en_cours: "bg-emerald-100 text-emerald-700 border-emerald-200",
    termine: "bg-blue-100 text-blue-700 border-blue-200",
    suspendu: "bg-muted text-muted-foreground border-border",
  };

  const activeCount = projets?.filter(p => p.statut === "en_cours").length ?? 0;
  const totalBudget = projets?.reduce((s, p) => s + p.budget_alloue, 0) ?? 0;

  // Timeline geometry from the real dates: every bar is positioned inside the
  // window spanned by the earliest start and the latest planned end. Projects
  // with no planned end get a minimum-width marker at their start date.
  const bounds = (projets ?? []).flatMap(p => {
    const s = new Date(p.date_debut).getTime();
    if (Number.isNaN(s)) return [];
    const e = p.date_fin_prevue ? new Date(p.date_fin_prevue).getTime() : s;
    return [s, Number.isNaN(e) ? s : e];
  });
  const winStart = bounds.length ? Math.min(...bounds) : 0;
  const span = (bounds.length ? Math.max(...bounds) : 0) - winStart || 1;
  const barFor = (p: Projet) => {
    const s = new Date(p.date_debut).getTime();
    if (Number.isNaN(s)) return null;
    const raw = p.date_fin_prevue ? new Date(p.date_fin_prevue).getTime() : s;
    const end = Number.isNaN(raw) ? s : Math.max(raw, s);
    return {
      left: ((s - winStart) / span) * 100,
      width: Math.max(3, ((end - s) / span) * 100),
    };
  };

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Research Projects</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            {projets ? `${projets.length} projects · ${activeCount} active · ${totalBudget.toLocaleString()} total budget` : "Loading…"}
          </p>
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
          <button onClick={() => setCreating(true)}
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200">
            <Plus size={14} />New project
          </button>
        </div>
      </div>

      <Modal open={creating} onClose={() => setCreating(false)} title="New research project"
        subtitle="Stored by the MIS agent · POST /api/mis/projets/">
        <NewProjectForm onDone={() => setCreating(false)} />
      </Modal>

      <Modal
        open={projectToDelete !== null}
        onClose={() => !deleteProjet.isPending && setProjectToDelete(null)}
        title="Delete research project"
        subtitle="This permanently removes the project from the MIS database."
      >
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Delete <span className="font-semibold text-foreground">{projectToDelete?.nom}</span>? This action cannot be undone.
          </p>
          <FormError error={deleteProjet.error} />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setProjectToDelete(null)}
              disabled={deleteProjet.isPending}
              className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-50 transition-all"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => projectToDelete && deleteProjet.mutate(projectToDelete.id, { onSuccess: () => setProjectToDelete(null) })}
              disabled={deleteProjet.isPending}
              className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              {deleteProjet.isPending ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
              {deleteProjet.isPending ? "Deleting…" : "Delete project"}
            </button>
          </div>
        </div>
      </Modal>

      {isLoading && (
        <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
          <RefreshCw size={16} className="animate-spin mr-2" />Loading projects…
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-500">
          <AlertCircle size={16} />Failed to load projects: {(error as Error).message}
        </div>
      )}

      {!isLoading && !error && projets && projets.length === 0 && (
        <div className="bg-card border border-border rounded-2xl p-10 text-center">
          <FolderKanban size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm font-semibold text-foreground">No projects yet</p>
          <p className="text-xs text-muted-foreground mt-1 mb-4">
            The MIS agent has no projects on record. Create the first one to start tracking budget, staff and equipment against it.
          </p>
          <button onClick={() => setCreating(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200">
            <Plus size={15} />New project
          </button>
        </div>
      )}

      {!isLoading && !error && projets && projets.length > 0 && view === "kanban" && (
        <div className="grid grid-cols-3 gap-5">
          {statusCols.map(status => {
            const col = projets.filter(p => p.statut === status);
            return (
              <div key={status}>
                <div className="flex items-center justify-between mb-3">
                  <div className={`px-3 py-1 text-xs font-semibold rounded-full border ${statusColors[status]}`}>
                    {statusLabels[status]}
                  </div>
                  <span className="text-xs text-muted-foreground">{col.length}</span>
                </div>
                <div className="space-y-3">
                  {col.map(proj => (
                    <div key={proj.id} className="bg-card border border-border rounded-2xl p-4 hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer group">
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="text-sm font-semibold text-foreground leading-tight pr-2 group-hover:text-primary transition-colors">{proj.nom}</h4>
                        <MoreHorizontal size={16} className="text-muted-foreground shrink-0 mt-0.5" />
                      </div>
                      {proj.description && (
                        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{proj.description}</p>
                      )}
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        <div className="flex items-center gap-1"><Users size={11} />{proj.responsable}</div>
                        {proj.date_fin_prevue && <div className="flex items-center gap-1"><Clock size={11} />{proj.date_fin_prevue}</div>}
                        <div className="font-semibold">{proj.budget_alloue.toLocaleString()}</div>
                      </div>
                      <button
                        onClick={e => { e.stopPropagation(); setProjectToDelete(proj); }}
                        className="mt-3 flex items-center gap-1 text-[10px] font-semibold text-red-600 hover:text-red-700"
                      >
                        <Trash2 size={11} /> Delete project
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {!isLoading && !error && projets && projets.length > 0 && view === "timeline" && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-border">
            <h3 className="font-bold text-foreground font-jakarta">Project Timeline</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              {bounds.length
                ? `${new Date(winStart).toLocaleDateString()} → ${new Date(winStart + span).toLocaleDateString()} · bars span each project's start to planned end`
                : "No dated projects yet."}
            </p>
          </div>
          <div className="overflow-x-auto">
            <div className="p-5 min-w-[800px]">
              {projets.map(proj => {
                const bar = barFor(proj);
                return (
                  <div key={proj.id} className="flex items-center gap-4 mb-4">
                    <div className="w-56 shrink-0">
                      <p className="text-xs font-medium text-foreground truncate">{proj.nom}</p>
                      <p className="text-[10px] text-muted-foreground">{proj.date_debut}</p>
                    </div>
                    <div className="flex-1 h-8 bg-muted rounded-xl relative overflow-hidden">
                      {bar ? (
                        <div
                          className="absolute top-1 bottom-1 rounded-lg bg-gradient-to-r from-primary to-[#2D9C72] flex items-center px-2 min-w-[3rem]"
                          style={{ left: `${bar.left}%`, width: `${bar.width}%` }}
                          title={`${proj.date_debut} → ${proj.date_fin_prevue ?? "no planned end"}`}
                        >
                          <span className="text-[10px] text-white font-semibold truncate">{statusLabels[proj.statut]}</span>
                        </div>
                      ) : (
                        <span className="absolute inset-0 flex items-center px-2 text-[10px] text-muted-foreground">
                          No valid start date
                        </span>
                      )}
                    </div>
                    <div className="w-24 text-xs text-muted-foreground shrink-0 text-right">{proj.date_fin_prevue ?? "—"}</div>
                  </div>
                );
              })}
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
  const [search, setSearch] = useState("");
  const { data: articles, isLoading } = useArticles();

  // Filter chips are the tags the veille agent actually assigned, most common
  // first. NB: `Map` resolves to the lucide-react icon here, so use a record.
  const tagFreq: Record<string, number> = {};
  for (const a of articles ?? []) {
    for (const t of a.tags) {
      const key = t.tag.trim();
      if (key) tagFreq[key] = (tagFreq[key] ?? 0) + 1;
    }
  }
  const tags = ["All", ...Object.entries(tagFreq).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([t]) => t)];

  const filtered = (articles ?? []).filter(a => {
    const matchesTag = filter === "all" || a.tags.some(t => t.tag.toLowerCase() === filter);
    const matchesSearch = !search || a.title.toLowerCase().includes(search.toLowerCase());
    return matchesTag && matchesSearch;
  });

  // BibTeX is built client-side from the collected fields — the API has no
  // export route, and everything a @misc entry needs is already on the article.
  const exportBibtex = () => {
    const esc = (s: string) => s.replace(/[{}]/g, "");
    const entries = filtered.map((a, i) => {
      const year = a.published_at ? new Date(a.published_at).getFullYear() : null;
      const first = a.authors?.[0]?.split(/\s+/).slice(-1)[0] ?? "anon";
      const key = `${esc(first).toLowerCase().replace(/\W/g, "")}${year ?? ""}${i}`;
      const fields = [
        ["title", esc(a.title)],
        ["author", (a.authors ?? []).map(esc).join(" and ")],
        ["year", year ? String(year) : ""],
        ["doi", a.doi ?? ""],
        ["url", a.url ?? ""],
        ["keywords", a.tags.map(t => esc(t.tag)).join(", ")],
      ].filter(([, v]) => v);
      return `@misc{${key},\n${fields.map(([k, v]) => `  ${k} = {${v}}`).join(",\n")}\n}`;
    });
    const blob = new Blob([entries.join("\n\n") + "\n"], { type: "application/x-bibtex" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "publications.bib";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Publications</h2>
          <p className="text-sm text-muted-foreground">{articles?.length ?? "…"} articles collected · Scientific Watch feed</p>
        </div>
        <button
          onClick={exportBibtex}
          disabled={filtered.length === 0}
          title={`Export the ${filtered.length} listed article(s) as BibTeX`}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          <Download size={14} /> Export BibTeX
        </button>
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
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search publications..." className="pl-8 pr-3 py-1.5 text-xs bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 w-52" />
          </div>
        </div>
      </div>

      {/* Article cards */}
      <div className="space-y-4">
        {isLoading && <div className="animate-pulse bg-card border border-border rounded-2xl h-24" />}
        {!isLoading && filtered.length === 0 && (
          <div className="bg-card border border-border rounded-2xl p-8 text-center text-sm text-muted-foreground">
            No articles found. Run the Scientific Watch agent to collect publications.
          </div>
        )}
        {filtered.map(art => (
          <div key={art.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md hover:border-primary/20 transition-all group">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-100 text-emerald-700">Collected</span>
                  <span className="text-[10px] text-muted-foreground">{formatDate(art.published_at ?? art.collected_at)}</span>
                </div>
                <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors mb-1 leading-snug">{art.title}</h3>
                {art.authors && art.authors.length > 0 && <p className="text-xs text-muted-foreground mb-2">{art.authors.join(", ")}</p>}
                <p className="text-xs font-semibold text-primary">{hostOf(art.url)}</p>
              </div>
            </div>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-border">
              <div className="flex gap-1 flex-wrap">
                {art.tags.map(t => <span key={t.tag} className="px-2 py-0.5 bg-primary/8 text-primary text-[10px] rounded-full">{t.tag}</span>)}
              </div>
              <div className="flex items-center gap-3 text-muted-foreground">
                {art.url && <a href={art.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-[10px] hover:text-primary transition-colors"><ExternalLink size={12} /> Source</a>}
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
function initialsOf(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]?.toUpperCase() ?? "").join("");
}

const formatDate = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—";

const hostOf = (url?: string | null) => {
  if (!url) return "Source";
  try { return new URL(url).hostname.replace(/^www\./, ""); } catch { return "Source"; }
};

const indicatorValue = (r: ApiResearcher, metric: string): number =>
  r.indicators.find(i => i.metric_name === metric)?.value ?? 0;

// POST /api/biblio/researchers takes a ResearcherCreate. The three external ids
// are optional; they are what the metric lookups key off (Google Scholar first,
// then Semantic Scholar / OpenAlex by name), so a profile with none of them has
// nothing to resolve against.
function NewResearcherForm({ onDone }: { onDone: () => void }) {
  const create = useCreateResearcher();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("");
  const [role, setRole] = useState("researcher");
  const [scholarId, setScholarId] = useState("");
  const [orcidId, setOrcidId] = useState("");
  const [scopusId, setScopusId] = useState("");

  return (
    <form
      className="space-y-4"
      onSubmit={e => {
        e.preventDefault();
        create.mutate(
          {
            name: name.trim(),
            email: email.trim(),
            department: department.trim(),
            role: role.trim(),
            scholar_id: scholarId.trim() || null,
            orcid_id: orcidId.trim() || null,
            scopus_id: scopusId.trim() || null,
          },
          { onSuccess: onDone },
        );
      }}
    >
      <Field label="Full name" required>
        <input className={inputCls} value={name} onChange={e => setName(e.target.value)} required placeholder="Amina Benali" />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Email" required>
          <input type="email" className={inputCls} value={email} onChange={e => setEmail(e.target.value)} required />
        </Field>
        <Field label="Department" required>
          <input className={inputCls} value={department} onChange={e => setDepartment(e.target.value)} required />
        </Field>
      </div>
      <Field label="Role" required>
        <input className={inputCls} value={role} onChange={e => setRole(e.target.value)} required placeholder="researcher / professor / phd" />
      </Field>
      <div className="pt-1">
        <p className="text-xs font-semibold text-foreground">External identifiers</p>
        <p className="text-[11px] text-muted-foreground mb-2">
          Optional, but the agent needs at least one to compute h-index, i10 and citations. Without an id, syncing returns nothing.
        </p>
        <div className="grid grid-cols-3 gap-3">
          <Field label="Scholar ID">
            <input className={inputCls} value={scholarId} onChange={e => setScholarId(e.target.value)} />
          </Field>
          <Field label="ORCID">
            <input className={inputCls} value={orcidId} onChange={e => setOrcidId(e.target.value)} />
          </Field>
          <Field label="Scopus ID">
            <input className={inputCls} value={scopusId} onChange={e => setScopusId(e.target.value)} />
          </Field>
        </div>
      </div>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-all duration-200">
          Cancel
        </button>
        <SubmitButton pending={create.isPending} label="Add researcher" />
      </div>
    </form>
  );
}

// PUT /api/biblio/researchers/{id} is a partial update; the form pre-fills
// every editable field and sends them all, keeping the mental model simple.
function EditResearcherForm({ researcher, onDone }: { researcher: ApiResearcher; onDone: () => void }) {
  const update = useUpdateResearcher();
  const [name, setName] = useState(researcher.name);
  const [email, setEmail] = useState(researcher.email);
  const [department, setDepartment] = useState(researcher.department);
  const [role, setRole] = useState(researcher.role);
  const [scholarId, setScholarId] = useState(researcher.scholar_id ?? "");
  const [orcidId, setOrcidId] = useState(researcher.orcid_id ?? "");
  const [scopusId, setScopusId] = useState(researcher.scopus_id ?? "");

  return (
    <form
      className="space-y-4"
      onSubmit={e => {
        e.preventDefault();
        update.mutate(
          {
            id: researcher.id,
            name: name.trim(),
            email: email.trim(),
            department: department.trim(),
            role: role.trim(),
            scholar_id: scholarId.trim() || null,
            orcid_id: orcidId.trim() || null,
            scopus_id: scopusId.trim() || null,
          },
          { onSuccess: onDone },
        );
      }}
    >
      <Field label="Full name" required>
        <input className={inputCls} value={name} onChange={e => setName(e.target.value)} required />
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Email" required>
          <input type="email" className={inputCls} value={email} onChange={e => setEmail(e.target.value)} required />
        </Field>
        <Field label="Department" required>
          <input className={inputCls} value={department} onChange={e => setDepartment(e.target.value)} required />
        </Field>
      </div>
      <Field label="Role" required>
        <input className={inputCls} value={role} onChange={e => setRole(e.target.value)} required />
      </Field>
      <div className="pt-1">
        <p className="text-xs font-semibold text-foreground">External identifiers</p>
        <div className="grid grid-cols-3 gap-3 mt-2">
          <Field label="Scholar ID">
            <input className={inputCls} value={scholarId} onChange={e => setScholarId(e.target.value)} />
          </Field>
          <Field label="ORCID">
            <input className={inputCls} value={orcidId} onChange={e => setOrcidId(e.target.value)} />
          </Field>
          <Field label="Scopus ID">
            <input className={inputCls} value={scopusId} onChange={e => setScopusId(e.target.value)} />
          </Field>
        </div>
      </div>
      <FormError error={update.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-all duration-200">
          Cancel
        </button>
        <SubmitButton pending={update.isPending} label="Save changes" />
      </div>
    </form>
  );
}

function ResearcherPublicationsModal({
  researcher,
  onClose,
}: {
  researcher: ApiResearcher | null;
  onClose: () => void;
}) {
  const publications = useResearcherPublications(researcher?.id ?? null);
  const syncPublications = useSyncPublications();
  const syncScholarPublications = useSyncScholarPublications();

  // The ORCID iD is what makes the import possible at all, so the absence of
  // one is stated up front rather than left to a 400 after the user clicks.
  const orcid = researcher?.orcid_id?.trim();
  const scholarId = researcher?.scholar_id?.trim();
  const rows = publications.data ?? [];
  const result = syncPublications.data;
  const scholarResult = syncScholarPublications.data;

  return (
    <Modal
      open={researcher !== null}
      onClose={onClose}
      title={researcher ? `Publications — ${researcher.name}` : "Publications"}
      subtitle="Imported from public ORCID / Google Scholar records · GET /api/biblio/researchers/{id}/publications"
    >
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="text-xs text-muted-foreground space-y-1">
            {orcid ? (
              <>
                ORCID{" "}
                <a
                  href={`https://orcid.org/${orcid}`}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary font-semibold hover:underline"
                >
                  {orcid}
                </a>
              </>
            ) : (
              <span className="text-amber-600">
                No ORCID iD on this profile — add one to import publications.
              </span>
            )}
            <br />
            {scholarId ? (
              <>Scholar profile {scholarId}</>
            ) : (
              <span className="text-amber-600">
                No Google Scholar ID on file — needed to import from Scholar.
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => researcher && syncScholarPublications.mutate(researcher.id)}
              disabled={!scholarId || syncScholarPublications.isPending}
              className="flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl border border-border bg-background hover:bg-muted transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {syncScholarPublications.isPending ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Download size={14} />
              )}
              Import from Scholar
            </button>
            <button
              onClick={() => researcher && syncPublications.mutate(researcher.id)}
              disabled={!orcid || syncPublications.isPending}
              className="flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
            >
              {syncPublications.isPending ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Download size={14} />
              )}
              Import from ORCID
            </button>
          </div>
        </div>

        {syncPublications.isError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
            <AlertCircle size={14} className="shrink-0 mt-0.5" />
            <span className="break-words">
              {(syncPublications.error as Error).message}
            </span>
          </div>
        )}

        {syncScholarPublications.isError && (
          <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
            <AlertCircle size={14} className="shrink-0 mt-0.5" />
            <span className="break-words">
              {(syncScholarPublications.error as Error).message}
            </span>
          </div>
        )}

        {result && (
          <div className="flex items-start gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700">
            <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
            <span>
              ORCID holds {result.works_found} works
              {" · "}
              {result.publications_created} new to the lab
              {" · "}
              {result.links_created} newly linked to this researcher
              {result.links_already_present > 0 &&
                ` · ${result.links_already_present} already on file`}
              {result.publications_enriched > 0 &&
                ` · ${result.publications_enriched} enriched`}
            </span>
          </div>
        )}

        {scholarResult && (
          <div className="flex items-start gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700">
            <CheckCircle2 size={14} className="shrink-0 mt-0.5" />
            <span>
              Scholar holds {scholarResult.works_found} works
              {" · "}
              {scholarResult.publications_created} new to the lab
              {" · "}
              {scholarResult.links_created} newly linked
              {scholarResult.citations_updated > 0 &&
                ` · ${scholarResult.citations_updated} citation counts refreshed`}
            </span>
          </div>
        )}

        {publications.isLoading && (
          <div className="flex items-center justify-center py-10 text-muted-foreground text-sm">
            <RefreshCw size={16} className="animate-spin mr-2" />
            Loading publications…
          </div>
        )}

        {publications.isError && (
          <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-500">
            <AlertCircle size={16} />
            {(publications.error as Error).message}
          </div>
        )}

        {!publications.isLoading && !publications.isError && rows.length === 0 && (
          <div className="bg-muted/40 border border-border rounded-xl p-6 text-center">
            <BookOpen size={22} className="mx-auto text-muted-foreground mb-2" />
            <p className="text-sm font-semibold text-foreground">
              No publications on file
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {orcid
                ? "Import from ORCID to populate this list."
                : "Add an ORCID iD to this profile, then import."}
            </p>
          </div>
        )}

        {rows.length > 0 && (
          <div className="space-y-2 max-h-[46vh] overflow-y-auto pr-1">
            <p className="text-xs text-muted-foreground">
              {rows.length} publication{rows.length === 1 ? "" : "s"}, newest first
            </p>
            {rows.map((p) => (
              <div
                key={p.id}
                className="border border-border rounded-xl p-3 hover:bg-secondary/40 transition-colors"
              >
                <p className="text-sm font-semibold text-foreground leading-snug">
                  {p.title}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {[p.journal, p.year ?? "year unknown"]
                    .filter(Boolean)
                    .join(" · ")}
                  {p.type ? ` · ${p.type}` : ""}
                </p>
                <div className="flex items-center gap-3 mt-1.5">
                  {p.doi ? (
                    <a
                      href={`https://doi.org/${p.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[11px] text-primary font-medium hover:underline inline-flex items-center gap-1"
                    >
                      {p.doi}
                      <ExternalLink size={10} />
                    </a>
                  ) : (
                    <span className="text-[11px] text-muted-foreground">no DOI</span>
                  )}
                  <span className="text-[11px] text-muted-foreground">
                    via {p.source}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
}

function ResearchersPage() {
  const { data: researchers, isLoading, error, refetch } = useResearchers();
  const sync = useSyncResearcher();
  const deleteResearcher = useDeleteResearcher();
  const [creating, setCreating] = useState(false);
  const [viewing, setViewing] = useState<ApiResearcher | null>(null);
  const [editing, setEditing] = useState<ApiResearcher | null>(null);

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Research Team</h2>
          <p className="text-sm text-muted-foreground">
            {researchers ? `${researchers.length} researchers` : "Loading team…"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-all duration-200"
          >
            <RefreshCw size={14} />Refresh
          </button>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200"
          >
            <Plus size={14} />Add researcher
          </button>
        </div>
      </div>

      <Modal open={creating} onClose={() => setCreating(false)} title="Add a researcher"
        subtitle="Stored by the bibliometric agent · POST /api/biblio/researchers">
        <NewResearcherForm onDone={() => setCreating(false)} />
      </Modal>

      <Modal open={editing !== null} onClose={() => setEditing(null)} title="Edit researcher"
        subtitle="Partial update · PUT /api/biblio/researchers/{id}">
        {editing && (
          <EditResearcherForm researcher={editing} onDone={() => setEditing(null)} />
        )}
      </Modal>

      <ResearcherPublicationsModal
        researcher={viewing}
        onClose={() => setViewing(null)}
      />

      {isLoading && (
        <div className="flex items-center justify-center py-20 text-muted-foreground text-sm">
          <RefreshCw size={16} className="animate-spin mr-2" />Loading researchers…
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-500">
          <AlertCircle size={16} />Failed to load researchers: {(error as Error).message}
        </div>
      )}

      {!isLoading && !error && researchers && researchers.length === 0 && (
        <div className="bg-card border border-border rounded-2xl p-10 text-center">
          <Users size={28} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm font-semibold text-foreground">No researchers on file</p>
          <p className="text-xs text-muted-foreground mt-1 mb-4">
            Add a profile to start tracking h-index, i10 and citation counts for the team.
          </p>
          <button onClick={() => setCreating(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200">
            <Plus size={15} />Add researcher
          </button>
        </div>
      )}

      {sync.isError && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span className="break-words">Sync failed: {(sync.error as Error).message}</span>
        </div>
      )}
      {sync.isSuccess && (
        <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-700">
          <CheckCircle2 size={14} className="shrink-0" />Sync completed.
        </div>
      )}
      {deleteResearcher.isError && (
        <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span className="break-words">{(deleteResearcher.error as Error).message}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-5">
        {researchers?.map(r => {
          const h = indicatorValue(r, "h_index");
          const i10 = indicatorValue(r, "i10_index");
          const citations = indicatorValue(r, "total_citations");
          return (
            <div key={r.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all group">
              <div className="flex items-start gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white font-bold text-lg shrink-0 shadow-md">
                  {initialsOf(r.name)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <h3 className="font-bold text-foreground font-jakarta group-hover:text-primary transition-colors">{r.name}</h3>
                  </div>
                  <p className="text-xs text-primary font-semibold mb-0.5">{r.role}</p>
                  <p className="text-xs text-muted-foreground">{r.department}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => sync.mutate(r.id)}
                    disabled={sync.isPending}
                    title="Sync Scholar metrics"
                    className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center text-muted-foreground hover:bg-primary hover:text-white transition-colors disabled:opacity-50"
                  >
                    <RefreshCw size={13} className={sync.isPending && sync.variables === r.id ? "animate-spin" : ""} />
                  </button>
                  <button
                    onClick={() => setEditing(r)}
                    title="Edit profile"
                    className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center text-muted-foreground hover:bg-primary hover:text-white transition-colors"
                  >
                    <Pencil size={13} />
                  </button>
                  <button
                    onClick={() => {
                      if (window.confirm(`Delete ${r.name}? The server refuses while publications remain linked.`))
                        deleteResearcher.mutate(r.id);
                    }}
                    disabled={deleteResearcher.isPending && deleteResearcher.variables === r.id}
                    title="Delete researcher"
                    className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center text-muted-foreground hover:bg-red-600 hover:text-white transition-colors disabled:opacity-50"
                  >
                    {deleteResearcher.isPending && deleteResearcher.variables === r.id
                      ? <Loader2 size={13} className="animate-spin" />
                      : <Trash2 size={13} />}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-border">
                <div className="text-center">
                  <div className="text-xl font-bold text-foreground font-jakarta">{h}</div>
                  <div className="text-[10px] text-muted-foreground">H-Index</div>
                </div>
                <div className="text-center border-x border-border">
                  <div className="text-xl font-bold text-foreground font-jakarta">{i10}</div>
                  <div className="text-[10px] text-muted-foreground">i10-Index</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-foreground font-jakarta">{citations.toLocaleString()}</div>
                  <div className="text-[10px] text-muted-foreground">Citations</div>
                </div>
              </div>

              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => setViewing(r)}
                  className="flex-1 py-1.5 bg-secondary text-foreground text-xs font-semibold rounded-xl hover:bg-primary hover:text-white transition-colors text-center"
                >
                  Publications
                </button>
                <a
                  href={`${API_BASE_URL}/api/biblio/researchers/${r.id}/cv/pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex-1 py-1.5 bg-primary/8 text-primary text-xs font-semibold rounded-xl hover:bg-primary hover:text-white transition-colors text-center"
                >
                  Download CV
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── AI AGENTS PAGE ──────────────────────────────────────────────────────────
function ManualEventForm({ onDone }: { onDone: () => void }) {
  const triggerEvent = useTriggerEvent();
  const [type, setType] = useState("projet.created");
  const [sourceAgent, setSourceAgent] = useState("manual");
  const [payloadText, setPayloadText] = useState("{}");
  const [payloadError, setPayloadError] = useState<string | null>(null);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const payload: unknown = JSON.parse(payloadText);
      if (!payload || Array.isArray(payload) || typeof payload !== "object") {
        setPayloadError("Payload must be a JSON object.");
        return;
      }
      setPayloadError(null);
      triggerEvent.mutate(
        { type, source_agent: sourceAgent, payload: payload as Record<string, unknown> },
        { onSuccess: onDone },
      );
    } catch {
      setPayloadError("Payload must contain valid JSON.");
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <Field label="Event type" required>
        <input className={inputCls} value={type} onChange={e => setType(e.target.value)} required placeholder="projet.created" />
      </Field>
      <Field label="Source agent" required>
        <input className={inputCls} value={sourceAgent} onChange={e => setSourceAgent(e.target.value)} required placeholder="manual" />
      </Field>
      <Field label="Payload (JSON)">
        <textarea className={`${inputCls} font-mono text-xs`} rows={6} value={payloadText} onChange={e => setPayloadText(e.target.value)} />
      </Field>
      {payloadError && <div className="text-xs text-red-600">{payloadError}</div>}
      <FormError error={triggerEvent.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-all">
          Cancel
        </button>
        <button type="submit" disabled={triggerEvent.isPending}
          className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 transition-all">
          {triggerEvent.isPending ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
          {triggerEvent.isPending ? "Routing..." : "Trigger event"}
        </button>
      </div>
    </form>
  );
}

function PlanningTaskForm({ onDone }: { onDone: () => void }) {
  const createTask = useCreatePlanningTask();
  const { data: projects } = useProjets();
  const { data: equipment } = useEquipements();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [projectId, setProjectId] = useState("");
  const [priority, setPriority] = useState<PlanningTask["priority"]>("normal");
  const [dueDate, setDueDate] = useState("");
  const [duration, setDuration] = useState("2");
  const [skills, setSkills] = useState("");
  const [equipmentIds, setEquipmentIds] = useState<string[]>([]);

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    createTask.mutate({
      title: title.trim(),
      description: description.trim() || null,
      project_id: projectId || null,
      priority,
      due_date: dueDate || null,
      duration_hours: Number(duration),
      required_skills: skills.split(",").map(skill => skill.trim()).filter(Boolean),
      required_equipment_ids: equipmentIds,
    }, { onSuccess: onDone });
  };

  return (
    <form className="space-y-3" onSubmit={submit}>
      <Field label="Task" required>
        <input className={inputCls} required value={title} onChange={event => setTitle(event.target.value)} placeholder="Calibrate lysimeter readings" />
      </Field>
      <Field label="Context">
        <textarea className={inputCls} rows={2} value={description} onChange={event => setDescription(event.target.value)} placeholder="Optional notes for the reviewer" />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Project">
          <select className={inputCls} value={projectId} onChange={event => setProjectId(event.target.value)}>
            <option value="">No project link</option>
            {(projects ?? []).map(project => <option key={project.id} value={project.id}>{project.nom}</option>)}
          </select>
        </Field>
        <Field label="Priority">
          <select className={inputCls} value={priority} onChange={event => setPriority(event.target.value as PlanningTask["priority"])}>
            <option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option>
          </select>
        </Field>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Due date"><input type="date" className={inputCls} value={dueDate} onChange={event => setDueDate(event.target.value)} /></Field>
        <Field label="Duration (hours)" required><input type="number" min="0.25" max="80" step="0.25" className={inputCls} required value={duration} onChange={event => setDuration(event.target.value)} /></Field>
      </div>
      <Field label="Required skills" hint="Comma-separated; matched exactly against MIS staff competencies.">
        <input className={inputCls} value={skills} onChange={event => setSkills(event.target.value)} placeholder="soil science, calibration" />
      </Field>
      {(equipment ?? []).length > 0 && (
        <Field label="Required equipment" hint="Only operational equipment can be proposed.">
          <div className="grid grid-cols-2 gap-2 pt-1">
            {equipment?.map(item => (
              <label key={item.id} className="flex gap-2 text-xs text-foreground items-center">
                <input type="checkbox" checked={equipmentIds.includes(item.id)} onChange={() => setEquipmentIds(current => current.includes(item.id) ? current.filter(id => id !== item.id) : [...current, item.id])} />
                <span className={item.etat === "operationnel" ? "" : "text-muted-foreground"}>{item.nom} ({item.etat})</span>
              </label>
            ))}
          </div>
        </Field>
      )}
      <FormError error={createTask.error} />
      <SubmitButton pending={createTask.isPending} label="Add planning task" />
    </form>
  );
}

function PlanningPanel() {
  const [adding, setAdding] = useState(false);
  const { data: tasks } = usePlanningTasks();
  const { data: proposals } = usePlanningProposals();
  const generate = useGeneratePlanningProposal();
  const approve = useApprovePlanningProposal();
  const latest = proposals?.[0];

  return (
    <section className="mb-6 bg-card border border-border rounded-2xl p-5">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h3 className="font-bold text-foreground font-jakarta">Reviewed Lab Planning</h3>
          <p className="text-xs text-muted-foreground mt-1 max-w-2xl">A transparent heuristic proposes assignments from MIS skills, availability and equipment state. It never changes staff work until a reviewer approves.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setAdding(true)} className="px-3 py-2 text-xs font-semibold rounded-xl border border-border hover:bg-muted"><Plus size={13} className="inline mr-1" />Add task</button>
          <button onClick={() => generate.mutate()} disabled={generate.isPending || !tasks?.some(task => task.status === "pending")} className="px-3 py-2 text-xs font-semibold rounded-xl bg-primary text-primary-foreground disabled:opacity-50"><BrainCircuit size={13} className="inline mr-1" />{generate.isPending ? "Planning…" : "Generate proposal"}</button>
        </div>
      </div>
      <FormError error={generate.error} />
      <Modal open={adding} onClose={() => setAdding(false)} title="Add a planning task" subtitle="The planner will only make a proposal; it cannot assign staff on its own.">
        <PlanningTaskForm onDone={() => setAdding(false)} />
      </Modal>

      <div className="mt-4 grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div className="rounded-xl bg-muted/50 border border-border p-3">
          <div className="text-[10px] uppercase tracking-wide font-semibold text-muted-foreground mb-2">Tasks</div>
          {!tasks?.length ? <p className="text-xs text-muted-foreground">Add a real lab task to start planning.</p> : (
            <div className="space-y-2">{tasks.slice(0, 6).map(task => <div key={task.id} className="text-xs flex justify-between gap-3"><span className="text-foreground font-medium">{task.title}</span><span className="text-muted-foreground whitespace-nowrap">{task.status}{task.assigned_personnel_id ? " · assigned" : ""}</span></div>)}</div>
          )}
        </div>
        <div className="rounded-xl bg-muted/50 border border-border p-3">
          <div className="text-[10px] uppercase tracking-wide font-semibold text-muted-foreground mb-2">Latest proposal</div>
          {!latest ? <p className="text-xs text-muted-foreground">No proposal yet. It will expose conflicts rather than silently forcing assignments.</p> : (
            <div className="space-y-2 text-xs">
              <p className="text-foreground"><span className="font-semibold">{latest.proposed_assignments.length}</span> proposed assignment(s) · <span className="font-semibold">{latest.conflicts.length}</span> conflict(s)</p>
              {latest.proposed_assignments.map(item => <p key={item.task_id} className="text-muted-foreground">{item.title} → <span className="text-foreground font-medium">{item.personnel_name}</span></p>)}
              {latest.conflicts.map(item => <p key={item.task_id} className="text-amber-700">{item.title}: {item.reasons.join(" ")}</p>)}
              {latest.status === "proposed" && <button onClick={() => approve.mutate(latest.id)} disabled={approve.isPending} className="mt-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 text-white disabled:opacity-50">{approve.isPending ? "Approving…" : "Approve conflict-free assignments"}</button>}
              {latest.status === "approved" && <p className="text-emerald-700 font-semibold">Approved by {latest.approved_by ?? "reviewer"}</p>}
            </div>
          )}
          <FormError error={approve.error} />
        </div>
      </div>
    </section>
  );
}

function AgentsPage({ setPage }: { setPage: (p: Page) => void }) {
  const [selected, setSelected] = useState<number | null>(null);
  const [triggeringEvent, setTriggeringEvent] = useState(false);
  const { data: orchStatus } = useOrchestratorStatus();
  const { data: alertes } = useAlertes();
  const { data: historique, isLoading: histLoading } = useHistorique();
  const triggerScrape = useTriggerScrape();

  const orchOnline = orchStatus?.statut === "actif";
  const activeAlerts = alertes?.length ?? 0;

  // Real per-agent telemetry, grouped from the orchestrator's event history.
  // OrchestratorAgent.handle_event appends in arrival order, so the last
  // matching entry is the most recent. This history lives in memory on the API
  // process, so it resets whenever the API restarts — hence "this session".
  const eventsByAgent: Record<string, HistoriqueEvenement[]> = {};
  for (const h of historique ?? []) {
    const bucket = eventsByAgent[h.source_agent];
    if (bucket) bucket.push(h);
    else eventsByAgent[h.source_agent] = [h];
  }

  const fmtWhen = (iso: string) => {
    const t = new Date(iso).getTime();
    if (Number.isNaN(t)) return "unknown time";
    const mins = Math.round((Date.now() - t) / 60000);
    if (mins < 1) return "just now";
    if (mins < 60) return `${mins} min ago`;
    const hrs = Math.round(mins / 60);
    if (hrs < 24) return `${hrs} h ago`;
    return `${Math.round(hrs / 24)} d ago`;
  };

  return (
    <div className="p-6 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">AI Agents Control Center</h2>
          <p className="text-sm text-muted-foreground">
            {agents.length} agents · {orchStatus ? `${orchStatus.evenements_traites} events routed · ${orchStatus.regles_actives} routing rules · ${orchStatus.alertes_actives} active alerts` : "connecting…"}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setTriggeringEvent(true)}
            className="flex items-center gap-1.5 px-3 py-2 bg-primary text-primary-foreground rounded-xl text-xs font-semibold hover:opacity-90 transition-colors"
          >
            <Send size={13} /> Trigger event
          </button>
          {activeAlerts > 0 && (
            <div className="flex items-center gap-1.5 px-3 py-2 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 font-semibold">
              <AlertCircle size={12} /> {activeAlerts} alert{activeAlerts !== 1 ? "s" : ""}
            </div>
          )}
          <div className={`flex items-center gap-2 px-3 py-2 border rounded-xl text-xs font-semibold ${orchOnline ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-muted border-border text-muted-foreground"}`}>
            <div className={`w-2 h-2 rounded-full ${orchOnline ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"}`} />
            {orchOnline ? "Orchestrator Online" : "Connecting…"}
          </div>
        </div>
      </div>

      {/* Activity below is derived from GET /api/orchestrateur/historique — the
          only per-agent telemetry the backend exposes. There is no uptime,
          confidence or success-rate metric, so none is shown. */}
      <Modal
        open={triggeringEvent}
        onClose={() => setTriggeringEvent(false)}
        title="Trigger orchestrator event"
        subtitle="Routes an event through POST /api/orchestrateur/trigger."
      >
        <ManualEventForm onDone={() => setTriggeringEvent(false)} />
      </Modal>

      <div className="mb-4 flex items-start gap-2 px-3 py-2 bg-muted/60 border border-border rounded-xl text-[11px] text-muted-foreground">
        <Info size={13} className="mt-0.5 shrink-0" />
        <span>
          Activity counts come from the orchestrator's event history, which is held in memory by the API
          process and resets on restart. Agents with no routed events show as idle rather than offline.
        </span>
      </div>

      <PlanningPanel />

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {agents.map(agent => {
          const events = eventsByAgent[agent.key] ?? [];
          const last = events.length ? events[events.length - 1] : null;
          const isSelected = selected === agent.id;
          // The orchestrator reports its own liveness via /status; for the other
          // agents the only honest signal is whether they have routed anything.
          const live = agent.key === "orchestrateur" ? orchOnline : events.length > 0;
          const badge = live
            ? { color: "bg-emerald-100 text-emerald-700", dot: "bg-emerald-500 animate-pulse", label: "Active" }
            : { color: "bg-amber-100 text-amber-700", dot: "bg-amber-500", label: "Idle" };
          return (
            <div
              key={agent.id}
              onClick={() => setSelected(isSelected ? null : agent.id)}
              className={`bg-card border rounded-2xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5
                ${isSelected ? "border-primary shadow-lg shadow-primary/10 ring-1 ring-primary/20" : "border-border"}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center">
                  <agent.icon size={20} className="text-primary" />
                </div>
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-semibold ${badge.color}`}>
                  <div className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                  {badge.label}
                </div>
              </div>

              <h4 className="text-xs font-bold text-foreground font-jakarta mb-1.5 leading-snug">{agent.name}</h4>
              <p className="text-[10px] text-muted-foreground leading-snug mb-3 line-clamp-3">{agent.desc}</p>

              <div className="mb-3 p-2 bg-muted/60 rounded-xl">
                <div className="text-[9px] uppercase tracking-wide text-muted-foreground mb-0.5">Last routed event</div>
                {last ? (
                  <>
                    <div className="text-[10px] font-semibold text-foreground font-mono truncate">{last.type_evenement}</div>
                    <div className="text-[9px] text-muted-foreground">{fmtWhen(last.timestamp)}</div>
                  </>
                ) : (
                  <div className="text-[10px] text-muted-foreground">
                    {histLoading ? "loading…" : "none this session"}
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span>{events.length.toLocaleString()} event{events.length !== 1 ? "s" : ""}</span>
                <span className="font-mono">{agent.endpoint}</span>
              </div>

              {isSelected && (
                <div className="mt-3 pt-3 border-t border-border">
                  <div className="flex gap-2">
                    <button
                      onClick={e => { e.stopPropagation(); setPage(agent.page); }}
                      className="flex-1 py-1.5 bg-primary text-white text-[10px] font-semibold rounded-lg flex items-center justify-center gap-1 hover:bg-primary/90 transition-colors"
                    >
                      <ExternalLink size={10} /> Open module
                    </button>
                    {/* Only the watch agent exposes an argument-free trigger
                        (POST /api/veille/trigger). Simulation and optimisation
                        runs need a parcel, so they are launched from their own
                        pages; the rest react to events only. */}
                    {agent.key === "veille" && (
                      <button
                        onClick={e => { e.stopPropagation(); triggerScrape.mutate(); }}
                        disabled={triggerScrape.isPending}
                        className="flex-1 py-1.5 bg-accent/15 text-accent-foreground text-[10px] font-semibold rounded-lg flex items-center justify-center gap-1 hover:bg-accent/25 transition-colors disabled:opacity-50"
                      >
                        <RefreshCw size={10} className={triggerScrape.isPending ? "animate-spin" : ""} />
                        {triggerScrape.isPending ? "Running…" : "Trigger"}
                      </button>
                    )}
                  </div>
                  <div className="mt-2 p-2 bg-muted rounded-xl">
                    {events.length ? (
                      <p className="text-[9px] text-muted-foreground font-mono leading-relaxed">
                        {events.slice(-4).reverse().map(ev => (
                          <span key={ev.id} className="block truncate">
                            [{new Date(ev.timestamp).toLocaleTimeString()}] {ev.type_evenement}
                            {ev.alertes_generees.length > 0 && ` → ${ev.alertes_generees.length} alert(s)`}
                          </span>
                        ))}
                      </p>
                    ) : (
                      <p className="text-[9px] text-muted-foreground leading-relaxed">
                        No events from <span className="font-mono">{agent.key}</span> in the orchestrator history yet.
                      </p>
                    )}
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
// Scenario presets. These are UI shorthand for real SimulationRunRequest
// parameters (agents/simulation/schemas.py) — nothing here is invented data, the
// numbers are just starting points the user can then move with the sliders.
const SIM_PRESETS: Record<string, { label: string; rainfall_factor: number; et_factor: number; temperature_delta_c: number }> = {
  baseline: { label: "Baseline", rainfall_factor: 1.0, et_factor: 1.0, temperature_delta_c: 0 },
  dry: { label: "Dry", rainfall_factor: 0.7, et_factor: 1.15, temperature_delta_c: 2 },
  hot_dry: { label: "Hot + Dry", rainfall_factor: 0.5, et_factor: 1.3, temperature_delta_c: 4 },
};

// POST /api/twin/parcels takes a ParcelCreate (agents/digitaltwin/schemas.py).
// crop_type, soil_type, field_capacity_mm and wilting_point_mm have server-side
// defaults; the form pre-fills them with those same values so what you see is
// what gets stored. The route is guarded by require_roles("administrator") — a
// non-admin session gets a 403, which FormError shows verbatim.
function NewParcelForm({
  onDone,
  initialName = "",
  projectId,
  onCreated,
}: {
  onDone: () => void;
  initialName?: string;
  projectId?: string;
  onCreated?: () => void;
}) {
  const create = useCreateParcel();
  const [name, setName] = useState(initialName);
  const [code, setCode] = useState("");
  const [areaHa, setAreaHa] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [cropType, setCropType] = useState("wheat");
  const [soilType, setSoilType] = useState("clay loam");
  const [fieldCapacity, setFieldCapacity] = useState("120");
  const [wiltingPoint, setWiltingPoint] = useState("45");

  return (
    <form
      className="space-y-4"
      onSubmit={e => {
        e.preventDefault();
        create.mutate(
          {
            project_id: projectId,
            name: name.trim(),
            code: code.trim(),
            area_ha: Number(areaHa),
            latitude: Number(latitude),
            longitude: Number(longitude),
            crop_type: cropType.trim(),
            soil_type: soilType.trim(),
            field_capacity_mm: Number(fieldCapacity),
            wilting_point_mm: Number(wiltingPoint),
          },
          { onSuccess: () => (onCreated ? onCreated() : onDone()) },
        );
      }}
    >
      <div className="grid grid-cols-2 gap-4">
        <Field label="Parcel name" required>
          <input className={inputCls} value={name} onChange={e => setName(e.target.value)} required placeholder="North field" />
        </Field>
        <Field label="Code" required>
          <input className={inputCls} value={code} onChange={e => setCode(e.target.value)} required placeholder="P-01" />
        </Field>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <Field label="Area (ha)" required>
          <input type="number" step="any" min="0" className={inputCls} value={areaHa} onChange={e => setAreaHa(e.target.value)} required />
        </Field>
        <Field label="Latitude" required>
          <input type="number" step="any" className={inputCls} value={latitude} onChange={e => setLatitude(e.target.value)} required placeholder="33.99" />
        </Field>
        <Field label="Longitude" required>
          <input type="number" step="any" className={inputCls} value={longitude} onChange={e => setLongitude(e.target.value)} required placeholder="-6.85" />
        </Field>
      </div>
      <p className="text-[11px] text-muted-foreground">
        Coordinates are what the twin uses to fetch a real weather forecast, so they need to be the parcel's actual location.
      </p>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Crop type">
          <input className={inputCls} value={cropType} onChange={e => setCropType(e.target.value)} />
        </Field>
        <Field label="Soil type">
          <input className={inputCls} value={soilType} onChange={e => setSoilType(e.target.value)} />
        </Field>
        <Field label="Field capacity (mm)">
          <input type="number" step="any" min="0" className={inputCls} value={fieldCapacity} onChange={e => setFieldCapacity(e.target.value)} />
        </Field>
        <Field label="Wilting point (mm)">
          <input type="number" step="any" min="0" className={inputCls} value={wiltingPoint} onChange={e => setWiltingPoint(e.target.value)} />
        </Field>
      </div>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground transition-all duration-200">
          Cancel
        </button>
        <SubmitButton pending={create.isPending} label="Create parcel" />
      </div>
    </form>
  );
}

function DigitalTwinsPage() {
  const [scenario, setScenario] = useState("baseline");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [creatingParcel, setCreatingParcel] = useState(false);
  // Scenario knobs, initialised from the baseline preset. Bounds match the
  // server-side Field() constraints so the API never 422s on our input.
  const [horizonDays, setHorizonDays] = useState(14);
  const [rainfallFactor, setRainfallFactor] = useState(SIM_PRESETS.baseline.rainfall_factor);
  const [etFactor, setEtFactor] = useState(SIM_PRESETS.baseline.et_factor);
  const [tempDelta, setTempDelta] = useState(SIM_PRESETS.baseline.temperature_delta_c);

  const applyPreset = (key: string) => {
    const p = SIM_PRESETS[key];
    if (!p) return;
    setScenario(key);
    setRainfallFactor(p.rainfall_factor);
    setEtFactor(p.et_factor);
    setTempDelta(p.temperature_delta_c);
  };

  const { data: parcels, isLoading: parcelsLoading } = useParcels();
  const effectiveId = selectedId ?? (parcels && parcels.length ? parcels[0].id : null);
  const { data: parcel, isLoading: parcelLoading } = useParcel(effectiveId);
  const { data: forecast } = useParcelForecast(effectiveId);
  const refreshForecast = useRefreshForecast();
  const runSim = useRunSimulation();
  const runOptimisation = useRunOptimisation();
  const { data: simRuns } = useSimulationRuns(effectiveId);
  const { data: optRuns } = useOptimisationRuns(effectiveId);

  // Real projection from the latest simulation run (runs come back newest-first).
  // Row shape is produced by agents/simulation/services/water_balance.py::_merge_series.
  const latestRun = simRuns?.[0];
  const simData = ((latestRun?.time_series ?? []) as unknown as Array<{
    day: number;
    baseline?: { soil_moisture_end_mm?: number };
    scenario?: { soil_moisture_end_mm?: number };
  }>).map(row => ({
    day: `D${row.day}`,
    baseline: row.baseline?.soil_moisture_end_mm ?? 0,
    scenario: row.scenario?.soil_moisture_end_mm ?? 0,
  }));

  // Day scrubber over the real projection (was a decorative 2024→2044 slider,
  // which misrepresented a run whose horizon is at most 16 days).
  const [dayIndex, setDayIndex] = useState(0);
  const cursor = simData.length ? simData[Math.min(dayIndex, simData.length - 1)] : null;

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
        <div className="bg-card border border-border rounded-2xl p-10 text-center">
          <MapPin size={28} className="mx-auto text-muted-foreground mb-3" />
          <h2 className="text-xl font-bold text-foreground font-jakarta">Digital Twins</h2>
          <p className="text-sm text-muted-foreground mt-2 mb-5 max-w-md mx-auto">
            No parcels yet. A parcel is the unit a twin is built on — add one with its coordinates
            and soil profile, and the agent can pull a weather forecast and run water-balance simulations against it.
          </p>
          <button onClick={() => setCreatingParcel(true)}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200">
            <Plus size={15} />Add parcel
          </button>
        </div>
        <Modal open={creatingParcel} onClose={() => setCreatingParcel(false)} title="Add a parcel"
          subtitle="Stored by the digital-twin agent · POST /api/twin/parcels (administrator only)">
          <NewParcelForm onDone={() => setCreatingParcel(false)} />
        </Modal>
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
              onClick={() => setCreatingParcel(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all duration-200"
            >
              <Plus size={13} /> Add parcel
            </button>
            <button
              onClick={() => effectiveId && refreshForecast.mutate(effectiveId)}
              disabled={refreshForecast.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-muted text-foreground hover:bg-secondary disabled:opacity-60 transition-colors"
            >
              <RefreshCw size={13} className={refreshForecast.isPending ? "animate-spin" : ""} /> Refresh forecast
            </button>
            {Object.entries(SIM_PRESETS).map(([key, p]) => (
              <button key={key} onClick={() => applyPreset(key)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors
                  ${scenario === key ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-secondary"}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Modal open={creatingParcel} onClose={() => setCreatingParcel(false)} title="Add a parcel"
        subtitle="Stored by the digital-twin agent · POST /api/twin/parcels (administrator only)">
        <NewParcelForm onDone={() => setCreatingParcel(false)} />
      </Modal>

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
          {/* Day scrubber over the latest real run */}
          <div className="p-4">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-muted-foreground">Projection Day</span>
              <span className="font-mono font-semibold text-foreground">
                {cursor ? `${cursor.day} · ${cursor.scenario.toFixed(1)} mm` : "—"}
              </span>
            </div>
            <input
              type="range" min={0} max={Math.max(0, simData.length - 1)}
              value={Math.min(dayIndex, Math.max(0, simData.length - 1))}
              onChange={e => setDayIndex(+e.target.value)}
              disabled={simData.length === 0}
              className="w-full accent-primary cursor-pointer disabled:cursor-not-allowed disabled:opacity-40"
            />
            {cursor ? (
              <div className="flex justify-between text-[9px] text-muted-foreground mt-1">
                <span>Baseline {cursor.baseline.toFixed(1)} mm</span>
                <span>Scenario {cursor.scenario.toFixed(1)} mm</span>
                <span>Δ {(cursor.scenario - cursor.baseline).toFixed(1)} mm</span>
              </div>
            ) : (
              <p className="text-[9px] text-muted-foreground mt-1">
                No simulation run for this parcel yet — run one to scrub the projection.
              </p>
            )}
          </div>
        </div>

        {/* Simulation Controls & Charts */}
        <div className="xl:col-span-1 space-y-4">
          {/* Scenario chart */}
          <div className="bg-card border border-border rounded-2xl p-4">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-1">Scenario Comparison</h3>
            <p className="text-[10px] text-muted-foreground mb-3">
              {latestRun
                ? `Soil moisture (mm) — “${latestRun.scenario_name}” over ${latestRun.horizon_days} days`
                : "Soil moisture (mm) — no simulation run yet"}
            </p>
            {simData.length === 0 ? (
              <div className="h-[160px] flex items-center justify-center text-center text-[11px] text-muted-foreground px-4">
                Run a simulation to project this parcel's water balance.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={160}>
                <ReLineChart data={simData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="day" tick={{ fontSize: 9 }} stroke="none" interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 9 }} stroke="none" />
                  <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                  <Line dataKey="baseline" name="Baseline" stroke="#0B6E4F" strokeWidth={2} dot={false} />
                  <Line dataKey="scenario" name="Scenario" stroke="#F59E0B" strokeWidth={2} dot={false} strokeDasharray="4,2" />
                </ReLineChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Controls — these are the actual request body of
              POST /api/simulation/parcels/{id}/runs, not decoration. */}
          <div className="bg-card border border-border rounded-2xl p-4">
            <h3 className="text-sm font-bold text-foreground font-jakarta mb-1">Scenario Parameters</h3>
            <p className="text-[10px] text-muted-foreground mb-3">
              Sent to the simulation agent as-is. Ranges match the server-side constraints.
            </p>
            <div className="space-y-3">
              {([
                { label: "Horizon", value: horizonDays, set: setHorizonDays, unit: "days", min: 3, max: 16, step: 1, fmt: (v: number) => String(v) },
                { label: "Rainfall factor", value: rainfallFactor, set: setRainfallFactor, unit: "×", min: 0, max: 3, step: 0.05, fmt: (v: number) => v.toFixed(2) },
                { label: "Evapotranspiration factor", value: etFactor, set: setEtFactor, unit: "×", min: 0, max: 3, step: 0.05, fmt: (v: number) => v.toFixed(2) },
                { label: "Temperature delta", value: tempDelta, set: setTempDelta, unit: "°C", min: -10, max: 15, step: 0.5, fmt: (v: number) => (v > 0 ? `+${v.toFixed(1)}` : v.toFixed(1)) },
              ]).map(c => (
                <div key={c.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{c.label}</span>
                    <span className="font-mono font-semibold text-foreground">{c.fmt(c.value)} {c.unit}</span>
                  </div>
                  <input
                    type="range" min={c.min} max={c.max} step={c.step} value={c.value}
                    onChange={e => { c.set(+e.target.value); setScenario("custom"); }}
                    className="w-full accent-primary cursor-pointer"
                  />
                </div>
              ))}
              <button
                onClick={() => {
                  if (!effectiveId) return;
                  runSim.mutate({
                    parcelId: effectiveId,
                    params: {
                      scenario_name: `${SIM_PRESETS[scenario]?.label ?? "Custom"} — ${horizonDays}d`,
                      horizon_days: horizonDays,
                      rainfall_factor: rainfallFactor,
                      et_factor: etFactor,
                      temperature_delta_c: tempDelta,
                    },
                  });
                  setDayIndex(0);
                }}
                disabled={runSim.isPending}
                className="w-full py-2 bg-gradient-to-r from-primary to-[#2D9C72] text-white text-xs font-bold rounded-xl hover:shadow-lg hover:shadow-primary/20 transition-all mt-2 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                <Play size={13} /> {runSim.isPending ? "Running…" : "Run Simulation"}
              </button>
              {runSim.isError && <p className="text-[10px] text-red-600 mt-1">{(runSim.error as Error).message}</p>}
              <button
                onClick={() => effectiveId && runOptimisation.mutate(effectiveId)}
                disabled={runOptimisation.isPending}
                className="w-full py-2 border border-primary/30 text-primary text-xs font-bold rounded-xl hover:bg-primary/10 transition-all mt-2 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                <Target size={13} /> {runOptimisation.isPending ? "Optimising…" : "Optimise Irrigation"}
              </button>
              {runOptimisation.isError && <p className="text-[10px] text-red-600 mt-1">{(runOptimisation.error as Error).message}</p>}
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

// ─── SENSOR READING INGESTION ────────────────────────────────────────────────
// The digital twin's whole water model runs off twin_sensor_readings, and until
// now nothing in the UI could write a row to it. These two forms are the intake.
//
// The field that matters is soil_moisture_mm: it is root-zone water STORAGE in
// millimetres, not volumetric percent. The API accepts any value >= 0 with no
// upper bound (SensorReadingCreate, agents/digitaltwin/schemas.py), so a "35"
// typed meaning "35 % VWC" is stored happily and quietly poisons the
// recommendation. Hence the parcel's own wilting-point → field-capacity band is
// printed next to the input, and the %→mm conversion is offered explicitly
// rather than guessed.

/** Mirrors CROP_COEFFICIENTS in agents/digitaltwin/services/irrigation.py:14.
 *  Any crop_type outside this table silently falls back to Kc = 1.0. */
const CROP_COEFFICIENTS: Record<string, number> = {
  wheat: 0.95, olive: 0.65, citrus: 0.85, vegetable: 1.05, forage: 1.10,
};

/** `YYYY-MM-DDTHH:mm` in local time — the exact format <input type="datetime-local">
 *  uses, and a naive ISO string the backend can parse without a timezone shift. */
function localNowForInput(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function AddReadingForm({ parcelId, parcel, onDone }: {
  parcelId: number; parcel?: Parcel; onDone: () => void;
}) {
  const [recordedAt, setRecordedAt] = useState(localNowForInput());
  const [moisture, setMoisture] = useState("");
  const [rainfall, setRainfall] = useState("0");
  const [et, setEt] = useState("0");
  const [temperature, setTemperature] = useState("");
  const [sensorCode, setSensorCode] = useState("");
  const [qualityFlag, setQualityFlag] = useState("ok");
  // Converter — local scratch values, never sent to the API.
  const [vwc, setVwc] = useState("");
  const [depth, setDepth] = useState("");

  const create = useCreateReading();

  const vwcNum = Number(vwc);
  const depthNum = Number(depth);
  const converted =
    vwc.trim() !== "" && depth.trim() !== "" &&
    Number.isFinite(vwcNum) && Number.isFinite(depthNum) && depthNum > 0
      ? (vwcNum / 100) * depthNum
      : null;

  const moistureNum = Number(moisture);
  const bandKnown = Boolean(parcel);
  const outOfBand =
    bandKnown && moisture.trim() !== "" && Number.isFinite(moistureNum) &&
    (moistureNum < parcel!.wilting_point_mm || moistureNum > parcel!.field_capacity_mm);
  const inFuture = recordedAt !== "" && new Date(recordedAt).getTime() > Date.now();

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    create.mutate(
      {
        parcelId,
        body: {
          // Posted verbatim: the input is already naive local time. Passing it
          // through toISOString() would append Z and shift the timestamp.
          recorded_at: recordedAt,
          soil_moisture_mm: moistureNum,
          rainfall_mm: rainfall.trim() === "" ? 0 : Number(rainfall),
          evapotranspiration_mm: et.trim() === "" ? 0 : Number(et),
          temperature_c: temperature.trim() === "" ? null : Number(temperature),
          sensor_code: sensorCode.trim(),
          quality_flag: qualityFlag,
        },
      },
      { onSuccess: onDone },
    );
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <Field label="Measured at" required
        hint="Local time, recorded exactly as entered (no timezone conversion).">
        <input type="datetime-local" required value={recordedAt}
          onChange={e => setRecordedAt(e.target.value)} className={inputCls} />
      </Field>
      {inFuture && (
        <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          This timestamp is in the future. The server accepts it, but it will become
          the "most recent" reading and will drive every recommendation until a later
          one is added.
        </p>
      )}

      <Field label="Soil moisture (mm)" required
        hint={parcel
          ? `Root-zone water storage. This parcel: wilting point ${parcel.wilting_point_mm} mm → field capacity ${parcel.field_capacity_mm} mm.`
          : "Root-zone water storage in millimetres, not volumetric percent."}>
        <input type="number" step="0.1" min="0" required value={moisture}
          onChange={e => setMoisture(e.target.value)} className={inputCls}
          placeholder={parcel ? String(parcel.wilting_point_mm) : "e.g. 60"} />
      </Field>
      {outOfBand && (
        <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          {moistureNum} mm is outside this parcel's {parcel!.wilting_point_mm}–{parcel!.field_capacity_mm} mm
          range. That is allowed — but it is also what a percentage reading typed into a
          millimetre field looks like. Use the converter below if you measured %.
        </p>
      )}

      <details className="rounded-xl border border-border bg-muted/40 px-3 py-2">
        <summary className="text-xs font-semibold text-foreground cursor-pointer">
          I measured volumetric water content (%) instead
        </summary>
        <div className="mt-3 space-y-3">
          <p className="text-[11px] text-muted-foreground">
            The parcel record has no root-zone depth column, so the depth cannot be
            filled in for you — enter the depth your probe integrates over. It is used
            for this conversion only and is not saved anywhere.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Volumetric water content (%)">
              <input type="number" step="0.1" min="0" value={vwc}
                onChange={e => setVwc(e.target.value)} className={inputCls} placeholder="e.g. 25" />
            </Field>
            <Field label="Root-zone depth (mm)">
              <input type="number" step="1" min="1" value={depth}
                onChange={e => setDepth(e.target.value)} className={inputCls} placeholder="e.g. 600" />
            </Field>
          </div>
          {converted !== null && (
            <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-card px-3 py-2">
              <span className="text-[11px] text-muted-foreground font-mono">
                {vwcNum} ÷ 100 × {depthNum} mm = <span className="font-bold text-foreground">{converted.toFixed(1)} mm</span>
              </span>
              <button type="button" onClick={() => setMoisture(converted.toFixed(1))}
                className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-border hover:bg-muted transition-colors shrink-0">
                Use this value
              </button>
            </div>
          )}
        </div>
      </details>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Rainfall (mm)" hint="Since the previous reading.">
          <input type="number" step="0.1" min="0" value={rainfall}
            onChange={e => setRainfall(e.target.value)} className={inputCls} />
        </Field>
        <Field label="Reference ET₀ (mm)" hint="The crop coefficient is applied server-side.">
          <input type="number" step="0.1" min="0" value={et}
            onChange={e => setEt(e.target.value)} className={inputCls} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Field label="Temperature (°C)" hint="Stored on the record; the water-balance model does not read it.">
          <input type="number" step="0.1" value={temperature}
            onChange={e => setTemperature(e.target.value)} className={inputCls} placeholder="optional" />
        </Field>
        <Field label="Sensor code" hint="Optional. Part of the CSV import's de-duplication key.">
          <input value={sensorCode} onChange={e => setSensorCode(e.target.value)}
            className={inputCls} placeholder="optional" />
        </Field>
      </div>

      <Field label="Quality flag" hint="Only the exact value “ok” is eligible for calibration runs.">
        <select value={qualityFlag} onChange={e => setQualityFlag(e.target.value)} className={inputCls}>
          <option value="ok">ok</option>
          <option value="suspect">suspect</option>
          <option value="calibration">calibration</option>
        </select>
      </Field>

      <FormError error={create.error} />
      <div className="flex items-center gap-2 pt-1">
        <SubmitButton pending={create.isPending} label="Save reading" />
        <button type="button" onClick={onDone}
          className="px-4 py-2 text-sm font-semibold rounded-xl border border-border text-muted-foreground hover:bg-muted transition-colors">
          Cancel
        </button>
      </div>
    </form>
  );
}

const CSV_REQUIRED_COLUMNS = ["recorded_at", "soil_moisture_mm", "rainfall_mm", "evapotranspiration_mm"];
const CSV_OPTIONAL_COLUMNS = ["temperature_c", "sensor_code", "quality_flag"];

function ImportReadingsForm({ parcelId, onDone }: { parcelId: number; onDone: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [sizeError, setSizeError] = useState<string | null>(null);
  const importer = useImportReadings();
  const result = importer.data;

  const downloadTemplate = () => {
    const header = [...CSV_REQUIRED_COLUMNS, ...CSV_OPTIONAL_COLUMNS].join(",");
    const example = [`${localNowForInput()}:00`, "62.5", "0", "4.2", "23.4", "probe-01", "ok"].join(",");
    const blob = new Blob([`${header}\n${example}\n`], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sensor-readings-template.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const pick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0] ?? null;
    // Mirrors the server's own guard so a 5 MB+ file fails here, not after upload.
    if (picked && picked.size > 5 * 1024 * 1024) {
      setSizeError("CSV import is limited to 5 MB.");
      setFile(null);
      return;
    }
    setSizeError(null);
    setFile(picked);
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    importer.mutate({ parcelId, file });
  };

  if (result) {
    const hidden = result.rejected - result.errors.length;
    return (
      <div className="space-y-3">
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Created", value: result.created, cls: "text-emerald-600 bg-emerald-50 border-emerald-200" },
            { label: "Updated", value: result.updated, cls: "text-blue-600 bg-blue-50 border-blue-200" },
            { label: "Rejected", value: result.rejected, cls: result.rejected ? "text-red-600 bg-red-50 border-red-200" : "text-muted-foreground bg-muted border-border" },
          ].map(s => (
            <div key={s.label} className={`rounded-xl border p-3 text-center ${s.cls}`}>
              <div className="text-2xl font-bold font-jakarta">{s.value}</div>
              <div className="text-[10px] font-semibold uppercase tracking-wide">{s.label}</div>
            </div>
          ))}
        </div>

        {result.errors.length > 0 && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 space-y-1 max-h-56 overflow-y-auto">
            {result.errors.map((err, i) => (
              <p key={i} className="text-[11px] text-red-700 font-mono break-words">{err}</p>
            ))}
            {hidden > 0 && (
              <p className="text-[11px] text-red-700 font-semibold pt-1">
                Showing the first {result.errors.length} of {result.rejected} rejected rows —
                {" "}{hidden} more were rejected but not itemised by the server.
              </p>
            )}
          </div>
        )}

        {result.created === 0 && result.updated === 0 && (
          <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
            Nothing was written, so the whole import was rolled back.
          </p>
        )}

        <div className="flex items-center gap-2 pt-1">
          <button type="button" onClick={onDone}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all">
            <CheckCircle2 size={15} /> Done
          </button>
          <button type="button" onClick={() => importer.reset()}
            className="px-4 py-2 text-sm font-semibold rounded-xl border border-border text-muted-foreground hover:bg-muted transition-colors">
            Import another file
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="rounded-xl border border-border bg-muted/40 p-3 space-y-2">
        <p className="text-[11px] text-muted-foreground">
          <span className="font-semibold text-foreground">Required columns:</span>{" "}
          <span className="font-mono">{CSV_REQUIRED_COLUMNS.join(", ")}</span>
        </p>
        <p className="text-[11px] text-muted-foreground">
          <span className="font-semibold text-foreground">Optional:</span>{" "}
          <span className="font-mono">{CSV_OPTIONAL_COLUMNS.join(", ")}</span>
        </p>
        <p className="text-[11px] text-muted-foreground">
          Rows are matched on <span className="font-mono">(parcel, recorded_at, sensor_code)</span>,
          so re-importing a corrected file updates those rows instead of duplicating them.
          A <span className="font-mono">data_origin</span> column is ignored — imported rows are
          always marked <span className="font-mono">field_import</span>.
        </p>
        <button type="button" onClick={downloadTemplate}
          className="flex items-center gap-2 text-xs font-semibold text-primary hover:underline">
          <Download size={13} /> Download CSV template
        </button>
      </div>

      <Field label="CSV file" required hint="UTF-8, up to 5 MB.">
        <input type="file" accept=".csv,text/csv" required onChange={pick}
          className="w-full text-xs text-muted-foreground file:mr-3 file:px-3 file:py-2 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:opacity-90" />
      </Field>

      {sizeError && <FormError error={sizeError} />}
      <FormError error={importer.error} />
      <div className="flex items-center gap-2 pt-1">
        <button type="submit" disabled={!file || importer.isPending}
          className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 transition-all">
          {importer.isPending ? <Loader2 size={15} className="animate-spin" /> : <Upload size={15} />}
          {importer.isPending ? "Importing…" : "Import readings"}
        </button>
        <button type="button" onClick={onDone}
          className="px-4 py-2 text-sm font-semibold rounded-xl border border-border text-muted-foreground hover:bg-muted transition-colors">
          Cancel
        </button>
      </div>
    </form>
  );
}

// ─── IRRIGATION EVENTS ───────────────────────────────────────────────────────
// Water actually applied, as opposed to water advised. Calibration sums these
// per calendar day into the balance it fits (services/calibration.py:75-88), so
// an unlogged irrigation makes a fitted parcel look like it loses water it never
// received. Logging is therefore a prerequisite for calibration, not a record.

const IRRIGATION_METHODS = ["drip", "sprinkler", "flood", "furrow", "pivot", "manual"];

function LogIrrigationForm({ parcelId, recommendation, onDone }: {
  parcelId: number;
  recommendation?: Recommendation | null;
  onDone: () => void;
}) {
  const [occurredAt, setOccurredAt] = useState(localNowForInput());
  const [amount, setAmount] = useState(recommendation ? String(recommendation.recommended_irrigation_mm) : "");
  const [method, setMethod] = useState(IRRIGATION_METHODS[0]);
  const [recordedBy, setRecordedBy] = useState("");
  const [notes, setNotes] = useState("");
  const record = useRecordIrrigation();

  const amountNum = Number(amount);
  const amountEntered = amount.trim() !== "" && Number.isFinite(amountNum);
  // Server bounds are gt=0 and le=500; both would come back as an opaque 422.
  const amountTooLow = amountEntered && amountNum <= 0;
  const amountTooHigh = amountEntered && amountNum > 500;
  const nameTooShort = recordedBy.trim() !== "" && recordedBy.trim().length < 2;
  const inFuture = occurredAt !== "" && new Date(occurredAt).getTime() > Date.now();
  const blocked = amountTooLow || amountTooHigh || nameTooShort;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (blocked) return;
    record.mutate(
      {
        parcelId,
        body: {
          recommendation_id: recommendation?.id,
          // Naive local time, posted verbatim — same convention as readings.
          occurred_at: occurredAt,
          amount_mm: amountNum,
          method,
          notes: notes.trim() === "" ? null : notes.trim(),
          recorded_by: recordedBy.trim(),
        },
      },
      { onSuccess: onDone },
    );
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      {recommendation && (
        <p className="text-[11px] text-primary bg-primary/5 border border-primary/20 rounded-xl px-3 py-2">
          Linked to approved recommendation #{recommendation.id}: {recommendation.recommended_irrigation_mm.toFixed(1)} mm advised.
          Record the actual applied amount below; a different amount is kept as evidence, not overwritten.
        </p>
      )}
      <Field label="Applied at" required
        hint="Local time, recorded exactly as entered (no timezone conversion).">
        <input type="datetime-local" required value={occurredAt}
          onChange={e => setOccurredAt(e.target.value)} className={inputCls} />
      </Field>
      {inFuture && (
        <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          This timestamp is in the future. The server accepts it, but an event dated
          ahead of your readings falls outside any calibration period and will not be
          counted by a run.
        </p>
      )}

      <Field label="Amount applied (mm)" required
        hint="Depth of water applied to the parcel. Server accepts 0 < value ≤ 500.">
        <input type="number" step="0.1" min="0.1" max="500" required value={amount}
          onChange={e => setAmount(e.target.value)} className={inputCls} placeholder="e.g. 25" />
      </Field>
      {amountTooLow && (
        <p className="text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2">
          The amount must be greater than 0. To correct a mistaken entry, log the real
          figure instead — there is no zero-amount event.
        </p>
      )}
      {amountTooHigh && (
        <p className="text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2">
          {amountNum} mm exceeds the server limit of 500 mm per event. Split a long
          irrigation into the separate applications that actually occurred.
        </p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <Field label="Method" hint="Stored for the record; the balance ignores it.">
          <select value={method} onChange={e => setMethod(e.target.value)} className={inputCls}>
            {IRRIGATION_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </Field>
        <Field label="Recorded by" required hint="Who applied or reported it. 2–100 characters.">
          <input required value={recordedBy} onChange={e => setRecordedBy(e.target.value)}
            className={inputCls} placeholder="e.g. A. Benali" />
        </Field>
      </div>
      {nameTooShort && (
        <p className="text-[11px] text-rose-700 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2">
          "Recorded by" needs at least 2 characters.
        </p>
      )}

      <Field label="Notes" hint="Optional — e.g. which block, or why the amount differed from the advice.">
        <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2}
          className={inputCls} placeholder="optional" />
      </Field>

      <FormError error={record.error} />
      <div className="flex items-center gap-2 pt-1">
        <SubmitButton pending={record.isPending} label="Log irrigation" />
        <button type="button" onClick={onDone}
          className="px-4 py-2 text-sm font-semibold rounded-xl border border-border text-muted-foreground hover:bg-muted transition-colors">
          Cancel
        </button>
      </div>
    </form>
  );
}

// ─── IRRIGATION RECOMMENDATION ───────────────────────────────────────────────
// POST /api/twin/parcels/{id}/recommend takes no body and reads exactly one row:
// the parcel's most recent reading by recorded_at (agents/digitaltwin/agent.py:60).
// Two consequences are stated on screen rather than left to surprise the user —
// back-dating a reading changes nothing, and `confidence` is not an uncertainty.

function RecommendationPanel({ parcelId, parcel, readingCount, latestReadingAt, irrigationEvents, onLogApplied }: {
  parcelId: number;
  parcel?: ParcelDetail;
  readingCount: number;
  latestReadingAt?: string;
  irrigationEvents?: IrrigationEvent[];
  onLogApplied: (recommendation: Recommendation) => void;
}) {
  const recommend = useRecommend();
  const approveRecommendation = useApproveRecommendation();
  const result = recommend.data;
  const history = parcel?.latest_recommendations ?? [];

  const kcKnown = parcel ? parcel.crop_type in CROP_COEFFICIENTS : false;
  const kc = parcel && kcKnown ? CROP_COEFFICIENTS[parcel.crop_type] : 1.0;

  return (
    <div className="bg-card border border-border rounded-2xl p-5 space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h3 className="font-bold text-foreground font-jakarta">Irrigation Recommendation</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Water-balance model over the root zone, after FAO-56.
            {parcel && ` Kc ${kc.toFixed(2)} for ${parcel.crop_type}.`}
          </p>
        </div>
        <button
          onClick={() => recommend.mutate(parcelId)}
          disabled={readingCount === 0 || recommend.isPending}
          title={readingCount === 0
            ? "Needs at least one sensor reading — the model has nothing to compute from."
            : "Recompute from the most recent reading"}
          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 transition-all shrink-0"
        >
          {recommend.isPending ? <Loader2 size={14} className="animate-spin" /> : <Droplet size={14} />}
          {recommend.isPending ? "Computing…" : "Generate recommendation"}
        </button>
      </div>

      {!kcKnown && parcel && (
        <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          Crop type <span className="font-mono">{parcel.crop_type}</span> is not in the
          model's coefficient table (wheat, olive, citrus, vegetable, forage), so it falls
          back to Kc = 1.0 — the crop's actual water demand is not being modelled.
        </p>
      )}

      {readingCount === 0 && (
        <p className="text-xs text-muted-foreground">
          No readings for this parcel, so no recommendation can be produced. Add one above.
        </p>
      )}

      <FormError error={recommend.error} />
      <FormError error={approveRecommendation.error} />

      {result && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Apply</div>
              <div className="text-3xl font-bold text-foreground font-jakarta mt-0.5">
                {result.recommended_irrigation_mm.toFixed(1)}<span className="text-base font-semibold ml-1">mm</span>
              </div>
              {parcel && (
                <div className="text-[10px] text-muted-foreground mt-1">
                  ≈ {(result.recommended_irrigation_mm * parcel.area_ha * 10).toFixed(0)} m³ over {parcel.area_ha} ha
                </div>
              )}
            </div>
            <div className="rounded-xl border border-border bg-muted/40 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Water balance</div>
              <div className={`text-3xl font-bold font-jakarta mt-0.5 ${
                result.water_balance_mm < 0 ? "text-red-600" : "text-emerald-600"
              }`}>
                {result.water_balance_mm > 0 ? "+" : ""}{result.water_balance_mm.toFixed(1)}
                <span className="text-base font-semibold ml-1">mm</span>
              </div>
              <div className="text-[10px] text-muted-foreground mt-1">
                {result.water_balance_mm < 0 ? "deficit against the target reserve" : "at or above the target reserve"}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/40 p-4">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Reserve score</div>
              <div className="text-3xl font-bold text-foreground font-jakarta mt-0.5">
                {result.confidence.toFixed(2)}
              </div>
              <div className="text-[10px] text-muted-foreground mt-1">range 0.65 – 0.90</div>
            </div>
          </div>

          <p className="text-xs text-foreground bg-muted/40 border border-border rounded-xl px-3 py-2">
            {result.rationale}
          </p>

          <div className="rounded-xl border border-border bg-card px-3 py-2 space-y-1.5">
            <div className="flex items-start gap-2">
              <Info size={13} className="text-muted-foreground shrink-0 mt-0.5" />
              <p className="text-[11px] text-muted-foreground">
                Computed from the single most recent reading
                {latestReadingAt ? ` (${formatDate(latestReadingAt)})` : ""}, not from a trend.
                Adding an older reading will not change this result.
              </p>
            </div>
            <p className="text-[11px] text-muted-foreground pl-[21px]">
              The reserve score is <span className="font-mono">0.65 + 0.25 × (projected reserve ÷ target reserve)</span> —
              it tracks how wet the soil is, not how reliable the advice is. A dry parcel scores
              low precisely when irrigation matters most, so read it as a wetness index.
            </p>
            {parcel && (
              <p className="text-[11px] text-muted-foreground pl-[21px]">
                Target reserve is field capacity {parcel.field_capacity_mm} mm − wilting point {parcel.wilting_point_mm} mm.
                Recommendations are capped at 35 % of field capacity per cycle.
              </p>
            )}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div>
          <div className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Previous recommendations
          </div>
          <div className="space-y-1.5">
            {[...history].slice(0, 5).map(h => (
              <div key={h.id} className="flex items-center gap-3 flex-wrap text-[11px] text-muted-foreground border-b border-border/50 last:border-0 pb-1.5 last:pb-0">
                <span className="whitespace-nowrap">{formatDate(h.generated_at)}</span>
                <span className="font-semibold text-foreground">{h.recommended_irrigation_mm.toFixed(1)} mm</span>
                <span>balance {h.water_balance_mm > 0 ? "+" : ""}{h.water_balance_mm.toFixed(1)} mm</span>
                {h.generation_mode === "automatic" && <span className="text-primary font-semibold">agent-generated</span>}
                <span>score {h.confidence.toFixed(2)}</span>
                {h.is_validated ? (() => {
                  const applications = (irrigationEvents ?? []).filter(ev => ev.recommendation_id === h.id);
                  const appliedMm = applications.reduce((total, ev) => total + ev.amount_mm, 0);
                  return applications.length > 0 ? (
                    <span className="ml-auto text-emerald-700 font-semibold">
                      applied {appliedMm.toFixed(1)} mm ({(appliedMm - h.recommended_irrigation_mm) >= 0 ? "+" : ""}{(appliedMm - h.recommended_irrigation_mm).toFixed(1)} vs plan)
                    </span>
                  ) : h.recommended_irrigation_mm > 0 ? (
                    <button
                      onClick={() => onLogApplied(h)}
                      className="ml-auto px-2 py-1 rounded-md border border-emerald-300 text-emerald-700 font-semibold hover:bg-emerald-50"
                    >
                      Log applied amount
                    </button>
                  ) : (
                    <span className="ml-auto text-emerald-700 font-semibold">approved · no irrigation advised</span>
                  );
                })() : (
                  <button
                    onClick={() => approveRecommendation.mutate({ recommendationId: h.id, parcelId })}
                    disabled={approveRecommendation.isPending}
                    className="ml-auto px-2 py-1 rounded-md border border-primary/30 text-primary font-semibold hover:bg-primary/10 disabled:opacity-50"
                  >
                    {approveRecommendation.isPending ? "Approving…" : "Approve"}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── CALIBRATION ─────────────────────────────────────────────────────────────
// Fits this parcel's own water-balance parameters instead of the generic soil
// defaults. Deliberately two-step: a researcher fits a candidate, a reviewer or
// administrator applies it (router.py:418-422), because applying overwrites the
// parcel's field capacity and every later recommendation depends on it.

/** Longest unbroken run of calendar days ending at the newest eligible reading.
 *  Mirrors the server gate (calibration.py:59-73): one `ok` reading per day with
 *  data_origin in {field, field_import}, no gaps. Computed here only so the user
 *  sees why a run would fail before spending a request on it. */
function eligibleCoverage(readings?: SensorReadingFull[]) {
  if (!readings || readings.length === 0) return null;
  const eligible = readings.filter(
    r => r.quality_flag === "ok" &&
      (r.data_origin === "field" || r.data_origin === "field_import"),
  );
  if (eligible.length === 0)
    return { days: 0, start: null, end: null, excluded: readings.length, duplicateDays: 0 };
  const dayKeys = [...new Set(eligible.map(r => r.recorded_at.slice(0, 10)))].sort();
  // More than one eligible reading on a day means only one of them is fitted.
  // calibration.py:61-64 keeps the latest by timestamp, but its comparison is a
  // strict >, so same-timestamp rows from two sensors resolve by insertion
  // order and the other series is dropped without a word.
  const duplicateDays = dayKeys.filter(
    day => eligible.filter(r => r.recorded_at.slice(0, 10) === day).length > 1,
  ).length;
  // Walk back from the newest day while each step is exactly one day earlier.
  let runStart = dayKeys.length - 1;
  for (let i = dayKeys.length - 1; i > 0; i--) {
    const gapMs = Date.parse(`${dayKeys[i]}T00:00:00Z`) - Date.parse(`${dayKeys[i - 1]}T00:00:00Z`);
    if (gapMs !== 86_400_000) break;
    runStart = i - 1;
  }
  return {
    days: dayKeys.length - runStart,
    start: dayKeys[runStart],
    end: dayKeys[dayKeys.length - 1],
    excluded: readings.length - eligible.length,
    duplicateDays,
  };
}

/** Field capacity is only identifiable when the soil actually reached the
 *  ceiling during the window. If the wettest reading stays below the fitted
 *  value, every candidate above it predicts identically and the grid search
 *  returns its lowest non-clipping option (calibration.py:105 keeps the first
 *  of a tie) — an artifact of grid order, not a measurement. Since `apply`
 *  writes exactly this number onto the parcel, the distinction matters.
 *
 *  Caveat: a profile does not store the readings it was fitted on, so this
 *  re-derives the check from whatever readings exist NOW. For an old profile
 *  whose readings were since corrected or deleted, treat the badge as a
 *  statement about today's data, not about that fit. */
function fieldCapacityIdentified(profile: CalibrationProfile, readings?: SensorReadingFull[]) {
  if (!readings) return null;
  const inWindow = readings.filter(
    r => r.recorded_at.slice(0, 10) >= profile.source_start_date &&
      r.recorded_at.slice(0, 10) <= profile.source_end_date,
  );
  if (inWindow.length === 0) return null;
  const wettest = Math.max(...inWindow.map(r => r.soil_moisture_mm));
  // Saturation clips at the ceiling, so an identified fit sits at the wettest
  // observation rather than above it.
  return { identified: wettest >= profile.parameters.field_capacity_mm - 0.01, wettest };
}

function RunCalibrationForm({ parcelId, coverage, onDone }: {
  parcelId: number;
  coverage: ReturnType<typeof eligibleCoverage>;
  onDone: () => void;
}) {
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [minObs, setMinObs] = useState("14");
  const run = useRunCalibration();

  const minObsNum = Number(minObs);
  const minObsEntered = minObs.trim() !== "" && Number.isFinite(minObsNum);
  // Server bounds are ge=7, le=365 — both would return an opaque 422.
  const minObsOutOfRange = minObsEntered && (minObsNum < 7 || minObsNum > 365);
  const rangeInverted = startDate !== "" && endDate !== "" && startDate > endDate;
  const shortOfCoverage =
    coverage !== null && minObsEntered && !minObsOutOfRange && coverage.days < minObsNum;
  const blocked = minObsOutOfRange || rangeInverted || !minObsEntered;

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (blocked) return;
    run.mutate(
      {
        parcelId,
        body: {
          start_date: startDate === "" ? null : startDate,
          end_date: endDate === "" ? null : endDate,
          min_observations: minObsNum,
        },
      },
      { onSuccess: onDone },
    );
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <p className="text-[11px] text-muted-foreground bg-muted rounded-xl px-3 py-2">
        This only produces a candidate. Nothing about the parcel changes until a
        reviewer applies it, so it is safe to run more than once.
      </p>
      <div className="grid grid-cols-2 gap-3">
        <Field label="From" hint="Optional — earliest reading day to include.">
          <input type="date" value={startDate}
            onChange={e => setStartDate(e.target.value)} className={inputCls} />
        </Field>
        <Field label="To" hint="Optional — latest reading day to include.">
          <input type="date" value={endDate}
            onChange={e => setEndDate(e.target.value)} className={inputCls} />
        </Field>
      </div>
      {rangeInverted && (
        <p className="text-[11px] text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
          The start date is after the end date, which would select no readings.
        </p>
      )}
      <Field label="Minimum observations" required
        hint="Server accepts 7–365. The window must also have no missing days.">
        <input type="number" required min={7} max={365} step={1} value={minObs}
          onChange={e => setMinObs(e.target.value)} className={inputCls} />
      </Field>
      {minObsOutOfRange && (
        <p className="text-[11px] text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
          Must be between 7 and 365.
        </p>
      )}
      {shortOfCoverage && (
        <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
          This parcel currently has {coverage!.days} unbroken day
          {coverage!.days === 1 ? "" : "s"} of eligible readings, fewer than the{" "}
          {minObsNum} you are asking for. The run will be rejected — add the
          missing days first.
        </p>
      )}
      <FormError error={run.error} />
      <SubmitButton pending={run.isPending} label="Fit candidate" />
    </form>
  );
}

function CalibrationPanel({ parcelId, parcel, readings }: {
  parcelId: number;
  parcel?: ParcelDetail;
  readings?: SensorReadingFull[];
}) {
  const { data: profiles } = useCalibrations(parcelId);
  const [runOpen, setRunOpen] = useState(false);
  const [toApply, setToApply] = useState<CalibrationProfile | null>(null);
  const [reviewedBy, setReviewedBy] = useState("");
  const apply = useApplyCalibration();

  const coverage = eligibleCoverage(readings);
  const applied = profiles?.find(p => p.status === "applied") ?? null;
  const nameTooShort = reviewedBy.trim() !== "" && reviewedBy.trim().length < 2;

  const confirmApply = () => {
    if (!toApply) return;
    apply.mutate(
      { profileId: toApply.id, reviewedBy: reviewedBy.trim(), parcelId },
      { onSuccess: () => { setToApply(null); setReviewedBy(""); } },
    );
  };

  return (
    <div className="bg-card border border-border rounded-2xl p-5">
      <div className="flex items-center justify-between gap-3 mb-1">
        <h3 className="font-bold text-foreground font-jakarta">Calibration</h3>
        <button
          onClick={() => setRunOpen(true)}
          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
        >
          <Target size={13} /> Fit candidate
        </button>
      </div>
      <p className="text-[11px] text-muted-foreground mb-4">
        Fits this parcel's own crop coefficient and field capacity against its
        measured days, instead of the generic {parcel?.soil_type ?? "soil"} defaults.
      </p>

      {/* Coverage precheck — the gate is strict, so show it before a run fails. */}
      <div className="mb-4 rounded-xl border border-border bg-muted px-3 py-2 text-[11px] text-muted-foreground">
        {!readings ? "Checking reading coverage…" : coverage === null || coverage.days === 0 ? (
          <>No calibration-eligible readings yet. A run needs readings flagged{" "}
            <span className="font-mono">ok</span> whose origin is{" "}
            <span className="font-mono">field</span> or{" "}
            <span className="font-mono">field_import</span> — manual entry and CSV
            import both qualify, seeded and demo rows deliberately do not.</>
        ) : (
          <>
            <span className="font-semibold text-foreground">{coverage.days} unbroken day
            {coverage.days === 1 ? "" : "s"}</span>{" "}
            of eligible readings ({coverage.start} → {coverage.end}).
            {coverage.days < 14 && " A run needs at least 7, and 14 is the default."}
            {coverage.excluded > 0 && ` ${coverage.excluded} reading${coverage.excluded === 1 ? "" : "s"} excluded as ineligible.`}
            {coverage.duplicateDays > 0 && (
              <span className="block mt-1 text-amber-700 font-semibold">
                {coverage.duplicateDays} day{coverage.duplicateDays === 1 ? " has" : "s have"} more
                than one eligible reading. Only one per day is fitted and the rest are dropped
                silently, so a second sensor will not improve this fit.
              </span>
            )}
          </>
        )}
      </div>

      {!profiles ? (
        <p className="text-xs text-muted-foreground">Loading calibration profiles…</p>
      ) : profiles.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          No calibration yet, so this parcel is still running on default
          parameters. Field capacity {parcel?.field_capacity_mm ?? "—"} mm comes
          from its soil type, not from its own measurements.
        </p>
      ) : (
        <div className="space-y-3">
          {profiles.map(p => {
            const fc = fieldCapacityIdentified(p, readings);
            return (
              <div key={p.id} className={`rounded-xl border p-3 ${
                p.status === "applied" ? "border-emerald-200 bg-emerald-50"
                  : p.status === "candidate" ? "border-border bg-muted"
                  : "border-border bg-card opacity-70"
              }`}>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-foreground">
                        Profile #{p.id}
                      </span>
                      <span className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold ${
                        p.status === "applied" ? "text-emerald-700 bg-emerald-100 border border-emerald-300"
                          : p.status === "candidate" ? "text-amber-700 bg-amber-50 border border-amber-200"
                          : "text-muted-foreground bg-muted border border-border"
                      }`}>{p.status}</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {p.source_start_date} → {p.source_end_date} ·{" "}
                      {p.data_quality.observation_count} days ·{" "}
                      {p.data_quality.irrigation_event_count} irrigation event
                      {p.data_quality.irrigation_event_count === 1 ? "" : "s"}
                      {p.reviewed_by && ` · applied by ${p.reviewed_by}`}
                    </div>
                  </div>
                  {p.status === "candidate" && (
                    <button
                      onClick={() => { apply.reset(); setToApply(p); }}
                      className="shrink-0 flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-border text-foreground hover:bg-card transition-colors"
                    >
                      <CheckCircle2 size={13} /> Apply
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                  <Stat label="Crop coefficient" value={p.parameters.crop_coefficient.toFixed(3)}
                    sub={`base ${p.parameters.base_crop_coefficient}`} />
                  <Stat label="Field capacity" value={`${p.parameters.field_capacity_mm.toFixed(1)} mm`}
                    sub={fc === null ? undefined : fc.identified ? "constrained by data" : "not identified"} />
                  <Stat label="RMSE" value={`${p.metrics.rmse_mm.toFixed(2)} mm`}
                    sub={`${p.metrics.validation_observations} days checked`} />
                  <Stat label="Bias" value={`${p.metrics.bias_mm > 0 ? "+" : ""}${p.metrics.bias_mm.toFixed(2)} mm`}
                    sub={p.metrics.bias_mm > 0 ? "predicts wetter" : p.metrics.bias_mm < 0 ? "predicts drier" : "centred"} />
                </div>
                {fc && !fc.identified && (
                  <p className="mt-2 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
                    Field capacity is not constrained by these readings — the soil
                    never reached the ceiling (wettest was {fc.wettest.toFixed(1)} mm).
                    Any value above that fits equally well, so{" "}
                    {p.parameters.field_capacity_mm.toFixed(1)} mm is the lowest the
                    search could pick, not a measurement. The crop coefficient
                    above is unaffected.
                  </p>
                )}
                {p.data_quality.irrigation_event_count === 0 && (
                  <p className="mt-2 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
                    No irrigation was logged in this window. If any water was
                    applied, the fit has absorbed it into the crop coefficient.
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {applied && (
        <p className="mt-3 text-[11px] text-muted-foreground">
          Applied profiles set the parcel's field capacity. The fitted crop
          coefficient is read by the simulation and optimisation agents, but the
          recommendation still uses the standard value for{" "}
          {parcel?.crop_type ?? "this crop"} — that path does not consult
          calibration.
        </p>
      )}

      <Modal open={runOpen} onClose={() => setRunOpen(false)}
        title="Fit a calibration candidate"
        subtitle={`POST /api/twin/parcels/${parcelId}/calibrations/run · requires researcher, reviewer or administrator`}>
        <RunCalibrationForm parcelId={parcelId} coverage={coverage}
          onDone={() => setRunOpen(false)} />
      </Modal>

      <Modal open={Boolean(toApply)}
        onClose={() => !apply.isPending && setToApply(null)}
        title={`Apply calibration #${toApply?.id ?? ""}?`}
        subtitle={`POST /api/twin/calibrations/${toApply?.id ?? ""}/apply · requires reviewer or administrator`}>
        {toApply && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground">
              This sets the parcel's field capacity to{" "}
              <span className="font-semibold text-foreground">
                {toApply.parameters.field_capacity_mm.toFixed(1)} mm
              </span>{" "}
              (currently {parcel?.field_capacity_mm ?? "—"} mm) and supersedes any
              profile already applied. Recommendations generated afterwards use
              the new value; ones already stored keep the old one.
            </p>
            {(() => {
              const fc = fieldCapacityIdentified(toApply, readings);
              return fc && !fc.identified ? (
                <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
                  Note this window never saturated the soil, so the field capacity
                  you are about to write is the search's lowest non-clipping
                  option rather than a fitted measurement.
                </p>
              ) : null;
            })()}
            <Field label="Reviewed by" required
              hint="Recorded on the profile as the person accountable. 2–100 characters.">
              <input value={reviewedBy} onChange={e => setReviewedBy(e.target.value)}
                placeholder="Full name" className={inputCls} />
            </Field>
            {nameTooShort && (
              <p className="text-[11px] text-red-700 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                At least 2 characters.
              </p>
            )}
            <FormError error={apply.error} />
            <div className="flex gap-2">
              <button type="button" onClick={() => setToApply(null)}
                disabled={apply.isPending}
                className="flex-1 px-4 py-2 text-sm font-semibold rounded-xl border border-border text-foreground hover:bg-muted disabled:opacity-50 transition-colors">
                Cancel
              </button>
              <button type="button" onClick={confirmApply}
                disabled={apply.isPending || reviewedBy.trim().length < 2}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-opacity">
                {apply.isPending ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle2 size={15} />}
                {apply.isPending ? "Applying…" : "Apply calibration"}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// ─── IOT PAGE ────────────────────────────────────────────────────────────────
function IoTPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [readingToDelete, setReadingToDelete] = useState<SensorReadingFull | null>(null);
  const [deleteResult, setDeleteResult] = useState<SensorReadingDeleteResult | null>(null);
  const [irrigationOpen, setIrrigationOpen] = useState(false);
  const [recommendationToLog, setRecommendationToLog] = useState<Recommendation | null>(null);
  const deleteReading = useDeleteReading();
  const { data: parcels, isLoading: parcelsLoading } = useParcels();
  const effectiveId = selectedId ?? (parcels && parcels.length ? parcels[0].id : null);
  const { data: parcel } = useParcel(effectiveId);
  // GET /readings rather than ParcelDetail.latest_readings: the embedded list is
  // capped at 30 rows server-side, which silently truncated every average and
  // chart on this page. useParcel is still the source for parcel metadata and
  // the recommendation history.
  const READINGS_LIMIT = 90;
  const { data: rawReadings, isLoading: readingsLoading } = useReadings(effectiveId, READINGS_LIMIT);
  const { data: irrigationEvents } = useIrrigationEvents(effectiveId);

  useEffect(() => {
    const targetId = Number(window.sessionStorage.getItem("lrste.iot.parcelId"));
    if (targetId && parcels?.some(parcelOption => parcelOption.id === targetId)) {
      setSelectedId(targetId);
      window.sessionStorage.removeItem("lrste.iot.parcelId");
    }
  }, [parcels]);

  // Readings come back newest-first; charts read left-to-right chronologically.
  const readings = [...(rawReadings ?? [])].sort(
    (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
  );

  const avg = (pick: (r: (typeof readings)[number]) => number | null | undefined) => {
    const vals = readings.map(pick).filter((v): v is number => typeof v === "number");
    return vals.length ? vals.reduce((n, v) => n + v, 0) / vals.length : null;
  };
  const fmt = (v: number | null, unit: string, digits = 1) =>
    v === null ? "—" : `${v.toFixed(digits)}${unit}`;

  const flagged = readings.filter(r => r.quality_flag !== "ok");
  const latestReading = readings[readings.length - 1];
  const readingWindow = `over ${readings.length} reading${readings.length === 1 ? "" : "s"}`;

  const series = readings.map(r => ({
    t: new Date(r.recorded_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit" }),
    temp: r.temperature_c ?? null,
    moisture: r.soil_moisture_mm,
    rainfall: r.rainfall_mm,
    et: r.evapotranspiration_mm,
  }));

  const metrics = [
    { label: "Avg Temperature", value: fmt(avg(r => r.temperature_c), "°C"), change: readingWindow, icon: Thermometer, color: "text-orange-500", bg: "bg-orange-50" },
    { label: "Avg Soil Moisture", value: fmt(avg(r => r.soil_moisture_mm), " mm"), change: parcel ? `FC ${parcel.field_capacity_mm} mm` : "—", icon: Droplets, color: "text-blue-500", bg: "bg-blue-50" },
    { label: "Avg Rainfall", value: fmt(avg(r => r.rainfall_mm), " mm"), change: readingWindow, icon: Wind, color: "text-cyan-500", bg: "bg-cyan-50" },
    { label: "Avg ET₀", value: fmt(avg(r => r.evapotranspiration_mm), " mm"), change: "reference ET", icon: Gauge, color: "text-purple-500", bg: "bg-purple-50" },
    { label: "Parcels Monitored", value: String(parcels?.length ?? 0), change: latestReading ? `last ${formatDate(latestReading.recorded_at)}` : "no data", icon: Radio, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Flagged Readings", value: String(flagged.length), change: flagged.length ? "needs review" : "all ok", icon: AlertCircle, color: flagged.length ? "text-red-500" : "text-emerald-600", bg: flagged.length ? "bg-red-50" : "bg-emerald-50" },
  ];

  if (parcelsLoading) {
    return (
      <div className="p-6 h-full overflow-y-auto scrollbar-hide">
        <div className="animate-pulse bg-card border border-border rounded-2xl h-40" />
      </div>
    );
  }

  if (!parcels || parcels.length === 0) {
    return (
      <div className="p-6 h-full overflow-y-auto scrollbar-hide">
        <div className="bg-card border border-border rounded-2xl p-8 text-center">
          <h2 className="text-xl font-bold text-foreground font-jakarta">IoT Monitoring</h2>
          <p className="text-sm text-muted-foreground mt-2">
            No parcels configured, so there are no sensor streams. Add a parcel on the
            Digital Twins page first — readings are always attached to one.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">IoT Monitoring Dashboard</h2>
          <p className="text-sm text-muted-foreground">
            {parcel ? `${parcel.name} · ${readings.length} reading${readings.length === 1 ? "" : "s"} on record` : "Loading sensor stream…"}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <select
            value={effectiveId ?? ""}
            onChange={e => setSelectedId(Number(e.target.value))}
            className="text-xs bg-muted border border-border rounded-xl px-3 py-1.5 text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            {parcels.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
          <button onClick={() => setAddOpen(true)} disabled={!effectiveId}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 transition-all">
            <Plus size={13} /> Add reading
          </button>
          <button onClick={() => setImportOpen(true)} disabled={!effectiveId}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-border text-foreground hover:bg-muted disabled:opacity-50 transition-colors">
            <Upload size={13} /> Import CSV
          </button>
          <button onClick={() => { setRecommendationToLog(null); setIrrigationOpen(true); }} disabled={!effectiveId}
            className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-border text-foreground hover:bg-muted disabled:opacity-50 transition-colors">
            <Droplet size={13} /> Log irrigation
          </button>
          <div className={`flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-xl border ${
            readings.length ? "text-emerald-700 bg-emerald-50 border-emerald-200" : "text-muted-foreground bg-muted border-border"
          }`}>
            <div className={`w-2 h-2 rounded-full ${readings.length ? "bg-emerald-500 animate-pulse" : "bg-muted-foreground"}`} />
            {readings.length ? "Stream Active" : "No Data"}
          </div>
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

      {effectiveId && (
        <RecommendationPanel
          parcelId={effectiveId}
          parcel={parcel}
          readingCount={readings.length}
          latestReadingAt={latestReading?.recorded_at}
          irrigationEvents={irrigationEvents}
          onLogApplied={recommendation => { setRecommendationToLog(recommendation); setIrrigationOpen(true); }}
        />
      )}

      {/* Time series charts */}
      {readingsLoading ? (
        <div className="animate-pulse bg-card border border-border rounded-2xl h-56" />
      ) : series.length === 0 ? (
        <div className="bg-card border border-border rounded-2xl p-8 text-center">
          <p className="text-sm text-muted-foreground">
            No sensor readings recorded for this parcel yet. Nothing on this page — and no
            irrigation recommendation — can be computed until at least one exists.
          </p>
          <div className="flex items-center justify-center gap-2 mt-4">
            <button onClick={() => setAddOpen(true)}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 hover:opacity-90 transition-all">
              <Plus size={13} /> Add the first reading
            </button>
            <button onClick={() => setImportOpen(true)}
              className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl border border-border text-foreground hover:bg-muted transition-colors">
              <Upload size={13} /> Import a CSV
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <div className="bg-card border border-border rounded-2xl p-5">
            <h3 className="font-bold text-foreground font-jakarta mb-4">Temperature & Soil Moisture</h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="t" tick={{ fontSize: 9 }} stroke="none" interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 9 }} stroke="none" />
                <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                <Area type="monotone" dataKey="temp" name="Temp (°C)" stroke="#F97316" fill="rgba(249,115,22,0.1)" strokeWidth={2} connectNulls />
                <Area type="monotone" dataKey="moisture" name="Soil moisture (mm)" stroke="#3B82F6" fill="rgba(59,130,246,0.08)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-card border border-border rounded-2xl p-5">
            <h3 className="font-bold text-foreground font-jakarta mb-4">Rainfall vs Evapotranspiration</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={series}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="t" tick={{ fontSize: 9 }} stroke="none" interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 9 }} stroke="none" />
                <Tooltip contentStyle={{ borderRadius: 10, fontSize: 11 }} />
                <Bar dataKey="rainfall" name="Rainfall (mm)" fill="#0B6E4F" radius={[4, 4, 0, 0]} />
                <Bar dataKey="et" name="ET₀ (mm)" fill="#F59E0B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recorded readings */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <div className="flex items-center justify-between gap-3 mb-4">
          <h3 className="font-bold text-foreground font-jakarta">Recorded Readings</h3>
          <span className="text-[10px] text-muted-foreground">
            newest first · server returns at most {READINGS_LIMIT}
          </span>
        </div>
        {deleteResult && (
          <div className="mb-4 flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">
            <CheckCircle2 size={14} className="mt-0.5 shrink-0" />
            <div className="flex-1">
              <div>
                Reading #{deleteResult.deleted_id} ({formatDate(deleteResult.recorded_at)}) deleted.{" "}
                {deleteResult.remaining} reading{deleteResult.remaining === 1 ? "" : "s"} left on this parcel.
              </div>
              {deleteResult.was_latest && deleteResult.remaining > 0 && (
                <div className="mt-1 font-semibold">
                  It was the newest row, so re-run the recommendation above to refresh the irrigation figure.
                </div>
              )}
              {deleteResult.remaining === 0 && (
                <div className="mt-1 font-semibold">
                  No readings remain — the recommendation cannot be computed until you add one.
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={() => setDeleteResult(null)}
              className="text-emerald-700 hover:text-emerald-900 font-semibold"
            >
              Dismiss
            </button>
          </div>
        )}
        {readings.length === 0 ? (
          <p className="text-xs text-muted-foreground">Nothing recorded for this parcel yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="pb-2 pr-3 font-semibold">Measured at</th>
                  <th className="pb-2 pr-3 font-semibold text-right">Moisture (mm)</th>
                  <th className="pb-2 pr-3 font-semibold text-right">Rain (mm)</th>
                  <th className="pb-2 pr-3 font-semibold text-right">ET₀ (mm)</th>
                  <th className="pb-2 pr-3 font-semibold text-right">Temp (°C)</th>
                  <th className="pb-2 pr-3 font-semibold">Sensor</th>
                  <th className="pb-2 pr-3 font-semibold">Quality</th>
                  <th className="pb-2 pr-3 font-semibold">Origin</th>
                  <th className="pb-2 font-semibold text-right">Correct</th>
                </tr>
              </thead>
              <tbody>
                {[...readings].reverse().map(r => (
                  <tr key={r.id} className="border-b border-border/50 last:border-0">
                    <td className="py-2 pr-3 text-foreground whitespace-nowrap">{formatDate(r.recorded_at)}</td>
                    <td className="py-2 pr-3 text-right font-semibold text-foreground">{r.soil_moisture_mm}</td>
                    <td className="py-2 pr-3 text-right text-muted-foreground">{r.rainfall_mm}</td>
                    <td className="py-2 pr-3 text-right text-muted-foreground">{r.evapotranspiration_mm}</td>
                    <td className="py-2 pr-3 text-right text-muted-foreground">
                      {typeof r.temperature_c === "number" ? r.temperature_c : "—"}
                    </td>
                    <td className="py-2 pr-3 text-muted-foreground font-mono">{r.sensor_code || "—"}</td>
                    <td className="py-2 pr-3">
                      <span className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold ${
                        r.quality_flag === "ok"
                          ? "text-emerald-700 bg-emerald-50 border border-emerald-200"
                          : "text-amber-700 bg-amber-50 border border-amber-200"
                      }`}>{r.quality_flag}</span>
                    </td>
                    <td className="py-2 pr-3 text-muted-foreground font-mono text-[10px]">{r.data_origin}</td>
                    <td className="py-2 text-right">
                      <button
                        type="button"
                        onClick={() => { setDeleteResult(null); deleteReading.reset(); setReadingToDelete(r); }}
                        title={`Delete reading #${r.id} — the only way to retract a mistyped measurement`}
                        aria-label={`Delete reading recorded at ${formatDate(r.recorded_at)}`}
                        className="p-1.5 rounded-lg text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <Trash2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Irrigation history — what was actually applied, as opposed to advised.
          Calibration buckets these per day into the balance it fits, so this list
          is the audit trail that run leans on. */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <div className="flex items-center justify-between gap-3 mb-4">
          <h3 className="font-bold text-foreground font-jakarta">Irrigation History</h3>
          <span className="text-[10px] text-muted-foreground">
            what was applied, not advised · {irrigationEvents?.length ?? 0} event{(irrigationEvents?.length ?? 0) === 1 ? "" : "s"}
          </span>
        </div>
        <p className="text-[11px] text-muted-foreground mb-3">
          These are the applications the calibration run sums into the water balance
          it fits. An irrigation you never log makes a parcel look like it loses
          water it actually received.
        </p>
        {!irrigationEvents ? (
          <p className="text-xs text-muted-foreground">Loading irrigation events…</p>
        ) : irrigationEvents.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            No irrigation logged yet. Log what you apply — it is the other half of
            the water story this page tracks.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-muted-foreground border-b border-border">
                  <th className="pb-2 pr-3 font-semibold">Applied at</th>
                  <th className="pb-2 pr-3 font-semibold text-right">Amount (mm)</th>
                  <th className="pb-2 pr-3 font-semibold">Method</th>
                  <th className="pb-2 pr-3 font-semibold">Recorded by</th>
                  <th className="pb-2 font-semibold">Notes</th>
                </tr>
              </thead>
              <tbody>
                {irrigationEvents.map(ev => (
                  <tr key={ev.id} className="border-b border-border/50 last:border-0">
                    <td className="py-2 pr-3 text-foreground whitespace-nowrap">{formatDate(ev.occurred_at)}</td>
                    <td className="py-2 pr-3 text-right font-semibold text-foreground">{ev.amount_mm} mm</td>
                    <td className="py-2 pr-3 text-muted-foreground">{ev.method || "—"}</td>
                    <td className="py-2 pr-3 text-muted-foreground">{ev.recorded_by}</td>
                    <td className="py-2 text-muted-foreground max-w-64 truncate">{ev.notes || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {effectiveId && (
        <CalibrationPanel parcelId={effectiveId} parcel={parcel} readings={rawReadings} />
      )}

      {/* Data-quality flags */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <h3 className="font-bold text-foreground font-jakarta mb-4">Data Quality Flags</h3>
        {readings.length === 0 ? (
          <p className="text-xs text-muted-foreground">No readings to assess yet.</p>
        ) : flagged.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            All {readings.length} reading{readings.length === 1 ? "" : "s"} for this parcel are flagged <span className="font-semibold text-emerald-600">ok</span>.
          </p>
        ) : (
          <div className="space-y-3">
            {flagged.map(r => (
              <div key={r.id} className="flex items-start gap-3 p-3 rounded-xl border bg-amber-50 border-amber-200">
                <AlertCircle size={16} className="text-amber-500 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-bold text-foreground capitalize">{r.quality_flag.replace(/_/g, " ")}</span>
                    <span className="text-[10px] text-muted-foreground">Reading #{r.id} · {r.data_origin}</span>
                    <span className="text-[10px] text-muted-foreground ml-auto">{formatDate(r.recorded_at)}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Soil moisture {r.soil_moisture_mm} mm · rainfall {r.rainfall_mm} mm · ET₀ {r.evapotranspiration_mm} mm
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={addOpen} onClose={() => setAddOpen(false)}
        title="Record a sensor reading"
        subtitle={`POST /api/twin/parcels/${effectiveId}/readings · requires researcher, reviewer or administrator`}>
        {effectiveId && (
          <AddReadingForm parcelId={effectiveId} parcel={parcel} onDone={() => setAddOpen(false)} />
        )}
      </Modal>

      <Modal open={importOpen} onClose={() => setImportOpen(false)}
        title="Import readings from CSV"
        subtitle={`POST /api/twin/parcels/${effectiveId}/readings/import · requires researcher, reviewer or administrator`}>
        {effectiveId && (
          <ImportReadingsForm parcelId={effectiveId} onDone={() => setImportOpen(false)} />
        )}
      </Modal>

      <Modal open={irrigationOpen} onClose={() => setIrrigationOpen(false)}
        title="Log an irrigation event"
        subtitle={`POST /api/twin/parcels/${effectiveId}/irrigation-events · requires researcher, reviewer or administrator`}>
        {effectiveId && (
          <LogIrrigationForm
            key={recommendationToLog?.id ?? "manual"}
            parcelId={effectiveId}
            recommendation={recommendationToLog}
            onDone={() => { setIrrigationOpen(false); setRecommendationToLog(null); }}
          />
        )}
      </Modal>

      {/* Reading deletion. The recommendation model reads exactly one row — the
          newest by recorded_at — so a mistyped measurement keeps driving the
          irrigation figure until it is removed or superseded. Deleting does NOT
          revise recommendations already stored (there is no FK from a
          recommendation to the reading it used), hence the re-run prompt. */}
      <Modal
        open={readingToDelete !== null}
        onClose={() => !deleteReading.isPending && setReadingToDelete(null)}
        title="Delete sensor reading"
        subtitle={`DELETE /api/twin/parcels/${effectiveId}/readings/${readingToDelete?.id} · requires researcher, reviewer or administrator`}
      >
        {readingToDelete && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Permanently remove the reading measured{" "}
              <span className="font-semibold text-foreground">{formatDate(readingToDelete.recorded_at)}</span>? This cannot be undone.
            </p>
            <div className="rounded-xl border border-border bg-muted/40 p-3 text-xs text-muted-foreground space-y-0.5">
              <div>Soil moisture <span className="font-semibold text-foreground">{readingToDelete.soil_moisture_mm} mm</span> · rainfall {readingToDelete.rainfall_mm} mm · ET₀ {readingToDelete.evapotranspiration_mm} mm</div>
              <div>Sensor <span className="font-mono">{readingToDelete.sensor_code || "—"}</span> · quality <span className="font-mono">{readingToDelete.quality_flag}</span> · origin <span className="font-mono">{readingToDelete.data_origin}</span></div>
            </div>
            {latestReading?.id === readingToDelete.id && (
              <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
                <AlertCircle size={14} className="mt-0.5 shrink-0" />
                <span>
                  This is the newest reading — the only one the recommendation uses. Deleting it
                  makes the next recommendation fall back to the previous measurement, and any
                  recommendation already generated keeps the old figure until you re-run it.
                </span>
              </div>
            )}
            <FormError error={deleteReading.error} />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setReadingToDelete(null)}
                disabled={deleteReading.isPending}
                className="px-4 py-2 text-sm font-medium rounded-xl text-muted-foreground hover:bg-secondary hover:text-foreground disabled:opacity-50 transition-all"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => effectiveId && deleteReading.mutate(
                  { parcelId: effectiveId, readingId: readingToDelete.id },
                  { onSuccess: (res) => { setDeleteResult(res); setReadingToDelete(null); } },
                )}
                disabled={deleteReading.isPending}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-xl bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {deleteReading.isPending ? <Loader2 size={15} className="animate-spin" /> : <Trash2 size={15} />}
                {deleteReading.isPending ? "Deleting…" : "Delete reading"}
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

// ─── SCIENTIFIC WATCH PAGE ───────────────────────────────────────────────────
// POST /api/veille/sources (SourceCreate: name, type, url, config?, active).
// The collection loop in agents/veille/agent.py only handles source.type in
// ("rss", "atom") — any other type is stored but silently skipped on a run, so
// the select offers just those two rather than inventing options that no-op.
function AddSourceForm({ onDone }: { onDone: () => void }) {
  const create = useCreateSource();
  const [name, setName] = useState("");
  const [type, setType] = useState<"rss" | "atom" | "arxiv" | "pubmed">("rss");
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(true);

  // arxiv/pubmed are query-driven (the agent calls their search APIs), while
  // rss/atom point at a concrete feed URL. The form swaps the input accordingly.
  const isApiType = type === "arxiv" || type === "pubmed";

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isApiType) {
      // config carries the query; url is a synthetic provenance marker.
      const configKey = type === "arxiv" ? "search_query" : "term";
      create.mutate(
        {
          name: name.trim(),
          type,
          url: `${type}://${query.trim()}`,
          config: { [configKey]: query.trim(), max_results: 25 },
          active,
        },
        { onSuccess: onDone },
      );
    } else {
      create.mutate(
        { name: name.trim(), type, url: url.trim(), active },
        { onSuccess: onDone },
      );
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <Field label="Source name" required>
        <input required value={name} onChange={e => setName(e.target.value)}
          placeholder="ArXiv — Agricultural AI" className={inputCls} />
      </Field>
      <Field label="Source type" required>
        <select value={type} onChange={e => {
          const t = e.target.value as typeof type;
          setType(t);
          setUrl("");
          setQuery("");
        }} className={inputCls}>
          <option value="rss">RSS feed</option>
          <option value="atom">Atom feed</option>
          <option value="arxiv">ArXiv (search query)</option>
          <option value="pubmed">PubMed (search query)</option>
        </select>
      </Field>

      {isApiType ? (
        <Field
          label={type === "arxiv" ? "ArXiv search query" : "PubMed search term"}
          hint={type === "arxiv"
            ? "ArXiv query syntax, e.g. 'all:water stress irrigation' or 'cat:cs.AI AND all:groundwater'."
            : "PubMed query syntax, e.g. 'drinking water quality' or 'wastewater treatment[Title/Abstract]'."}
          required
        >
          <input required value={query} onChange={e => setQuery(e.target.value)}
            placeholder={type === "arxiv" ? "all:water stress irrigation" : "drinking water quality"}
            className={inputCls} />
        </Field>
      ) : (
        <Field label="Feed URL" hint="The RSS/Atom endpoint the agent will fetch on each run." required>
          <input required type="url" value={url} onChange={e => setUrl(e.target.value)}
            placeholder="http://export.arxiv.org/rss/cs.AI" className={inputCls} />
        </Field>
      )}

      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)}
          className="rounded border-border" />
        <span className="text-xs text-foreground">
          Active — only active sources are picked up by a collection run
        </span>
      </label>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone}
          className="px-4 py-2 text-sm font-semibold rounded-xl text-muted-foreground hover:bg-muted transition-colors">
          Cancel
        </button>
        <SubmitButton pending={create.isPending} label="Add source" />
      </div>
    </form>
  );
}

function WatchPage() {
  const { data: articles, isLoading, error, refetch } = useArticles();
  const { data: sources } = useSources();
  const trigger = useTriggerScrape();
  const deleteSource = useDeleteSource();
  const [addOpen, setAddOpen] = useState(false);
  const activeSources = (sources ?? []).filter(s => s.active);

  const relevanceOf = (a: Article) => {
    const c = a.tags[0]?.confidence;
    return typeof c === "number" ? Math.round(c * 100) : a.tags.length * 20 + 40;
  };
  const summaryOf = (a: Article) => a.summaries[0]?.summary_text || a.abstract || "No summary available yet.";

  // Tag frequencies across the collected corpus.
  const watchTagCounts: Record<string, number> = {};
  for (const a of articles ?? []) {
    for (const t of a.tags) {
      const key = t.tag.trim();
      if (key) watchTagCounts[key] = (watchTagCounts[key] ?? 0) + 1;
    }
  }
  const topTags = Object.entries(watchTagCounts).sort((a, b) => b[1] - a[1]).slice(0, 8);

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
            onClick={() => setAddOpen(true)}
            className="flex items-center gap-1.5 text-xs font-semibold border border-border text-foreground px-3 py-1.5 rounded-xl hover:bg-muted transition-colors"
          >
            <Plus size={13} /> Add source
          </button>
          <button
            onClick={() => trigger.mutate()}
            disabled={trigger.isPending || activeSources.length === 0}
            title={activeSources.length === 0 ? "Add an active source first — a run iterates configured sources." : undefined}
            className="flex items-center gap-1.5 text-xs font-semibold bg-primary text-white px-3 py-1.5 rounded-xl hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw size={13} className={trigger.isPending ? "animate-spin" : ""} />
            {trigger.isPending ? "Collecting…" : "Trigger scrape"}
          </button>
          <div className="flex items-center gap-2 text-xs text-primary font-semibold bg-primary/8 px-3 py-1.5 rounded-xl">
            <Eye size={14} /> Live feed
          </div>
        </div>
      </div>

      {/* Sources — a collection run takes no search terms; it iterates these
          rows, so an empty list is the reason "Trigger scrape" appears to do
          nothing. Surface both the list and the run outcome. */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-sm font-bold text-foreground">Configured sources</p>
            <p className="text-xs text-muted-foreground">
              A scrape has no search box — it fetches every active source below.
            </p>
          </div>
          <span className="text-xs font-semibold text-muted-foreground">
            {activeSources.length} active / {sources?.length ?? 0}
          </span>
        </div>

        {sources && sources.length === 0 ? (
          <div className="flex items-start gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
            <AlertCircle size={14} className="shrink-0 mt-0.5" />
            <span>
              No sources configured, so a scrape has nothing to fetch and returns immediately.
              Add a feed to give the agent something to collect.
            </span>
          </div>
        ) : (
          <div className="space-y-2">
            {sources?.map(s => (
              <div key={s.id} className="flex items-center justify-between gap-3 bg-muted/50 rounded-xl px-3 py-2">
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-foreground truncate">{s.name}</p>
                  <p className="text-[11px] text-muted-foreground truncate">{s.url}</p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-[10px] uppercase font-bold text-muted-foreground bg-background px-2 py-0.5 rounded-full">{s.type}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${s.active ? "text-primary bg-primary/10" : "text-muted-foreground bg-background"}`}>
                    {s.active ? "active" : "paused"}
                  </span>
                  <span className="text-[10px] text-muted-foreground w-20 text-right">
                    {s.last_scraped ? formatDate(s.last_scraped) : "never run"}
                  </span>
                  <button
                    onClick={() => {
                      if (window.confirm(`Delete source "${s.name}"? The server refuses while it still has collected articles.`))
                        deleteSource.mutate(s.id);
                    }}
                    disabled={deleteSource.isPending && deleteSource.variables === s.id}
                    title="Delete this source"
                    className="p-1.5 rounded-lg text-muted-foreground hover:text-red-600 hover:bg-red-50 transition-colors disabled:opacity-40"
                  >
                    {deleteSource.isPending && deleteSource.variables === s.id
                      ? <Loader2 size={13} className="animate-spin" />
                      : <Trash2 size={13} />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {deleteSource.isError && (
          <div className="mt-3">
            <FormError error={deleteSource.error} />
          </div>
        )}

        {trigger.isError && (
          <div className="mt-3">
            <FormError error={trigger.error} />
          </div>
        )}
        {trigger.isSuccess && !trigger.isPending && (
          <p className="mt-3 text-xs text-primary font-semibold">
            Collection run finished. New articles appear in the feed below; duplicates are skipped.
          </p>
        )}
      </div>

      <Modal open={addOpen} onClose={() => setAddOpen(false)}
        title="Add a watch source"
        subtitle="POST /api/veille/sources — the agent fetches active sources on each run">
        <AddSourceForm onDone={() => setAddOpen(false)} />
      </Modal>

      {/* Trending topics — real tag frequencies from the collected corpus */}
      <div className="bg-gradient-to-br from-[#0F3D2E] to-[#0B6E4F] rounded-2xl p-5 text-white">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-3">
          Most frequent AI-assigned tags
        </p>
        <div className="flex flex-wrap gap-2">
          {topTags.length === 0 && (
            <span className="text-xs text-white/70">
              No tags yet — trigger a scrape to let the agent tag incoming literature.
            </span>
          )}
          {topTags.map(([tag, count]) => (
            <span key={tag} className="px-3 py-1.5 bg-white/10 border border-white/15 rounded-full text-xs font-medium backdrop-blur-sm hover:bg-white/20 cursor-pointer transition-colors">
              {tag} <span className="text-white/50">{count}</span>
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
            {activeSources.length === 0 ? (
              <>
                <p className="text-xs text-muted-foreground mt-1 mb-4">
                  A collection run iterates active sources, and there are none — so a scrape
                  would finish without collecting anything. Add a feed first.
                </p>
                <button onClick={() => setAddOpen(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold bg-primary text-white px-4 py-2 rounded-xl hover:bg-primary/90">
                  <Plus size={13} /> Add source
                </button>
              </>
            ) : (
              <>
                <p className="text-xs text-muted-foreground mt-1 mb-4">
                  Trigger a scrape to fetch {activeSources.length} active source
                  {activeSources.length === 1 ? "" : "s"}.
                </p>
                <button onClick={() => trigger.mutate()} disabled={trigger.isPending}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold bg-primary text-white px-4 py-2 rounded-xl hover:bg-primary/90 disabled:opacity-60">
                  <RefreshCw size={13} className={trigger.isPending ? "animate-spin" : ""} /> Trigger scrape
                </button>
              </>
            )}
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
  const { data: aiArticles } = useArticles();
  const { data: aiResearchers } = useResearchers();
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hello! I can search the lab's collected publications and researcher profiles. Ask me about a topic, method, or name." },
  ]);
  // Suggestions are the most frequent real tags on the collected articles, so a
  // click always returns hits. (`Map` is the lucide icon in this file — use a
  // record.) Falls back to nothing when no articles have been collected yet.
  const suggestionFreq: Record<string, number> = {};
  for (const a of aiArticles ?? []) {
    for (const t of a.tags) suggestionFreq[t.tag] = (suggestionFreq[t.tag] ?? 0) + 1;
  }
  const suggestions = Object.entries(suggestionFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([t]) => t);

  // Local keyword search over live API data. Conversational answers would need a
  // backend RAG endpoint — the API does not expose one yet.
  const answer = (q: string): string => {
    const terms = q.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    if (!terms.length) return "Try a longer query — single short words match too much.";

    const articles = aiArticles ?? [];
    const researchers = aiResearchers ?? [];
    const matches = (hay: string) => terms.some(t => hay.toLowerCase().includes(t));

    const hitArticles = articles.filter(a =>
      matches(a.title) ||
      matches(a.abstract ?? "") ||
      a.tags.some(t => matches(t.tag)),
    );
    const hitResearchers = researchers.filter(r => matches(r.name) || matches(r.department) || matches(r.role));

    if (!hitArticles.length && !hitResearchers.length) {
      return `No matches in ${articles.length} collected article${articles.length === 1 ? "" : "s"} or ${researchers.length} researcher profile${researchers.length === 1 ? "" : "s"}. Run the Scientific Watch agent to collect more literature.`;
    }

    const parts: string[] = [
      `Found ${hitArticles.length} article${hitArticles.length === 1 ? "" : "s"} and ${hitResearchers.length} researcher${hitResearchers.length === 1 ? "" : "s"} (searched ${articles.length} articles, ${researchers.length} profiles).`,
    ];
    if (hitArticles.length) {
      parts.push("Publications: " + hitArticles.slice(0, 3).map(a => `“${a.title}”`).join("; "));
      const summary = hitArticles.find(a => a.summaries.length)?.summaries[0]?.summary_text;
      if (summary) parts.push("Summary: " + summary.slice(0, 260) + (summary.length > 260 ? "…" : ""));
    }
    if (hitResearchers.length) {
      parts.push("Researchers: " + hitResearchers.slice(0, 3).map(r => `${r.name} (${r.department})`).join("; "));
    }
    return parts.join("\n\n");
  };

  const send = () => {
    if (!input.trim()) return;
    const q = input;
    setMessages(m => [...m, { role: "user", text: q }, { role: "ai", text: answer(q) }]);
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
            <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs leading-relaxed whitespace-pre-line
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
  const { data: dbArticles } = useArticles();
  const { data: dbResearchersData } = useResearchers();
  const { data: dbProjets } = useProjets();
  const { data: dbPersonnels } = usePersonnels();
  const { data: dbSources } = useSources();
  const { data: dbParcels } = useParcels();
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
  const [researcherQuery, setResearcherQuery] = useState("");
  const [researcherDept, setResearcherDept] = useState<string | null>(null);
  const [carouselIdx, setCarouselIdx] = useState(0);
  const [savedPosts, setSavedPosts] = useState<Set<number>>(new Set());

  // Research feed built from the articles the veille agent collected.
  // The API carries no engagement metrics (likes/views), so those are not shown.
  const feedItems = (dbArticles ?? []).map(a => {
    const body = a.summaries[0]?.summary_text || a.abstract || "";
    const words = body.trim() ? body.trim().split(/\s+/).length : 0;
    return {
      id: a.id,
      type: a.summaries.length ? "insight" : "research",
      title: a.title,
      summary: body || "No abstract or summary available for this article yet.",
      author: a.authors?.[0] || "Unknown author",
      coAuthors: Math.max(0, (a.authors?.length ?? 0) - 1),
      date: formatDate(a.published_at ?? a.collected_at),
      sortKey: new Date(a.published_at ?? a.collected_at).getTime(),
      readTime: words ? `${Math.max(1, Math.round(words / 200))} min` : "—",
      tags: a.tags.slice(0, 2).map(t => t.tag),
      tagCount: a.tags.length,
      hasSummary: a.summaries.length > 0,
      url: a.url,
      doi: a.doi,
      source: hostOf(a.url),
    };
  });

  const sortedFeed = [...feedItems].sort((a, b) => {
    if (feedFilter === "tagged") return b.tagCount - a.tagCount;
    if (feedFilter === "ai-picks") return Number(b.hasSummary) - Number(a.hasSummary) || b.sortKey - a.sortKey;
    return b.sortKey - a.sortKey; // "latest"
  }).filter(item => feedFilter !== "ai-picks" || item.hasSummary);


  // Real MIS projects. "Progress" is elapsed schedule time (the backend tracks no
  // completion percentage); team size counts personnel assigned to the project.
  const statutLabels: Record<string, string> = {
    planifie: "Planned", en_cours: "In progress", termine: "Completed", suspendu: "Suspended",
  };
  const featuredProjects = (dbProjets ?? []).map(p => {
    const start = new Date(p.date_debut).getTime();
    const end = p.date_fin_prevue ? new Date(p.date_fin_prevue).getTime() : null;
    const now = Date.now();
    let progress = p.statut === "termine" ? 100 : 0;
    if (p.statut !== "termine" && end && end > start) {
      progress = Math.round(Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100)));
    }
    return {
      id: p.id,
      title: p.nom,
      desc: p.description || "No description recorded for this project.",
      lead: p.responsable || "Unassigned",
      statut: p.statut,
      statutLabel: statutLabels[p.statut] ?? p.statut,
      budget: p.budget_alloue,
      progress,
      team: (dbPersonnels ?? []).filter(person => person.projet_actuel_id === p.id).length,
    };
  });

  // Categories derived from the tags the veille agent actually assigned.
  // NB: `Map` here would resolve to the lucide-react icon of that name, so use a record.
  const tagCounts: Record<string, number> = {};
  for (const a of dbArticles ?? []) {
    for (const t of a.tags) {
      const key = t.tag.trim();
      if (key) tagCounts[key] = (tagCounts[key] ?? 0) + 1;
    }
  }
  const categoryPalette = [
    { color: "from-emerald-100 to-green-50 border-emerald-200", iconColor: "text-emerald-700", icon: Sprout },
    { color: "from-blue-100 to-cyan-50 border-blue-200", iconColor: "text-blue-600", icon: Waves },
    { color: "from-orange-100 to-amber-50 border-orange-200", iconColor: "text-orange-600", icon: ThermometerSun },
    { color: "from-violet-100 to-purple-50 border-violet-200", iconColor: "text-violet-600", icon: BrainCircuit },
    { color: "from-indigo-100 to-blue-50 border-indigo-200", iconColor: "text-indigo-600", icon: SatelliteDish },
    { color: "from-teal-100 to-emerald-50 border-teal-200", iconColor: "text-teal-600", icon: BarChart2 },
    { color: "from-pink-100 to-rose-50 border-pink-200", iconColor: "text-pink-600", icon: Brain },
    { color: "from-cyan-100 to-sky-50 border-cyan-200", iconColor: "text-cyan-600", icon: Wifi },
    { color: "from-amber-100 to-yellow-50 border-amber-200", iconColor: "text-amber-700", icon: Map },
    { color: "from-sky-100 to-blue-50 border-sky-200", iconColor: "text-sky-600", icon: Droplet },
    { color: "from-green-100 to-lime-50 border-green-200", iconColor: "text-green-700", icon: Leaf },
    { color: "from-slate-100 to-gray-50 border-slate-200", iconColor: "text-slate-600", icon: Gauge },
  ];
  const categories = Object.entries(tagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 12)
    .map(([label, count], i) => ({ label, count, ...categoryPalette[i % categoryPalette.length] }));

  // Trending = most frequent tags across collected articles.
  const trending = categories.slice(0, 6).map(c => c.label);


  // Real profiles. The bibliometrie agent computes exactly three indicators
  // (h_index, i10_index, total_citations — see services/indicators.py), so those
  // are the only metrics shown. Interests are derived from the department field;
  // the backend stores no skills, institution or country per researcher.
  const researcherProfiles = (dbResearchersData ?? []).map(r => ({
    id: r.id,
    name: r.name,
    role: r.role,
    field: r.department,
    email: r.email,
    h: indicatorValue(r, "h_index"),
    i10: indicatorValue(r, "i10_index"),
    citations: indicatorValue(r, "total_citations"),
    avatar: initialsOf(r.name),
    orcid: r.orcid_id ?? null,
    scholar: r.scholar_id ?? null,
    scopus: r.scopus_id ?? null,
    cvGenerated: r.cv_profile?.last_generated ?? null,
    metricsAt: r.indicators.length
      ? r.indicators.map(i => i.computed_at).sort().slice(-1)[0]
      : null,
    interests: r.department ? r.department.split(/\s*[&,/]\s*/).filter(Boolean) : [],
  }));

  // Department facets + free-text search over the real fields.
  const researcherDepts = Array.from(new Set(researcherProfiles.map(r => r.field).filter(Boolean)));

  // Suggested searches are real terms present in the corpus — researcher names
  // and departments, plus tags ranked below the "trending" cut — so clicking one
  // always yields results. Static natural-language prompts returned nothing.
  const searchSuggestions = Array.from(new Set([
    ...researcherProfiles.slice(0, 2).map(r => r.name),
    ...researcherDepts.slice(0, 2),
    ...categories.slice(6, 8).map(c => c.label),
  ])).filter(Boolean).slice(0, 6);

  const visibleResearchers = researcherProfiles.filter(r => {
    if (researcherDept && r.field !== researcherDept) return false;
    if (!researcherQuery.trim()) return true;
    const q = researcherQuery.toLowerCase();
    return r.name.toLowerCase().includes(q)
      || r.field.toLowerCase().includes(q)
      || r.role.toLowerCase().includes(q);
  });

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
              {/* No OAuth provider is configured in AuthContext (signIn/signUp/
                  signOut only), so an "or continue with Google/ORCID" button
                  would be dead. Say what the email+password path actually is. */}
              <p className="text-[11px] text-muted-foreground text-center leading-relaxed pt-1">
                Email + password accounts are managed by Supabase. Social and ORCID
                sign-in are not enabled.
              </p>
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
                  <p className="text-xs text-muted-foreground truncate">{selectedR.field}</p>
                </div>
                <div className="flex gap-2 pb-1">
                  <a
                    href={`mailto:${selectedR.email}`}
                    className="px-4 py-2 bg-primary text-white text-xs font-bold rounded-xl hover:bg-primary/90 transition-colors flex items-center gap-1.5"
                  >
                    <Mail size={13} /> Contact
                  </a>
                </div>
              </div>

              {/* Stats — the three indicators the bibliometrie agent computes */}
              <div className="grid grid-cols-3 gap-3 mb-2">
                {[
                  { label: "H-Index", value: selectedR.h },
                  { label: "i10-Index", value: selectedR.i10 },
                  { label: "Citations", value: selectedR.citations.toLocaleString() },
                ].map(s => (
                  <div key={s.label} className="bg-muted rounded-2xl p-3 text-center">
                    <div className="text-2xl font-extrabold text-foreground font-jakarta">{s.value}</div>
                    <div className="text-[10px] text-muted-foreground">{s.label}</div>
                  </div>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mb-5">
                {selectedR.metricsAt
                  ? `Last synced ${new Date(selectedR.metricsAt).toLocaleString()} — Google Scholar, falling back to Semantic Scholar then OpenAlex.`
                  : "Metrics have not been synced yet for this researcher."}
              </p>

              {/* Research Interests — derived from the department field */}
              {selectedR.interests.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-xs font-bold text-foreground mb-2">Department & Interests</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedR.interests.map(i => <span key={i} className="px-2.5 py-1 bg-primary/8 text-primary text-xs rounded-full font-medium">{i}</span>)}
                  </div>
                </div>
              )}

              {/* Identifiers */}
              <div className="mb-4">
                <h3 className="text-xs font-bold text-foreground mb-2">Identifiers</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[10px]">
                  {[
                    { k: "ORCID", v: selectedR.orcid },
                    { k: "Scholar", v: selectedR.scholar },
                    { k: "Scopus", v: selectedR.scopus },
                  ].map(idf => (
                    <div key={idf.k} className="bg-muted rounded-xl p-2">
                      <div className="text-muted-foreground">{idf.k}</div>
                      <div className="font-mono text-foreground truncate">{idf.v ?? "not on file"}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Links — ORCID and Scholar only when the id exists; the CV route
                  streams the PDF the agent generated (weasyprint/reportlab). */}
              <div className="flex gap-2">
                {selectedR.orcid ? (
                  <a href={`https://orcid.org/${selectedR.orcid}`} target="_blank" rel="noopener noreferrer"
                     className="flex-1 py-2 bg-muted text-xs font-semibold text-muted-foreground rounded-xl hover:bg-secondary flex items-center justify-center gap-1.5 transition-colors">
                    <Globe size={12} /> ORCID
                  </a>
                ) : (
                  <span className="flex-1 py-2 bg-muted/50 text-xs font-semibold text-muted-foreground/50 rounded-xl flex items-center justify-center gap-1.5 cursor-not-allowed">
                    <Globe size={12} /> No ORCID
                  </span>
                )}
                {selectedR.scholar ? (
                  <a href={`https://scholar.google.com/citations?user=${selectedR.scholar}`} target="_blank" rel="noopener noreferrer"
                     className="flex-1 py-2 bg-muted text-xs font-semibold text-muted-foreground rounded-xl hover:bg-secondary flex items-center justify-center gap-1.5 transition-colors">
                    <BookOpen size={12} /> Scholar
                  </a>
                ) : (
                  <span className="flex-1 py-2 bg-muted/50 text-xs font-semibold text-muted-foreground/50 rounded-xl flex items-center justify-center gap-1.5 cursor-not-allowed">
                    <BookOpen size={12} /> No Scholar id
                  </span>
                )}
                <a
                  href={`${API_BASE_URL}/api/biblio/researchers/${selectedR.id}/cv/pdf`}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={selectedR.cvGenerated ? `Last generated ${new Date(selectedR.cvGenerated).toLocaleString()}` : "Generated on request"}
                  className="flex-1 py-2 bg-muted text-xs font-semibold text-muted-foreground rounded-xl hover:bg-secondary flex items-center justify-center gap-1.5 transition-colors"
                >
                  <Download size={12} /> CV PDF
                </a>
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
              <p className="text-muted-foreground text-lg mb-6 max-w-xl mx-auto">
                Access {dbArticles?.length ?? 0} publication{(dbArticles?.length ?? 0) === 1 ? "" : "s"}, connect with {dbResearchersData?.length ?? 0} researcher{(dbResearchersData?.length ?? 0) === 1 ? "" : "s"}, and explore AI-powered scientific insights.
              </p>
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
                  {searchSuggestions.length > 0 && (
                    <div>
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-2">Suggested Searches</p>
                      <div className="flex flex-wrap gap-1.5">
                        {searchSuggestions.map(s => (
                          <button key={s} onClick={() => setSearchQuery(s)} className="px-2.5 py-1 bg-muted hover:bg-primary hover:text-white text-xs text-muted-foreground rounded-full transition-colors">{s}</button>
                        ))}
                      </div>
                    </div>
                  )}
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
            {categories.length === 0 && (
              <p className="text-sm text-muted-foreground col-span-full">
                No tagged articles yet — domains appear once the Scientific Watch agent tags collected literature.
              </p>
            )}
            {categories.map(c => (
              <button key={c.label} className={`bg-gradient-to-br ${c.color} border rounded-2xl p-4 text-left hover:shadow-md hover:-translate-y-0.5 transition-all group`}>
                <c.icon size={22} className={`${c.iconColor} mb-2`} />
                <p className="text-xs font-bold text-foreground leading-tight mb-1">{c.label}</p>
                <p className="text-[10px] text-muted-foreground">{c.count} article{c.count === 1 ? "" : "s"}</p>
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
            {featuredProjects.length === 0 && (
              <p className="text-sm text-muted-foreground col-span-full">
                No projects registered yet. Add them via the MIS module.
              </p>
            )}
            {featuredProjects.map((p, i) => (
              <div key={p.id} className={`bg-card border border-border rounded-2xl overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all group ${i < carouselIdx ? "opacity-40" : "opacity-100"}`}>
                <div className="relative h-36 bg-gradient-to-br from-[#0F3D2E] to-[#0B6E4F] overflow-hidden flex items-end p-3">
                  <div className="absolute top-3 right-3">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      p.statut === "en_cours" ? "bg-emerald-400/90 text-emerald-950"
                        : p.statut === "termine" ? "bg-white/80 text-[#0F3D2E]"
                        : p.statut === "suspendu" ? "bg-red-400/90 text-red-950"
                        : "bg-amber-300/90 text-amber-950"
                    }`}>{p.statutLabel}</span>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-white/90 bg-white/20 backdrop-blur-sm px-2 py-0.5 rounded-full">
                      Lead: {p.lead}
                    </span>
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="font-bold text-foreground font-jakarta text-sm mb-1.5 group-hover:text-primary transition-colors">{p.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-3 line-clamp-2">{p.desc}</p>
                  <div className="mb-2">
                    <div className="flex justify-between text-[10px] mb-1">
                      <span className="text-muted-foreground">Schedule elapsed</span>
                      <span className="font-semibold text-foreground">{p.progress}%</span>
                    </div>
                    <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-primary to-[#2D9C72] rounded-full" style={{ width: `${p.progress}%` }} />
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <div className="flex items-center gap-1"><Users size={11} />{p.team} assigned</div>
                    <span className="font-semibold text-foreground">
                      {p.budget.toLocaleString("en-US", { style: "currency", currency: "MAD", maximumFractionDigits: 0 })}
                    </span>
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
                {["latest", "tagged", "ai-picks"].map(f => (
                  <button key={f} onClick={() => setFeedFilter(f)}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-semibold transition-colors capitalize
                      ${feedFilter === f ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
                    {f === "ai-picks" ? "AI Summarized" : f === "tagged" ? "Most Tagged" : "Latest"}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-5">
              {sortedFeed.length === 0 && (
                <div className="bg-card border border-border rounded-2xl p-8 text-center text-sm text-muted-foreground">
                  {feedFilter === "ai-picks"
                    ? "No AI-summarized articles yet."
                    : "No articles collected yet. The Scientific Watch agent populates this feed."}
                </div>
              )}
              {sortedFeed.map(item => {
                const tl = typeLabels[item.type];
                const saved = savedPosts.has(item.id);
                return (
                  <article key={item.id} className="bg-card border border-border rounded-2xl overflow-hidden hover:shadow-lg hover:border-primary/15 transition-all group">
                    <div className="relative h-20 bg-gradient-to-br from-[#0F3D2E] to-[#0B6E4F] overflow-hidden">
                      <div className="absolute top-3 left-3">
                        <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${tl.color}`}>{tl.label}</span>
                      </div>
                      <div className="absolute top-3 right-3 flex gap-2">
                        {item.tags.map(t => <span key={t} className="text-[10px] bg-white/90 text-foreground px-2 py-0.5 rounded-full font-medium">{t}</span>)}
                      </div>
                      <div className="absolute bottom-2 left-3 text-[10px] text-white/70">{item.source}</div>
                    </div>
                    <div className="p-5">
                      <h3 className="text-base font-bold text-foreground font-jakarta mb-2 group-hover:text-primary transition-colors leading-snug">{item.title}</h3>
                      <p className="text-xs text-muted-foreground leading-relaxed mb-4 line-clamp-4">{item.summary}</p>
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-7 h-7 rounded-lg bg-primary/10 flex items-center justify-center text-primary text-[10px] font-bold shrink-0">
                          {initialsOf(item.author)}
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-foreground">
                            {item.author}
                            {item.coAuthors > 0 && <span className="text-muted-foreground font-normal"> +{item.coAuthors} more</span>}
                          </p>
                          <p className="text-[10px] text-muted-foreground">{item.date} · {item.readTime} read</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between pt-3 border-t border-border">
                        <div className="flex items-center gap-4">
                          <button onClick={e => { e.stopPropagation(); setSavedPosts(s => { const n = new Set(s); saved ? n.delete(item.id) : n.add(item.id); return n; }); }}
                            className={`flex items-center gap-1.5 text-xs transition-colors ${saved ? "text-primary" : "text-muted-foreground hover:text-primary"}`}>
                            <Bookmark size={14} fill={saved ? "currentColor" : "none"} /> {saved ? "Saved" : "Save"}
                          </button>
                          {item.doi && (
                            <span className="text-[10px] text-muted-foreground font-mono">DOI {item.doi}</span>
                          )}
                        </div>
                        {item.url ? (
                          <a href={item.url} target="_blank" rel="noreferrer" className="text-xs font-bold text-primary hover:underline">
                            Read source →
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground">No link</span>
                        )}
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

            {/* Monitored literature sources (veille agent) */}
            <div className="bg-card border border-border rounded-2xl p-5">
              <h3 className="font-bold text-foreground font-jakarta mb-4 flex items-center gap-2"><Calendar size={16} className="text-primary" /> Monitored Sources</h3>
              <div className="space-y-4">
                {(dbSources ?? []).length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    No sources registered yet. Add one via POST /api/veille/sources.
                  </p>
                )}
                {(dbSources ?? []).map(s => (
                  <div key={s.id} className="border border-border rounded-xl p-3 hover:border-primary/30 hover:bg-muted/50 transition-all group">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h4 className="text-xs font-bold text-foreground leading-snug group-hover:text-primary transition-colors">{s.name}</h4>
                      <span className={`shrink-0 text-[9px] font-semibold px-2 py-0.5 rounded-full ${
                        s.active ? "text-emerald-700 bg-emerald-100" : "text-muted-foreground bg-muted"
                      }`}>{s.active ? "active" : "paused"}</span>
                    </div>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground mb-2">
                      <MapPin size={10} /> {s.type.toUpperCase()} · {hostOf(s.url)}
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">
                        Last scraped: {s.last_scraped ? formatDate(s.last_scraped) : "never"}
                      </span>
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-primary font-bold hover:underline">Visit</a>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Monitored parcels (digital-twin agent) */}
            <div className="bg-card border border-border rounded-2xl p-5">
              <h3 className="font-bold text-foreground font-jakarta mb-4 flex items-center gap-2"><Database size={16} className="text-primary" /> Monitored Parcels</h3>
              <div className="space-y-3">
                {(dbParcels ?? []).length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    No parcels registered yet. Add one via POST /api/twin/parcels.
                  </p>
                )}
                {(dbParcels ?? []).map(p => (
                  <div key={p.id} className="p-3 bg-muted rounded-xl hover:bg-secondary transition-colors group">
                    <p className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors mb-1 leading-snug">{p.name}</p>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground mb-2">
                      <span>{p.crop_type}</span><span>·</span><span>{p.area_ha} ha</span><span>·</span><span>{p.soil_type}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full font-mono">{p.code}</span>
                      <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                        <SquareCode size={10} /> {p.latitude.toFixed(2)}, {p.longitude.toFixed(2)}
                      </span>
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
            <span className="text-xs text-muted-foreground">
              {visibleResearchers.length} of {researcherProfiles.length} shown
            </span>
          </div>
          {/* Filter bar — facets are the real department values on file */}
          <div className="flex flex-wrap gap-2 mb-5">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                value={researcherQuery}
                onChange={e => setResearcherQuery(e.target.value)}
                placeholder="Search by name, role or department…"
                className="pl-9 pr-4 py-2 text-xs bg-white border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 w-64"
              />
            </div>
            {researcherDepts.map(f => (
              <button
                key={f}
                onClick={() => setResearcherDept(researcherDept === f ? null : f)}
                className={`px-3 py-2 text-xs font-medium rounded-xl transition-colors
                  ${researcherDept === f ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-secondary"}`}
              >
                {f}
              </button>
            ))}
          </div>
          {researcherProfiles.length === 0 && (
            <div className="bg-card border border-border rounded-2xl p-8 text-center text-sm text-muted-foreground">
              No researchers on file yet — add one via <span className="font-mono">POST /api/biblio/researchers</span>.
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {visibleResearchers.map(r => (
              <div key={r.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-lg hover:-translate-y-0.5 transition-all group cursor-pointer" onClick={() => setSelectedResearcher(r.id)}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-[#2D9C72] flex items-center justify-center text-white font-extrabold text-lg shadow-md">
                    {r.avatar}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-sm font-bold text-foreground font-jakarta truncate group-hover:text-primary transition-colors">{r.name}</h3>
                    <p className="text-[10px] text-primary font-semibold truncate">{r.role}</p>
                    <p className="text-[10px] text-muted-foreground truncate">{r.field}</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 mb-4">
                  {[["H-idx", r.h], ["i10", r.i10], ["Cited", r.citations > 999 ? (r.citations / 1000).toFixed(1) + "K" : r.citations]].map(([l, v]) => (
                    <div key={l as string} className="bg-muted rounded-xl p-2 text-center">
                      <div className="text-sm font-bold text-foreground">{v}</div>
                      <div className="text-[9px] text-muted-foreground">{l}</div>
                    </div>
                  ))}
                </div>
                <button className="w-full py-2 bg-primary/8 text-primary text-[10px] font-bold rounded-xl group-hover:bg-primary group-hover:text-white transition-colors">View Profile</button>
              </div>
            ))}
          </div>
        </section>

        {/* ── Latest Publications ── */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-bold text-foreground font-jakarta">Latest Publications</h2>
            <button className="text-xs text-primary font-semibold">See all {dbArticles?.length ?? "…"} →</button>
          </div>
          <div className="space-y-4">
            {(dbArticles ?? []).length === 0 && (
              <div className="bg-card border border-border rounded-2xl p-6 text-center text-sm text-muted-foreground">No publications collected yet.</div>
            )}
            {(dbArticles ?? []).slice(0, 6).map(art => (
              <div key={art.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md hover:border-primary/20 transition-all group">
                <div className="flex items-start gap-5">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-100 text-emerald-700">Collected</span>
                      <span className="text-[10px] font-bold text-primary">{hostOf(art.url)}</span>
                      <span className="text-[10px] text-muted-foreground">{formatDate(art.published_at ?? art.collected_at)}</span>
                    </div>
                    <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors mb-1.5 leading-snug">{art.title}</h3>
                    {art.authors && art.authors.length > 0 && <p className="text-xs text-muted-foreground mb-3">{art.authors.join(", ")}</p>}
                    <div className="flex flex-wrap gap-1.5">
                      {art.tags.map(t => <span key={t.tag} className="px-2 py-0.5 bg-primary/8 text-primary text-[10px] rounded-full font-medium">{t.tag}</span>)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 mt-3 pt-3 border-t border-border">
                  {art.url && <a href={art.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"><ExternalLink size={12} /> Source</a>}
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
                <h2 className="text-3xl font-extrabold text-white font-jakarta mb-3">Join the Lab's Research Network</h2>
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
  const { signIn, devBypass } = useAuth();
  const { data: wpArticles } = useArticles();
  const { data: wpResearchers } = useResearchers();
  const { data: wpParcels } = useParcels();
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

  // Real Supabase sign-in. When Supabase is not configured the AuthProvider is
  // already in dev-bypass mode (DEV_USER, administrator role), so there is no
  // credential to check — go straight through instead of pretending to verify.
  const handleAdminLogin = async () => {
    setError("");
    if (devBypass) { onAdmin(); return; }
    if (!email || !password) { setError("Please enter your credentials."); return; }
    setLoading(true);
    try {
      await signIn(email, password);
      onAdmin();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed.");
    } finally {
      setLoading(false);
    }
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
              <div className="text-white/40 text-[10px] mt-0.5">Multi-Agent Research Platform</div>
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

            {/* Stats — real counts; "—" while unauthenticated or still loading,
                since these endpoints sit behind the gateway's auth dependency. */}
            <div className="flex gap-8 mt-10">
              {[
                { value: wpArticles ? String(wpArticles.length) : "—", label: "Publications" },
                { value: wpResearchers ? String(wpResearchers.length) : "—", label: "Researchers" },
                { value: wpParcels ? String(wpParcels.length) : "—", label: "Monitored Parcels" },
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
                    onClick={() => void handleAdminLogin()}
                    disabled={loading}
                    className="w-full py-3.5 bg-gradient-to-r from-primary to-[#2D9C72] text-white font-bold rounded-xl hover:shadow-xl hover:shadow-primary/25 transition-all text-sm flex items-center justify-center gap-2 disabled:opacity-70"
                  >
                    {loading ? (
                      <><RefreshCw size={16} className="animate-spin" /> Authenticating…</>
                    ) : (
                      <><LogIn size={16} /> Sign In to Platform</>
                    )}
                  </button>
                </div>

                {/* Honest note about which auth path is live. Google Workspace
                    SSO and password reset are not wired to a Supabase provider,
                    so they are described rather than offered as dead buttons. */}
                <div className="mt-5 p-3 bg-accent/8 border border-accent/15 rounded-xl">
                  <p className="text-[10px] text-accent/80 leading-relaxed text-center">
                    {devBypass
                      ? "Supabase is not configured (VITE_SUPABASE_* unset), so auth is bypassed for local development — any entry signs you in as a dev administrator."
                      : "Credentials are verified by Supabase. Your role comes from the app_metadata.lab_role claim. SSO and password reset are not enabled yet."}
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

// ─── MIS CREATE FORMS (Personnel, Equipment, Budget) ─────────────────────
// These mirror the backend schemas in agents/mis/schemas.py. They are used by the
// AdminPage to let users create entities that the Quality agent can then validate.

function NewPersonnelForm({ onDone }: { onDone: () => void }) {
  const create = useCreatePersonnel();
  const [nom, setNom] = useState("");
  const [prenom, setPrenom] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Personnel["role"]>("chercheur");
  const [competences, setCompetences] = useState("");

  return (
    <form className="space-y-4" onSubmit={e => {
      e.preventDefault();
      create.mutate({
        nom: nom.trim(), prenom: prenom.trim(), email: email.trim(), role,
        competences: competences.split(",").map(s => s.trim()).filter(Boolean),
        disponible: true,
      }, { onSuccess: onDone });
    }}>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Last name" required><input required className={inputCls} value={nom} onChange={e => setNom(e.target.value)} /></Field>
        <Field label="First name" required><input required className={inputCls} value={prenom} onChange={e => setPrenom(e.target.value)} /></Field>
      </div>
      <Field label="Email" required><input required type="email" className={inputCls} value={email} onChange={e => setEmail(e.target.value)} /></Field>
      <Field label="Role" required>
        <select className={inputCls} value={role} onChange={e => setRole(e.target.value as Personnel["role"])}>
          <option value="chercheur">Chercheur</option>
          <option value="ingenieur">Ingénieur</option>
          <option value="technicien">Technicien</option>
          <option value="administratif">Administratif</option>
          <option value="doctorant">Doctorant</option>
        </select>
      </Field>
      <Field label="Skills (comma-separated)" hint="e.g. Python, GIS, hydrology">
        <input className={inputCls} value={competences} onChange={e => setCompetences(e.target.value)} placeholder="Python, data analysis" />
      </Field>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-semibold rounded-xl text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
        <SubmitButton pending={create.isPending} label="Add staff member" />
      </div>
    </form>
  );
}

function NewEquipementForm({ onDone }: { onDone: () => void }) {
  const create = useCreateEquipement();
  const [nom, setNom] = useState("");
  const [type, setType] = useState("");
  const [etat, setEtat] = useState<Equipement["etat"]>("operationnel");
  const [localisation, setLocalisation] = useState("");
  const [valeur, setValeur] = useState("0");

  return (
    <form className="space-y-4" onSubmit={e => {
      e.preventDefault();
      create.mutate({
        nom: nom.trim(), type: type.trim(), etat, localisation: localisation.trim(),
        valeur_estimee: Number(valeur) || 0,
      }, { onSuccess: onDone });
    }}>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Name" required><input required className={inputCls} value={nom} onChange={e => setNom(e.target.value)} placeholder="Spectrophotometer UV-Vis" /></Field>
        <Field label="Type" required><input required className={inputCls} value={type} onChange={e => setType(e.target.value)} placeholder="Analytical instrument" /></Field>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Status" required>
          <select className={inputCls} value={etat} onChange={e => setEtat(e.target.value as Equipement["etat"])}>
            <option value="operationnel">Operational</option>
            <option value="en_maintenance">Under maintenance</option>
            <option value="indisponible">Unavailable</option>
          </select>
        </Field>
        <Field label="Location" required><input required className={inputCls} value={localisation} onChange={e => setLocalisation(e.target.value)} placeholder="Lab A-204" /></Field>
      </div>
      <Field label="Estimated value (€)">
        <input type="number" min="0" step="any" className={inputCls} value={valeur} onChange={e => setValeur(e.target.value)} />
      </Field>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-semibold rounded-xl text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
        <SubmitButton pending={create.isPending} label="Add equipment" />
      </div>
    </form>
  );
}

function NewBudgetForm({ onDone }: { onDone: () => void }) {
  const create = useCreateBudget();
  const { data: projets } = useProjets();
  const [projetId, setProjetId] = useState("");
  const [alloue, setAlloue] = useState("0");
  const [devise, setDevise] = useState("EUR");
  const [dateDebut, setDateDebut] = useState(new Date().toISOString().slice(0, 10));
  const [dateFin, setDateFin] = useState("");
  const [description, setDescription] = useState("");

  return (
    <form className="space-y-4" onSubmit={e => {
      e.preventDefault();
      create.mutate({
        projet_id: projetId, montant_alloue: Number(alloue) || 0, montant_depense: 0, devise,
        date_debut: dateDebut, date_fin: dateFin || null, description: description.trim() || null,
      }, { onSuccess: onDone });
    }}>
      <Field label="Project" required>
        <select required className={inputCls} value={projetId} onChange={e => setProjetId(e.target.value)}>
          <option value="">Select a project…</option>
          {(projets ?? []).map(p => <option key={p.id} value={p.id}>{p.nom}</option>)}
        </select>
      </Field>
      <div className="grid grid-cols-3 gap-4">
        <Field label="Allocated amount" required>
          <input required type="number" min="0" step="any" className={inputCls} value={alloue} onChange={e => setAlloue(e.target.value)} />
        </Field>
        <Field label="Currency">
          <select className={inputCls} value={devise} onChange={e => setDevise(e.target.value)}>
            <option value="EUR">EUR</option>
            <option value="DZD">DZD</option>
            <option value="USD">USD</option>
          </select>
        </Field>
        <Field label="Start date" required>
          <input required type="date" className={inputCls} value={dateDebut} onChange={e => setDateDebut(e.target.value)} />
        </Field>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="End date"><input type="date" className={inputCls} value={dateFin} onChange={e => setDateFin(e.target.value)} /></Field>
        <Field label="Description"><input className={inputCls} value={description} onChange={e => setDescription(e.target.value)} placeholder="Annual equipment budget" /></Field>
      </div>
      <FormError error={create.error} />
      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onDone} className="px-4 py-2 text-sm font-semibold rounded-xl text-muted-foreground hover:bg-muted transition-colors">Cancel</button>
        <SubmitButton pending={create.isPending} label="Add budget" />
      </div>
    </form>
  );
}

// ─── ADMINISTRATION PAGE ─────────────────────────────────────────────────────
// Surfaces the Qualité agent (agents/qualite) plus the real session/auth state.
// Everything here is backed by an endpoint: /api/qualite/status, /rapports and
// /valider/{entite}/{id}, and the MIS collections the agent validates against.
function AdminPage() {
  const { user, devBypass, session } = useAuth();
  const { data: qStatus } = useQualiteStatus();
  const { data: rapports, isLoading: rapportsLoading } = useRapports();
  const { data: projets } = useProjets();
  const { data: personnels } = usePersonnels();
  const { data: equipements } = useEquipements();
  const { data: budgets } = useBudgets();
  const valider = useValiderEntite();
  const [family, setFamily] = useState<QualiteEntite>("projet");
  // Which create modal is open. Projects are created on the Projects page; here
  // we offer creation for staff / equipment / budget so the Quality agent has
  // real records to validate without dropping to curl.
  const [adding, setAdding] = useState<null | "personnel" | "equipement" | "budget">(null);

  const niveauStyle: Record<string, { badge: string; label: string }> = {
    conforme: { badge: "bg-emerald-100 text-emerald-700 border-emerald-200", label: "Compliant" },
    avertissement: { badge: "bg-amber-100 text-amber-700 border-amber-200", label: "Warning" },
    non_conforme: { badge: "bg-red-100 text-red-700 border-red-200", label: "Non-compliant" },
  };

  // The four entity families the agent can validate, with their real rows.
  const families: { key: QualiteEntite; label: string; rows: { id: string; label: string; sub: string }[] }[] = [
    {
      key: "projet", label: "Projects",
      rows: (projets ?? []).map(p => ({ id: p.id, label: p.nom, sub: `${p.statut} · lead ${p.responsable || "unassigned"}` })),
    },
    {
      key: "personnel", label: "Staff",
      rows: (personnels ?? []).map(p => ({ id: p.id, label: `${p.prenom} ${p.nom}`, sub: `${p.role} · ${p.email || "no email"}` })),
    },
    {
      key: "equipement", label: "Equipment",
      rows: (equipements ?? []).map(e => ({ id: e.id, label: e.nom, sub: `${e.etat} · ${e.localisation || "no location"}` })),
    },
    {
      key: "budget", label: "Budgets",
      rows: (budgets ?? []).map(b => ({
        id: b.id, label: b.description || `Budget ${b.id.slice(0, 8)}`,
        sub: `${b.montant_depense.toLocaleString()} / ${b.montant_alloue.toLocaleString()} ${b.devise}`,
      })),
    },
  ];
  const activeFamily = families.find(f => f.key === family)!;

  // Reports come back in append order; newest is most useful first.
  const recentRapports = [...(rapports ?? [])].reverse();

  const stats = [
    { label: "Reports", value: qStatus?.total_rapports, color: "text-foreground" },
    { label: "Compliant", value: qStatus?.conformes, color: "text-emerald-600" },
    { label: "Warnings", value: qStatus?.avertissements, color: "text-amber-600" },
    { label: "Non-compliant", value: qStatus?.non_conformes, color: "text-red-600" },
  ];

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div>
        <h2 className="text-xl font-bold text-foreground font-jakarta">Administration</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Data quality, GDPR compliance and session state · Quality agent {qStatus ? qStatus.statut : "connecting…"}
        </p>
      </div>

      {/* Quality agent stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map(s => (
          <div key={s.label} className="bg-card border border-border rounded-2xl p-4">
            <div className="text-[10px] uppercase tracking-wide text-muted-foreground mb-1">{s.label}</div>
            <div className={`text-2xl font-bold font-jakarta ${s.color}`}>{s.value ?? "—"}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        {/* Run a validation */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-border">
            <h3 className="font-bold text-foreground font-jakarta">Run a Validation</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              The Quality agent re-reads the record and reports missing fields, budget overruns and
              GDPR gaps (staff records only).
            </p>
          </div>
          <div className="px-5 pt-4">
            <div className="flex items-center justify-between gap-2">
              <div className="flex bg-muted rounded-xl p-1 gap-1 flex-1">
                {families.map(f => (
                  <button
                    key={f.key}
                    onClick={() => setFamily(f.key)}
                    className={`flex-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors
                      ${family === f.key ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    {f.label} <span className="opacity-60">{f.rows.length}</span>
                  </button>
                ))}
              </div>
              {family !== "projet" && (
                <button
                  onClick={() => setAdding(family)}
                  className="shrink-0 flex items-center gap-1 px-2.5 py-1.5 text-[11px] font-semibold rounded-lg bg-primary text-white hover:bg-primary/90 transition-colors"
                >
                  <Plus size={12} /> Add
                </button>
              )}
            </div>
          </div>
          <div className="p-5 space-y-2 max-h-80 overflow-y-auto scrollbar-hide">
            {activeFamily.rows.length === 0 && (
              <div className="text-xs text-muted-foreground py-6 text-center space-y-3">
                <p>
                  No {activeFamily.label.toLowerCase()} recorded yet{family === "projet" ? " — create projects on the Research Projects page." : "."}
                </p>
                {family !== "projet" && (
                  <button
                    onClick={() => setAdding(family)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-primary text-white hover:bg-primary/90 transition-colors"
                  >
                    <Plus size={13} /> Add the first {activeFamily.label.toLowerCase().replace(/s$/, "")}
                  </button>
                )}
              </div>
            )}
            {activeFamily.rows.map(row => {
              const pending = valider.isPending && valider.variables?.id === row.id;
              const latest = recentRapports.find(r => r.entite_id === row.id);
              return (
                <div key={row.id} className="flex items-center gap-3 p-3 bg-muted/50 rounded-xl">
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-semibold text-foreground truncate">{row.label}</div>
                    <div className="text-[10px] text-muted-foreground truncate">{row.sub}</div>
                  </div>
                  {latest && (
                    <span className={`px-2 py-0.5 rounded-full border text-[9px] font-semibold shrink-0 ${niveauStyle[latest.niveau]?.badge ?? ""}`}>
                      {niveauStyle[latest.niveau]?.label ?? latest.niveau}
                    </span>
                  )}
                  <button
                    onClick={() => valider.mutate({ entite: activeFamily.key, id: row.id })}
                    disabled={valider.isPending}
                    className="shrink-0 px-2.5 py-1.5 bg-primary text-white text-[10px] font-semibold rounded-lg flex items-center gap-1 hover:bg-primary/90 transition-colors disabled:opacity-50"
                  >
                    <Shield size={10} className={pending ? "animate-pulse" : ""} />
                    {pending ? "Checking…" : "Validate"}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Reports */}
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-border">
            <h3 className="font-bold text-foreground font-jakarta">Compliance Reports</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Held in memory by the API process — they reset on restart.
            </p>
          </div>
          <div className="p-5 space-y-3 max-h-96 overflow-y-auto scrollbar-hide">
            {rapportsLoading && (
              <div className="flex items-center justify-center py-10 text-muted-foreground text-sm">
                <RefreshCw size={16} className="animate-spin mr-2" />Loading reports…
              </div>
            )}
            {!rapportsLoading && recentRapports.length === 0 && (
              <p className="text-xs text-muted-foreground py-10 text-center">
                No validation has been run yet. Pick a record on the left and press Validate.
              </p>
            )}
            {recentRapports.map(r => (
              <div key={r.id} className="border border-border rounded-xl p-3">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`px-2 py-0.5 rounded-full border text-[9px] font-semibold shrink-0 ${niveauStyle[r.niveau]?.badge ?? ""}`}>
                      {niveauStyle[r.niveau]?.label ?? r.niveau}
                    </span>
                    <span className="text-[10px] text-muted-foreground font-mono truncate">
                      {r.entite_type}/{r.entite_id}
                    </span>
                  </div>
                  <span className="text-[9px] text-muted-foreground shrink-0">
                    {new Date(r.timestamp).toLocaleString()}
                  </span>
                </div>
                {r.problemes.length === 0 ? (
                  <p className="text-[10px] text-emerald-600">No issues found.</p>
                ) : (
                  <ul className="list-disc pl-4 space-y-0.5">
                    {r.problemes.map((p, i) => (
                      <li key={i} className="text-[10px] text-muted-foreground">{p}</li>
                    ))}
                  </ul>
                )}
                {r.entite_type === "personnel" && (
                  <div className={`mt-1.5 text-[9px] font-semibold ${r.conforme_rgpd ? "text-emerald-600" : "text-red-600"}`}>
                    {r.conforme_rgpd ? "GDPR: compliant" : "GDPR: non-compliant"}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Session & access — real values, no user-management endpoint exists yet */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-border">
          <h3 className="font-bold text-foreground font-jakarta">Session & Access</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Roles come from the Supabase <span className="font-mono">app_metadata.lab_role</span> claim; the API
            enforces them per route. There is no user-management endpoint yet, so accounts are managed in Supabase.
          </p>
        </div>
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          {[
            { k: "Signed in as", v: user?.email ?? "not signed in" },
            { k: "Role claim", v: user?.role ?? "—" },
            { k: "User id", v: user?.id ?? "—" },
            { k: "API base URL", v: API_BASE_URL },
            { k: "Auth mode", v: devBypass ? "dev bypass (Supabase not configured)" : "Supabase JWT" },
            { k: "Access token", v: session?.access_token ? "present" : devBypass ? "not required" : "none" },
          ].map(row => (
            <div key={row.k} className="flex flex-col gap-0.5">
              <span className="text-[10px] uppercase tracking-wide text-muted-foreground">{row.k}</span>
              <span className="font-mono text-foreground break-all">{row.v}</span>
            </div>
          ))}
        </div>
        {devBypass && (
          <div className="mx-5 mb-5 flex items-start gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-800">
            <AlertCircle size={13} className="mt-0.5 shrink-0" />
            <span>
              Auth is bypassed because <span className="font-mono">VITE_SUPABASE_*</span> is unset. This pairs with
              the backend's <span className="font-mono">DISABLE_AUTH</span> flag and must never be used in a deployed
              environment.
            </span>
          </div>
        )}
      </div>

      {/* Create-entity modals — staff / equipment / budget. Projects are created
          on the Projects page; here we only offer the three entities the Quality
          agent validates against. */}
      <Modal open={adding === "personnel"} onClose={() => setAdding(null)}
        title="Add staff member"
        subtitle="POST /api/mis/personnels/ — stored by the MIS agent">
        <NewPersonnelForm onDone={() => setAdding(null)} />
      </Modal>
      <Modal open={adding === "equipement"} onClose={() => setAdding(null)}
        title="Add equipment"
        subtitle="POST /api/mis/equipements/ — stored by the MIS agent">
        <NewEquipementForm onDone={() => setAdding(null)} />
      </Modal>
      <Modal open={adding === "budget"} onClose={() => setAdding(null)}
        title="Add budget"
        subtitle="POST /api/mis/budgets/ — stored by the MIS agent">
        <NewBudgetForm onDone={() => setAdding(null)} />
      </Modal>
    </div>
  );
}
// Used only for modules with no backend behind them yet. It says so plainly
// rather than showing an inert "Explore" button over invented content.
function PlaceholderPage({ title, desc, missing, icon: Icon }: {
  title: string; desc: string; missing: string; icon: React.ElementType;
}) {
  return (
    <div className="h-full flex items-center justify-center p-8">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/15 to-primary/5 flex items-center justify-center mx-auto mb-5">
          <Icon size={36} className="text-primary" />
        </div>
        <h2 className="text-2xl font-bold text-foreground font-jakarta mb-2">{title}</h2>
        <p className="text-muted-foreground mx-auto text-sm leading-relaxed">{desc}</p>
        <div className="mt-6 flex items-start gap-2 px-4 py-3 bg-muted/60 border border-border rounded-xl text-xs text-muted-foreground text-left">
          <Info size={14} className="mt-0.5 shrink-0" />
          <span>Not implemented yet — {missing}</span>
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
      case "dashboard": return <DashboardPage onNavigate={setPage} />;
      case "projects": return <ProjectsPage />;
      case "publications": return <PublicationsPage />;
      case "researchers": return <ResearchersPage />;
      case "twins": return <DigitalTwinsPage />;
      case "iot": return <IoTPage />;
      case "watch": return <WatchPage />;
      case "theses": return <PlaceholderPage title="Theses & Masters" desc="Track PhD and master's theses, progress, supervisors and defence calendars." missing="there is no thesis model or endpoint in the backend. Supervision could be derived from MIS staff and projects." icon={GraduationCap} />;
      case "gis": return <PlaceholderPage title="GIS Maps & Spatial Analytics" desc="Interactive spatial mapping and environmental overlay layers." missing="no map layer is served yet. Parcels already carry latitude/longitude via /api/twin/parcels, which is enough to plot them." icon={Map} />;
      case "datasets": return <PlaceholderPage title="Open Data Portal" desc="Published datasets with API access and downloads." missing="no dataset model exists. The closest real data are the monitored sources (/api/veille/sources) and parcel readings (/api/twin/parcels)." icon={Database} />;
      case "events": return <PlaceholderPage title="Events & Conferences" desc="Scientific events timeline, registration and post-event archives." missing="no event or conference model exists in the backend." icon={Globe} />;
      case "news": return <PlaceholderPage title="News & Updates" desc="Lab announcements and media coverage." missing="no news model exists. The scientific watch feed (/api/veille/articles) is the live alternative." icon={Newspaper} />;
      case "admin": return <AdminPage />;
      case "agents": return <AgentsPage setPage={setPage} />;
      case "visitor": return <VisitorPortalPage />;
      default: return <DashboardPage onNavigate={setPage} />;
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
