import React, { useState, useEffect, useRef } from "react";
import {
  FolderKanban, BookOpen, Users, Wifi, Bot, Database, Cpu,
  ArrowUpRight, ArrowDownRight, Clock, MoreHorizontal
} from "lucide-react";
import {
  AreaChart, Area, PieChart as RePieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from "recharts";

// ─── Animated Counter ───────────────────────────────────────────────────────
function AnimatedCounter({ target, suffix = "", prefix = "" }) {
  const [val, setVal] = useState(0);
  const ref = useRef(null);
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

// ─── KPI Card ───────────────────────────────────────────────────────────────
function KPICard({ label, value, suffix = "", change, icon: Icon, color = "primary", trend }) {
  const colors = {
    primary: "from-primary/10 to-primary/5 border-primary/20",
    emerald: "from-emerald-50 to-emerald-50/50 border-emerald-200",
    amber: "from-amber-50 to-amber-50/50 border-amber-200",
    blue: "from-blue-50 to-blue-50/50 border-blue-200",
    purple: "from-purple-50 to-purple-50/50 border-purple-200",
  };
  const iconColors = {
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

const publications = [
  { id: 1, title: "Groundwater Recharge Dynamics Under Climate Change Scenarios in Semi-Arid Regions", authors: "El-Amine, K., Bouziane, A., Chakir, R.", journal: "Journal of Hydrology", year: 2024, citations: 47, impact: 6.2, tags: ["Climate", "Hydrology", "AI"], status: "published" },
  { id: 2, title: "Deep Learning for Real-Time Remote Sensing Data Fusion in Environmental Monitoring", authors: "Mansouri, L., Ouali, S., Benali, T.", journal: "Remote Sensing", year: 2024, citations: 31, impact: 5.8, tags: ["AI", "Remote Sensing", "IoT"], status: "published" },
  { id: 3, title: "Digital Twin Framework for Aquifer System Simulation and Predictive Governance", authors: "Bouziane, A., El-Amine, K., Alami, M.", journal: "Environmental Modelling & Software", year: 2024, citations: 18, impact: 4.9, tags: ["Digital Twins", "Simulation"], status: "published" },
];

const COLORS = ["#0B6E4F", "#2D9C72", "#4ADE80", "#F59E0B", "#3B82F6"];
const pubTypeData = [
  { name: "Journal Articles", value: 143 }, { name: "Conference Papers", value: 68 },
  { name: "Book Chapters", value: 24 }, { name: "Policy Briefs", value: 31 },
];

export default function DashboardPage() {
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
