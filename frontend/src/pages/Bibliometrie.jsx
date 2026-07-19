import { useEffect, useState } from "react";
import { Search, Activity, Users, UserPlus, X } from "lucide-react";
import ResearcherCard from "../components/ResearcherCard";
import { biblio } from "../lib/api";

export default function Bibliometrie() {
  const [researchers, setResearchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "", email: "", scholar_id: "", orcid_id: "",
    department: "", role: "Researcher"
  });
  const [submitting, setSubmitting] = useState(false);

  const reload = () =>
    biblio.listResearchers().then(setResearchers).catch((e) => setError(e.message));

  useEffect(() => {
    reload().finally(() => setLoading(false));
  }, []);

  const filtered = researchers.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.department?.toLowerCase().includes(search.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const clean = { ...formData };
      if (!clean.scholar_id) delete clean.scholar_id;
      if (!clean.orcid_id) delete clean.orcid_id;

      const res = await biblio.addResearcher(clean);
      setShowForm(false);
      setFormData({ name: "", email: "", scholar_id: "", orcid_id: "", department: "", role: "Researcher" });

      // If scholar_id was provided, sync publications
      if (formData.scholar_id) {
        try {
          await biblio.syncResearcher(res.id);
        } catch (syncErr) {
          console.warn("Sync warning:", syncErr);
        }
      }
      await reload();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="page-loader">
        <Activity size={32} className="spin" />
        <span>Loading researchers…</span>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <h2 className="page-title">Agent Bibliométrie</h2>
        <p className="page-subtitle">
          Researcher profiles, publications &amp; bibliometric indicators
        </p>
      </header>

      <div className="toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            type="text"
            placeholder="Search researchers…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
          <span className="toolbar__count" style={{marginRight: '15px'}}>
            {filtered.length} researcher{filtered.length !== 1 ? "s" : ""}
          </span>
          <button className="btn btn-primary" onClick={() => setShowForm(true)}>
            <UserPlus size={16} style={{marginRight: '6px'}} />
            Add Researcher
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* ── Add Researcher Modal ── */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Researcher</h3>
              <button className="btn-icon" onClick={() => setShowForm(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-grid">
                <div className="form-group">
                  <label>Full Name *</label>
                  <input required value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    placeholder="e.g. Lilia Romdhane" />
                </div>
                <div className="form-group">
                  <label>Email *</label>
                  <input required type="email" value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    placeholder="researcher@lab.org" />
                </div>
                <div className="form-group">
                  <label>Department *</label>
                  <input required value={formData.department}
                    onChange={(e) => setFormData({...formData, department: e.target.value})}
                    placeholder="e.g. Hydraulique" />
                </div>
                <div className="form-group">
                  <label>Role *</label>
                  <input required value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                    placeholder="e.g. Professeur" />
                </div>
                <div className="form-group">
                  <label>Google Scholar ID</label>
                  <input value={formData.scholar_id}
                    onChange={(e) => setFormData({...formData, scholar_id: e.target.value})}
                    placeholder="e.g. qc6CJjYAAAAJ (optional)" />
                </div>
                <div className="form-group">
                  <label>ORCID ID</label>
                  <input value={formData.orcid_id}
                    onChange={(e) => setFormData({...formData, orcid_id: e.target.value})}
                    placeholder="e.g. 0000-0002-1234-5678 (optional)" />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? "Adding..." : "Add Researcher"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="empty-state">
          <Users size={40} />
          <h3>No researchers found</h3>
          <p>
            {researchers.length === 0
              ? "No researcher profiles have been created yet. Click 'Add Researcher' above."
              : "No researchers match your search."}
          </p>
        </div>
      ) : (
        <div className="researcher-grid">
          {filtered.map((r) => (
            <ResearcherCard key={r.id} researcher={r} />
          ))}
        </div>
      )}
    </div>
  );
}
