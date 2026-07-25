import { Link } from 'react-router-dom'
import { COLORS } from '../config'

/**
 * Danh sách top 10 / bottom 10 — hiển thị kèm thanh xác suất và badge
 */
export default function TopList({ title, items = [], colorKey = 'bull', icon }) {
  const isBull = colorKey === 'bull'
  const color  = isBull ? COLORS.bullish : COLORS.bearish

  return (
    <div className="list-card glass">
      <p className="section-title">
        <span>{icon}</span> {title}
      </p>

      <ul className="ticker-list">
        {items.map((item, idx) => {
          const prob    = (item.Probability * 100).toFixed(1)
          const barPct  = isBull ? item.Probability * 100 : (1 - item.Probability) * 100

          return (
            <Link
              key={item.Symbol}
              to={`/symbol/${item.Symbol}`}
              className="ticker-item"
            >
              <span className="ticker-rank">#{idx + 1}</span>

              <span className="ticker-symbol">{item.Symbol}</span>

              <span className="ticker-bar-wrap">
                <span
                  className="ticker-bar"
                  style={{ width: `${barPct}%`, backgroundColor: color }}
                />
              </span>

              <span className="ticker-prob" style={{ color }}>
                {isBull ? prob : (100 - item.Probability * 100).toFixed(1)}%
              </span>

              <span className={`badge ${isBull ? 'badge-bull' : 'badge-bear'}`}>
                {isBull ? '▲' : '▼'}
              </span>
            </Link>
          )
        })}
      </ul>
    </div>
  )
}
