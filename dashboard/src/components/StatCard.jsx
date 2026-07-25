/* StatCard — hiển thị 1 số metric */
export default function StatCard({ label, value, sub, colorClass = '', icon }) {
  return (
    <div className={`stat-card glass ${colorClass}`}>
      <div className="label">{icon && <span>{icon} </span>}{label}</div>
      <div className="value">{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  )
}
