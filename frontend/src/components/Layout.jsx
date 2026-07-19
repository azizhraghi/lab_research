import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Cpu,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Moon,
  Search,
  Sun,
} from "lucide-react";
import { useAuth } from "../auth/AuthProvider";

function NavItem({ icon: Icon, label, path, currentPath, collapsed }) {
  const active = currentPath === path || currentPath.startsWith(`${path}/`);
  return (
    <Link
      to={path}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative ${
        active
          ? "bg-primary text-primary-foreground shadow-sm"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
      }`}
    >
      <Icon size={18} className="shrink-0" />
      {!collapsed && <span className="truncate">{label}</span>}
      {collapsed && (
        <div className="absolute left-full ml-2 px-2 py-1 bg-foreground text-background text-xs rounded-md opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity">
          {label}
        </div>
      )}
    </Link>
  );
}

function Sidebar({ collapsed, setCollapsed, dark, location }) {
  const nav = [
    { icon: LayoutDashboard, label: "Dashboard", path: "/" },
    { icon: Search, label: "Scientific Watch", path: "/watch" },
    { icon: BookOpen, label: "Bibliometrics", path: "/bibliometrics" },
    { icon: Cpu, label: "Digital Twin", path: "/digital-twin" },
  ];

  return (
    <aside className={`flex flex-col h-full ${dark ? "bg-[#0A1F16]" : "bg-white"} border-r border-border transition-all duration-300 ${collapsed ? "w-16" : "w-60"} shrink-0 z-20`}>
      <div className={`flex items-center gap-3 px-3 py-5 border-b border-border ${collapsed ? "justify-center" : ""}`}>
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0 shadow-sm">
          <FlaskConical size={16} className="text-white" />
        </div>
        {!collapsed && (
          <div className="font-bold text-sm tracking-tight text-foreground font-jakarta truncate">
            AI Research Lab <span className="text-primary">Platform</span>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1 scrollbar-hide" aria-label="Primary navigation">
        {nav.map((item) => (
          <NavItem key={item.path} {...item} currentPath={location.pathname} collapsed={collapsed} />
        ))}
      </nav>

      <div className="p-3 border-t border-border">
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 p-2 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
          title={collapsed ? "Expand navigation" : "Collapse navigation"}
        >
          {collapsed ? <ChevronRight size={18} /> : <><ChevronLeft size={18} /><span className="text-xs font-medium">Collapse</span></>}
        </button>
      </div>
    </aside>
  );
}

function TopNav({ dark, setDark, location }) {
  const { signOut, user } = useAuth();
  const [signingOut, setSigningOut] = useState(false);
  const pathParts = location.pathname.split("/").filter(Boolean);
  const pageName = pathParts.length > 0
    ? pathParts[0].replace("-", " ")
    : "Dashboard";
  const displayName = user?.user_metadata?.full_name || user?.email?.split("@")[0] || "Laboratory member";
  const initials = displayName.split(/\s+/).map((part) => part[0]).join("").slice(0, 2).toUpperCase();

  const handleSignOut = async () => {
    setSigningOut(true);
    await signOut();
    setSigningOut(false);
  };

  return (
    <header className="h-16 border-b border-border bg-card/90 backdrop-blur-md px-4 flex items-center gap-4 shrink-0 z-10 sticky top-0">
      <div className="font-semibold text-lg text-foreground capitalize font-jakarta">{pageName}</div>
      <div className="flex items-center gap-2 ml-auto">
        <button type="button" onClick={() => setDark(!dark)} className="p-2 rounded-lg hover:bg-secondary text-muted-foreground transition-colors" title="Toggle theme">
          {dark ? <Sun size={18} /> : <Moon size={18} />}
        </button>
        <div className="hidden sm:flex items-center gap-2 pl-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white text-xs font-bold">{initials}</div>
          <div className="text-left max-w-40">
            <div className="text-xs font-semibold text-foreground truncate">{displayName}</div>
            <div className="text-[10px] text-muted-foreground truncate">{user?.email}</div>
          </div>
        </div>
        <button type="button" onClick={handleSignOut} disabled={signingOut} className="p-2 rounded-lg hover:bg-secondary text-muted-foreground transition-colors disabled:opacity-60" title="Sign out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false);
  const [dark, setDark] = useState(false);
  const location = useLocation();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className={`h-screen flex overflow-hidden bg-background font-sans ${dark ? "dark" : ""}`} style={{ fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif" }}>
      <Sidebar location={location} collapsed={collapsed} setCollapsed={setCollapsed} dark={dark} />
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        <TopNav location={location} dark={dark} setDark={setDark} />
        <main className="flex-1 overflow-hidden relative">{children}</main>
      </div>
    </div>
  );
}