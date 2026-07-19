import React, { useState } from "react";
import { Download, Bookmark, Search, ExternalLink, Award, Star, TrendingUp, Globe } from "lucide-react";
import { publications } from "../mockData";

export default function Publications() {
  const [filter, setFilter] = useState("all");
  const tags = ["All", "AI", "Hydrology", "Climate", "Remote Sensing", "Digital Twins", "IoT"];

  return (
    <div className="p-6 space-y-5 h-full overflow-y-auto scrollbar-hide">
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
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
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
        <div className="ml-auto flex items-center gap-2 w-full sm:w-auto mt-3 sm:mt-0">
          <div className="relative w-full sm:w-auto">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input placeholder="Search publications..." className="pl-8 pr-3 py-1.5 text-xs bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/30 w-full sm:w-52" />
          </div>
        </div>
      </div>

      {/* Publication cards */}
      <div className="space-y-4">
        {publications.map(pub => (
          <div key={pub.id} className="bg-card border border-border rounded-2xl p-5 hover:shadow-md hover:border-primary/20 transition-all group">
            <div className="flex flex-col sm:flex-row items-start justify-between gap-4">
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
              <div className="shrink-0 sm:text-right flex flex-row sm:flex-col items-center sm:items-end gap-3 sm:gap-0 mt-2 sm:mt-0">
                <div className="text-center sm:text-right">
                  <div className="text-2xl font-extrabold text-foreground font-jakarta">{pub.citations}</div>
                  <div className="text-[10px] text-muted-foreground">citations</div>
                </div>
                <div className="sm:mt-2 text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">IF {pub.impact}</div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mt-3 pt-3 border-t border-border gap-3 sm:gap-0">
              <div className="flex flex-wrap gap-1">
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
