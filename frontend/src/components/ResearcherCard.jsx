import { useState } from "react";
import { Mail, Building2, Download } from "lucide-react";
import { biblio } from "../lib/api";

export default function ResearcherCard({ researcher }) {
  const [downloading, setDownloading] = useState(false);
  const hIndex = researcher.indicators?.find((indicator) => indicator.metric_name === "h_index")?.value ?? "-";
  const totalCitations = researcher.indicators?.find((indicator) => indicator.metric_name === "total_citations")?.value ?? "-";
  const pubCount = researcher.publications?.length ?? 0;

  const downloadCv = async () => {
    setDownloading(true);
    try {
      const { blob, filename } = await biblio.downloadCV(researcher.id);
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(href);
    } catch (error) {
      window.alert(error.message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="researcher-card">
      <div className="researcher-card__avatar">
        {researcher.name
          .split(" ")
          .map((name) => name[0])
          .join("")
          .slice(0, 2)
          .toUpperCase()}
      </div>

      <div className="researcher-card__info">
        <h3 className="researcher-card__name">{researcher.name}</h3>
        <span className="researcher-card__role">
          <Building2 size={13} /> {researcher.role} - {researcher.department}
        </span>
        <span className="researcher-card__email">
          <Mail size={13} /> {researcher.email}
        </span>
      </div>

      <div className="researcher-card__metrics">
        <div className="metric-pill">
          <span className="metric-pill__value">{hIndex}</span>
          <span className="metric-pill__label">h-index</span>
        </div>
        <div className="metric-pill">
          <span className="metric-pill__value">{totalCitations}</span>
          <span className="metric-pill__label">Citations</span>
        </div>
        <div className="metric-pill">
          <span className="metric-pill__value">{pubCount}</span>
          <span className="metric-pill__label">Pubs</span>
        </div>
      </div>

      <div className="researcher-card__actions">
        <button type="button" className="btn btn--sm" onClick={downloadCv} disabled={downloading}>
          <Download size={14} /> {downloading ? "Preparing..." : "CV"}
        </button>
      </div>
    </div>
  );
}