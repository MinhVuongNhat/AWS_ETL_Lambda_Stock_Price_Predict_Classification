/* Gauge SVG Circle dự đoán */
import { COLORS } from '../config'

export default function PredictionGauge({ probability, prediction }) {
  const pct       = Math.round(probability * 100)
  const isBull    = prediction === 1
  const color     = isBull ? COLORS.bullish : COLORS.bearish
  const radius    = 68
  const circ      = 2 * Math.PI * radius
  const filled    = (pct / 100) * circ
  const gapColor  = 'rgba(255,255,255,0.08)'

  return (
    <div className="gauge-card glass">
      <p className="section-title" style={{ marginBottom: 0 }}>📡 Dự đoán mới nhất</p>

      <div className="gauge-circle">
        <svg width="160" height="160" viewBox="0 0 160 160">
          {/* Track */}
          <circle
            cx="80" cy="80" r={radius}
            fill="none" stroke={gapColor}
            strokeWidth="12"
          />
          {/* Progress */}
          <circle
            cx="80" cy="80" r={radius}
            fill="none" stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circ - filled}`}
            style={{ transition: 'stroke-dasharray 1s ease-out, stroke 0.4s' }}
          />
        </svg>

        <div className="gauge-text">
          <span className="gauge-pct" style={{ color }}>{pct}%</span>
          <span className="gauge-label">xác suất tăng</span>
        </div>
      </div>

      <span
        className="gauge-signal"
        style={{
          color,
          background: isBull ? COLORS.bullish + '18' : COLORS.bearish + '18',
          border: `1px solid ${color}44`
        }}
      >
        {isBull ? '▲ BULLISH — NÊN MUA' : '▼ BEARISH — NÊN BÁN'}
      </span>
    </div>
  )
}
