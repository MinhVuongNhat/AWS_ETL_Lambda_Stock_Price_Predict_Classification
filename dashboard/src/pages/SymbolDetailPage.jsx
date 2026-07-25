import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { API_PATHS, COLORS } from '../config'
import PredictionGauge from '../components/PredictionGauge'
import { ProbLineChart, PredBarChart } from '../components/Charts'

export default function SymbolDetailPage() {
  const { symbol } = useParams()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(API_PATHS.symbolHistory(symbol))
      .then(r => {
        if (!r.ok) throw new Error(`Mã ${symbol} không có dữ liệu (${r.status})`)
        return r.json()
      })
      .then(data => { setHistory(data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [symbol])

  /* ── Tính toán thống kê ── */
  const stats = useMemo(() => {
    if (!history.length) return null
    const latest   = history[history.length - 1]
    const bullDays = history.filter(h => h.Prediction === 1).length
    const avgProb  = history.reduce((s, h) => s + h.Probability, 0) / history.length

    // Accuracy: so Prediction với ngày kế tiếp thực tế
    // (chỉ tính được nếu có ActualLabel — field tùy chọn)
    const withActual = history.filter(h => h.ActualLabel !== undefined)
    const correct    = withActual.filter(h => h.ActualLabel === h.Prediction).length
    const accuracy   = withActual.length > 0 ? (correct / withActual.length) * 100 : null

    return { latest, bullDays, avgProb, accuracy, withActual: withActual.length }
  }, [history])

  /* ── Streak: số ngày liên tiếp cùng hướng ── */
  const streak = useMemo(() => {
    if (!history.length) return 0
    const last = history[history.length - 1].Prediction
    let count  = 0
    for (let i = history.length - 1; i >= 0; i--) {
      if (history[i].Prediction === last) count++
      else break
    }
    return count
  }, [history])

  if (loading) return (
    <div className="page loading-wrap">
      <div className="spinner" />
      <span>Đang tải lịch sử {symbol}...</span>
    </div>
  )

  if (error || !history.length) return (
    <div className="page error-wrap">
      <h3>❌ Không tìm thấy dữ liệu</h3>
      <p>{error || `Không có lịch sử dự đoán cho mã ${symbol}`}</p>
      <Link to="/" className="back-btn" style={{ marginTop: '1.5rem', display: 'inline-flex' }}>
        ← Về Dashboard
      </Link>
    </div>
  )

  const { latest, bullDays, avgProb, accuracy } = stats

  return (
    <div className="page">
      {/* ── Header ── */}
      <div className="detail-header">
        <Link to="/" className="back-btn">← Về Dashboard</Link>
        <span className="detail-symbol">{symbol}</span>
        <span
          className={`badge ${latest.Prediction === 1 ? 'badge-bull' : 'badge-bear'}`}
          style={{ fontSize: '0.9rem', padding: '4px 14px' }}
        >
          {latest.Prediction === 1 ? '▲ BULLISH' : '▼ BEARISH'} ngày {latest.Date}
        </span>
      </div>

      {/* ── Stat Cards ── */}
      <div className="stats-row" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card glass">
          <div className="label">📅 Ngày Mới Nhất</div>
          <div className="value" style={{ fontSize: '1.4rem' }}>{latest.Date}</div>
        </div>
        <div className="stat-card glass stat-bull">
          <div className="label">📊 Tỉ Lệ Bullish</div>
          <div className="value">{((bullDays / history.length) * 100).toFixed(0)}%</div>
          <div className="sub">{bullDays}/{history.length} ngày tăng</div>
        </div>
        <div className="stat-card glass stat-primary">
          <div className="label">🎯 Xác Suất TB</div>
          <div className="value">{(avgProb * 100).toFixed(1)}%</div>
          <div className="sub">trong {history.length} ngày gần nhất</div>
        </div>
        <div className="stat-card glass">
          <div className="label">🔥 Streak Hiện Tại</div>
          <div className="value" style={{ color: latest.Prediction === 1 ? COLORS.bullish : COLORS.bearish }}>
            {streak} ngày
          </div>
          <div className="sub">{latest.Prediction === 1 ? 'liên tiếp Bullish' : 'liên tiếp Bearish'}</div>
        </div>
        {accuracy !== null ? (
          <div className="stat-card glass">
            <div className="label">✅ Độ Chính Xác Thực Tế</div>
            <div className="value">{accuracy.toFixed(1)}%</div>
            <div className="sub">({stats.withActual} ngày có dữ liệu thực tế)</div>
          </div>
        ) : (
          <div className="stat-card glass">
            <div className="label">✅ Độ Chính Xác</div>
            <div className="value" style={{ fontSize: '1rem', color: '#94a3b8' }}>Chưa đủ dữ liệu</div>
            <div className="sub">Cần cột ActualLabel</div>
          </div>
        )}
      </div>

      {/* ── Gauge + Line Chart ── */}
      <div className="detail-grid">
        <div className="chart-card glass">
          <p className="section-title">📈 Lịch Sử Xác Suất Tăng — {history.length} Ngày Gần Nhất</p>
          <ProbLineChart data={history} />
          <p style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: '0.5rem' }}>
            Đường kẻ ngang là ngưỡng 50%. Điểm trên ngưỡng = dự đoán Tăng.
          </p>
        </div>
        <PredictionGauge
          probability={latest.Probability}
          prediction={latest.Prediction}
        />
      </div>

      {/* ── Bar Chart tín hiệu ── */}
      <div className="chart-card glass mb-3">
        <p className="section-title">🔁 Biểu Đồ Tín Hiệu Dự Đoán (Màu Theo Hướng)</p>
        <PredBarChart data={history} />
        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.8rem', color: '#94a3b8' }}>
          <span>
            <span style={{ display:'inline-block', width:10, height:10, background:COLORS.bullish, borderRadius:2, marginRight:5 }} />
            Bullish (Tăng)
          </span>
          <span>
            <span style={{ display:'inline-block', width:10, height:10, background:COLORS.bearish, borderRadius:2, marginRight:5 }} />
            Bearish (Giảm)
          </span>
        </div>
      </div>

      {/* ── History Table ── */}
      <div className="history-card glass">
        <p className="section-title">📋 Bảng Lịch Sử Chi Tiết</p>
        <div style={{ overflowX: 'auto' }}>
          <table className="predictions-table">
            <thead>
              <tr>
                <th>Ngày</th>
                <th>Tín Hiệu</th>
                <th>Xác Suất Tăng</th>
                <th>Thanh Đo</th>
                {history.some(h => h.ActualLabel !== undefined) && (
                  <th>Thực Tế</th>
                )}
              </tr>
            </thead>
            <tbody>
              {[...history].reverse().map(row => {
                const isBull = row.Prediction === 1
                const color  = isBull ? COLORS.bullish : COLORS.bearish
                const pct    = (row.Probability * 100).toFixed(2)
                return (
                  <tr key={row.Date}>
                    <td style={{ fontWeight: 600, color: '#94a3b8' }}>{row.Date}</td>
                    <td>
                      <span className={`badge ${isBull ? 'badge-bull' : 'badge-bear'}`}>
                        {isBull ? '▲ TĂNG' : '▼ GIẢM'}
                      </span>
                    </td>
                    <td style={{ color, fontWeight: 700 }}>{pct}%</td>
                    <td style={{ width: 120 }}>
                      <div className="ticker-bar-wrap" style={{ width: 100 }}>
                        <div className="ticker-bar" style={{ width: `${row.Probability * 100}%`, backgroundColor: color }} />
                      </div>
                    </td>
                    {row.ActualLabel !== undefined && (
                      <td>
                        {row.ActualLabel === row.Prediction
                          ? <span style={{ color: COLORS.bullish, fontWeight: 700 }}>✅ Đúng</span>
                          : <span style={{ color: COLORS.bearish, fontWeight: 700 }}>❌ Sai</span>
                        }
                      </td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
