import { Calendar, Tag, ExternalLink } from "lucide-react";

export default function ArticleCard({ article }) {
  const date = article.published_at
    ? new Date(article.published_at).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "Date inconnue";

  return (
    <div className="article-card">
      <div className="article-card__header">
        <h3 className="article-card__title">{article.title}</h3>
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="article-card__link"
            title="Open source"
          >
            <ExternalLink size={14} />
          </a>
        )}
      </div>

      {article.abstract && (
        <p className="article-card__abstract">
          {article.abstract.length > 200
            ? article.abstract.slice(0, 200) + "…"
            : article.abstract}
        </p>
      )}

      <div className="article-card__meta">
        <span className="article-card__date">
          <Calendar size={13} />
          {date}
        </span>

        {article.tags?.length > 0 && (
          <div className="article-card__tags">
            {article.tags.slice(0, 4).map((t, i) => (
              <span key={i} className="tag-badge">
                <Tag size={10} />
                {t.tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {article.summaries?.length > 0 && (
        <details className="article-card__summary-toggle">
          <summary>AI Summary</summary>
          <p className="article-card__summary-text">
            {article.summaries[0].summary_text}
          </p>
        </details>
      )}
    </div>
  );
}
