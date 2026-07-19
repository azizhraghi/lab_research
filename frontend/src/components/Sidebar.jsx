import { NavLink } from "react-router-dom";
import {
  Activity,
  Droplets,
  GraduationCap,
  LayoutDashboard,
  Newspaper,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { health } from "../lib/api";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard", hint: "Overview" },
  { to: "/veille", icon: Newspaper, label: "Veille", hint: "Scientific watch" },
  { to: "/bibliometrie", icon: GraduationCap, label: "Bibliometrie", hint: "Profiles & CVs" },
  { to: "/digital-twin", icon: Droplets, label: "Digital Twin", hint: "Irrigation scenarios" },
];

export default function Sidebar() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    health()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-logo">AI</span>
        <div>
          <h1 className="sidebar-title">Research Lab</h1>
          <p className="sidebar-subtitle">Agent platform</p>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {links.map(({ to, icon: Icon, label, hint }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "sidebar-link--active" : ""}`
            }
          >
            <span className="sidebar-link__icon"><Icon size={18} /></span>
            <span className="sidebar-link__text">
              <strong>{label}</strong>
              <small>{hint}</small>
            </span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-review-card">
        <ShieldCheck size={18} />
        <div>
          <strong>Governed AI</strong>
          <p>Human validation stays in the loop for sensitive outputs.</p>
        </div>
      </div>

      <div className="sidebar-footer">
        <div className={`status-dot ${status === "ok" ? "status-dot--ok" : "status-dot--off"}`} />
        <span className="status-label">
          Backend {status === "ok" ? "Online" : "Offline"}
        </span>
        {status === null && <Activity size={13} className="spin" />}
      </div>
    </aside>
  );
}
