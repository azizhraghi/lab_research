export default function StatCard({ icon: Icon, label, value, accent = "var(--c-primary)" }) {
  return (
    <div className="stat-card" style={{ "--accent": accent }}>
      <div className="stat-card__icon">
        <Icon size={22} />
      </div>
      <div className="stat-card__body">
        <span className="stat-card__value">{value}</span>
        <span className="stat-card__label">{label}</span>
      </div>
    </div>
  );
}
