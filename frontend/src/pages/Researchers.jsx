import React from "react";
import { Plus, ExternalLink } from "lucide-react";
import { researchers } from "../mockData";

export default function Researchers() {
  return (
    <div className="p-6 space-y-5 h-full overflow-y-auto scrollbar-hide">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Research Team</h2>
          <p className="text-sm text-muted-foreground">84 researchers · 12 departments · 6 countries</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white text-xs font-semibold rounded-xl">
          <Plus size={14} />Add Researcher
        </button>
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
