import { useEffect, useState } from "react";
import { Search, Activity, Filter } from "lucide-react";
import ArticleCard from "../components/ArticleCard";
import { veille } from "../lib/api";

export default function Veille() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    veille
      .listArticles()
      .then(setArticles)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = articles.filter(
    (a) =>
      a.title.toLowerCase().includes(search.toLowerCase()) ||
      a.abstract?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="page-loader">
        <Activity size={32} className="spin" />
        <span>Loading articles…</span>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <h2 className="page-title">Agent Veille</h2>
        <p className="page-subtitle">
          Scientific articles collected and enriched by AI
        </p>
      </header>

      <div className="toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search articles…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
          <span className="toolbar__count" style={{marginRight: '15px'}}>
            {filtered.length} article{filtered.length !== 1 ? "s" : ""}
          </span>
          <button className="btn btn-secondary" onClick={() => {
            veille.addSource({
              name: "ArXiv Hydrology & Digital Twins",
              type: "rss",
              url: "http://export.arxiv.org/api/query?search_query=all:hydrology+AND+all:twin&start=0&max_results=3"
            }).then(() => alert("Source added! Click 'Run Collection' to scrape.")).catch(e => alert(e));
          }}>
            Add Hydrology Source
          </button>
          <button className="btn btn-primary" onClick={() => {
            setLoading(true);
            veille.trigger().then(() => {
              alert("Collection finished!");
              return veille.listArticles();
            }).then(setArticles).catch(e => alert(e)).finally(() => setLoading(false));
          }}>
            Run Collection
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {filtered.length === 0 ? (
        <div className="empty-state">
          <Filter size={40} />
          <h3>No articles found</h3>
          <p>
            {articles.length === 0
              ? "The agent hasn't collected any articles yet. Trigger a collection from the backend."
              : "No articles match your search."}
          </p>
        </div>
      ) : (
        <div className="article-grid">
          {filtered.map((a) => (
            <ArticleCard key={a.id} article={a} />
          ))}
        </div>
      )}
    </div>
  );
}
