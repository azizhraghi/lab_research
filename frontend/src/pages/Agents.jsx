import React, { useState } from "react";
import { RefreshCw, Play, Pause, Activity } from "lucide-react";
import { agents } from "../mockData";

export default function Agents() {
  const [selected, setSelected] = useState(null);
  const statusConfig = {
    active: { color: "bg-emerald-100 text-emerald-700", dot: "bg-emerald-500 animate-pulse", label: "Active" },
    running: { color: "bg-blue-100 text-blue-700", dot: "bg-blue-500 animate-pulse", label: "Running" },
    idle: { color: "bg-amber-100 text-amber-700", dot: "bg-amber-500", label: "Idle" },
  };

  return (
    <div className="p-6 overflow-y-auto h-full scrollbar-hide">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
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
