import React from "react";
import { Eye, BookMarked, Share2, ExternalLink, Brain } from "lucide-react";

export default function Watch() {
  const papers = [
    { id: 1, title: "Artificial Intelligence in Hydrological Forecasting: A Systematic Review", source: "Nature Water", date: "Sep 2, 2024", relevance: 98, tags: ["AI", "Hydrology"], summary: "Comprehensive meta-analysis of 847 AI-based hydrological models published 2018-2024, identifying transformer architectures as dominant paradigm." },
    { id: 2, title: "Digital Twin Applications in Climate Adaptation: Emerging Frameworks", source: "Nature Climate Change", date: "Sep 1, 2024", relevance: 94, tags: ["Digital Twins", "Climate"], summary: "Reviews 156 digital twin implementations for climate adaptation, highlighting real-time data assimilation as critical success factor." },
    { id: 3, title: "IoT-Based Environmental Monitoring at Scale: Lessons from 50 Deployments", source: "Environmental Science & Technology", date: "Aug 30, 2024", relevance: 89, tags: ["IoT", "Monitoring"], summary: "Synthesizes operational data from 50 large-scale IoT deployments across 22 countries, proposing unified data quality framework." },
    { id: 4, title: "Groundwater Depletion Under SSP Scenarios: GRACE-FO Satellite Analysis", source: "Geophysical Research Letters", date: "Aug 29, 2024", relevance: 92, tags: ["Groundwater", "Remote Sensing"], summary: "GRACE-FO data reveals 340 km³/yr global groundwater depletion acceleration under SSP3-7.0, exceeding IPCC projections by 28%." },
  ];

  return (
    <div className="p-6 space-y-5 overflow-y-auto h-full scrollbar-hide">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground font-jakarta">Scientific Watch</h2>
          <p className="text-sm text-muted-foreground">847 papers scanned today · 12 high-relevance alerts · AI-curated</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-primary font-semibold bg-primary/8 px-3 py-1.5 rounded-xl">
          <Eye size={14} /> Watched: 34 keywords
        </div>
      </div>

      {/* Trending topics */}
      <div className="bg-gradient-to-br from-[#0F3D2E] to-[#0B6E4F] rounded-2xl p-5 text-white">
        <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-3">AI-Detected Trending Topics - This Week</p>
        <div className="flex flex-wrap gap-2">
          {["Foundation Models for Climate", "Digital Twin Calibration", "GRACE-FO Groundwater", "Transformer-based Hydrology", "Federated IoT Learning", "Scenario-Based Risk", "LLM for Scientific Literature"].map(t => (
            <span key={t} className="px-3 py-1.5 bg-white/10 border border-white/15 rounded-full text-xs font-medium backdrop-blur-sm hover:bg-white/20 cursor-pointer transition-colors">
              {t}
            </span>
          ))}
        </div>
      </div>

      {/* Watch Feed */}
      <div className="space-y-4">
        {papers.map(p => (
          <div key={p.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md transition-all group">
            <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded-full">Score: {p.relevance}</span>
                  <span className="text-[10px] font-semibold text-foreground">{p.source}</span>
                  <span className="text-[10px] text-muted-foreground">{p.date}</span>
                </div>
                <h3 className="text-sm font-bold text-foreground mb-2 leading-snug group-hover:text-primary transition-colors">{p.title}</h3>
                <p className="text-xs text-muted-foreground mb-3 leading-relaxed">{p.summary}</p>
                <div className="flex flex-wrap gap-1">
                  {p.tags.map(t => <span key={t} className="px-2 py-0.5 bg-muted text-muted-foreground text-[10px] rounded-md">{t}</span>)}
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mt-4 pt-4 border-t border-border gap-4 sm:gap-0">
              <div className="flex items-center gap-4">
                <button className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors"><BookMarked size={12} /> Save</button>
                <button className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors"><Share2 size={12} /> Share</button>
                <button className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-primary transition-colors"><ExternalLink size={12} /> Full Paper</button>
              </div>
              <div className="sm:ml-auto">
                <button className="w-full sm:w-auto flex items-center justify-center gap-1 text-[10px] font-semibold text-white bg-primary px-3 py-1.5 sm:py-1 rounded-lg hover:bg-primary/90 transition-colors">
                  <Brain size={11} /> AI Summary
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
