import React, { useState } from "react";
import { Plus, MoreHorizontal, Users, Clock } from "lucide-react";
import { projects } from "../mockData";

export default function Projects() {
  const [view, setView] = useState("kanban");
  const statusCols = ["planning", "active", "completed"];
  const statusLabels = { planning: "Planning", active: "Active", completed: "Completed" };
  const statusColors = {
    planning: "bg-amber-100 text-amber-700 border-amber-200",
    active: "bg-emerald-100 text-emerald-700 border-emerald-200",
    completed: "bg-blue-100 text-blue-700 border-blue-200",
  };
  const riskColors = {
    low: "text-emerald-600", medium: "text-amber-600", high: "text-red-500", none: "text-muted-foreground",
  };

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Research Projects</h2>
          <p className="text-sm text-muted-foreground mt-0.5">47 projects · 8 active · MAD 12.4M total budget</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex bg-muted rounded-xl p-1 gap-1">
            {["kanban", "timeline"].map(v => (
              <button key={v} onClick={() => setView(v)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize
                ${view === v ? "bg-white text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
                {v}
              </button>
            ))}
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl hover:bg-primary/90 transition-colors">
            <Plus size={14} /> <span className="hidden sm:inline">New Project</span>
          </button>
        </div>
      </div>

      {view === "kanban" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
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
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-muted-foreground">
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
