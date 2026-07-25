import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { API_PATHS, COLORS } from '../config'
import StatCard from '../components/StatCard'
import TopList from '../components/TopList'
import { HBarChart, DonutChart } from '../components/Charts'

const PAGE_SIZE = 20

export default function DashboardPage() {
  const [data,    setData]    = useState(null)
  const [allData, setAllData] = useState([])
  const [error,   setError]   = useState(null)
  const [search,  setSearch]  = useState('')
  const [page,    setPage]    = useState(1)
  const [sortKey, setSortKey] = useState('Probability')
  const [sortAsc, setSortAsc] = useState(false)

  useEffect(() => {
    fetch(API_PATHS.latest())
      .then(r => r.json())
      .then(json => {
        setData(json)
        // Carregar all predictions for the table
        return fetch(API_PATHS.dailyAll(json.date))
      })
      .then(r => r.json())
      .then(arr => setAllData(arr))
      .catch(e => setError(e.message))
  }, [])

  /* ── Search + Sort + Paginate ── */
  const filtered = useMemo(() => {
    let rows = allData
    if (search.trim()) {
      const q = search.toUpperCase()
      rows = rows.filter(r => r.Symbol.includes(q))
    }
    rows = [...rows].sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey]
      return sortAsc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1)
    })
    return rows
  }, [allData, search, sortKey, sortAsc])

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const pageData   = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleSort = (key) => {
    if (sortKey === key) setSortAsc(!sortAsc)
    else { setSortKey(key); setSortAsc(false) }
    setPage(1)
  }

  const sortIcon = (key) => sortKey === key ? (sortAsc ? ' ↑' : ' ↓') : ''

  if (error) return (
    <div className="page error-wrap">
      <h3>❌ Không tải được dữ liệu</h3>
      <p>{error}</p>
      <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#94a3b8' }}>
        Kiểm tra: (1) S3 bucket đã bật public access, (2) CORS đã được cấu hình,<br/>
        (3) Cập nhật <code>VITE_S3_BASE_URL</code> trong file <code>.env</code>
      </p>
    </div>
  )

  if (!data) return (
    <div className="page loading-wrap">
      <div className="spinner" />
      <span>Đang tải dữ liệu từ S3...</span>
    </div>
  )

  return (
    <div className="page">
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.2rem' }}>
            📊 Dashboard — Dự đoán Hàng Ngày
          </h2>
          <p className="text-muted text-sm">
            Ngày: <strong style={{ color: '#f1f5f9' }}>{data.date}</strong>
            &nbsp;&nbsp;·&nbsp;&nbsp;
            Cập nhật: {new Date(data.updated_at).toLocaleString('vi-VN')}
          </p>
        </div>
      </div>

      {/* ── Stat Cards ── */}
      <div className="stats-row">
        <StatCard label="Tổng Mã Dự Đoán" value={data.total.toLocaleString()} icon="🏦" />
        <StatCard label="Tín Hiệu Tăng" value={data.bullish_count} colorClass="stat-bull"
          sub={`${data.bullish_pct}% tổng số mã`} icon="🟢" />
        <StatCard label="Tín Hiệu Giảm" value={data.bearish_count} colorClass="stat-bear"
          sub={`${(100 - data.bullish_pct).toFixed(1)}% tổng số mã`} icon="🔴" />
        <StatCard label="Ngày Dự Đoán" value={data.date} colorClass="stat-primary" icon="📅" />
      </div>

      {/* ── Top 10 Lists ── */}
      <div className="lists-grid mb-3">
        <TopList
          title="Top 10 — Xác Suất Tăng Cao Nhất"
          items={data.top10}
          colorKey="bull"
          icon="🏆"
        />
        <TopList
          title="Top 10 — Xác Suất Giảm Cao Nhất"
          items={data.bottom10}
          colorKey="bear"
          icon="⚠️"
        />
      </div>

      {/* ── Charts ── */}
      <div className="charts-row mb-3">
        <div className="chart-card glass">
          <p className="section-title">📈 Biểu Đồ Top 10 Bullish</p>
          <HBarChart data={data.top10} colorKey="bull" />
        </div>
        <div className="chart-card glass">
          <p className="section-title">📉 Biểu Đồ Top 10 Bearish</p>
          <HBarChart data={data.bottom10} colorKey="bear" />
        </div>
        <div className="chart-card glass" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
          <p className="section-title">🥧 Tỉ Lệ Thị Trường</p>
          <DonutChart bullCount={data.bullish_count} bearCount={data.bearish_count} />
        </div>
      </div>

      {/* ── All Predictions Table ── */}
      <div className="search-results-card glass">
        <div className="flex items-center justify-between mb-2" style={{ flexWrap: 'wrap', gap: '0.75rem' }}>
          <p className="section-title" style={{ marginBottom: 0 }}>
            🔍 Toàn Bộ Dự Đoán ({filtered.length} mã)
          </p>
          <div className="search-input-wrap">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
            </svg>
            <input
              className="search-input"
              type="text"
              placeholder="Lọc theo mã..."
              value={search}
              onChange={e => { setSearch(e.target.value.toUpperCase()); setPage(1) }}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table className="predictions-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('Symbol')}>Mã CK{sortIcon('Symbol')}</th>
                <th>Tín Hiệu</th>
                <th onClick={() => handleSort('Probability')}>Xác Suất Tăng{sortIcon('Probability')}</th>
                <th>Thanh đo</th>
                <th>Xem chi tiết</th>
              </tr>
            </thead>
            <tbody>
              {pageData.map(row => {
                const isBull = row.Prediction === 1
                const pct    = (row.Probability * 100).toFixed(1)
                const color  = isBull ? COLORS.bullish : COLORS.bearish
                return (
                  <tr key={row.Symbol}>
                    <td style={{ fontWeight: 700 }}>{row.Symbol}</td>
                    <td>
                      <span className={`badge ${isBull ? 'badge-bull' : 'badge-bear'}`}>
                        {isBull ? '▲ BULLISH' : '▼ BEARISH'}
                      </span>
                    </td>
                    <td style={{ color, fontWeight: 600 }}>{pct}%</td>
                    <td style={{ width: 120 }}>
                      <div className="ticker-bar-wrap" style={{ width: 100 }}>
                        <div className="ticker-bar" style={{ width: `${row.Probability * 100}%`, backgroundColor: color }} />
                      </div>
                    </td>
                    <td>
                      <Link
                        to={`/symbol/${row.Symbol}`}
                        style={{
                          color: COLORS.primary,
                          textDecoration: 'none',
                          fontSize: '0.82rem',
                          fontWeight: 600,
                          padding: '3px 10px',
                          border: `1px solid ${COLORS.primary}44`,
                          borderRadius: 6,
                          background: COLORS.primary + '10'
                        }}
                      >
                        Chi tiết →
                      </Link>
                    </td>
                  </tr>
                )
              })}
              {pageData.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>
                  Không tìm thấy mã "{search}"
                </td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button className="page-btn" onClick={() => setPage(1)} disabled={page === 1}>«</button>
            <button className="page-btn" onClick={() => setPage(p => p - 1)} disabled={page === 1}>‹</button>
            {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
              const p = Math.max(1, Math.min(page - 3, totalPages - 6)) + i
              if (p < 1 || p > totalPages) return null
              return (
                <button
                  key={p}
                  className={`page-btn ${p === page ? 'active' : ''}`}
                  onClick={() => setPage(p)}
                >{p}</button>
              )
            })}
            <button className="page-btn" onClick={() => setPage(p => p + 1)} disabled={page === totalPages}>›</button>
            <button className="page-btn" onClick={() => setPage(totalPages)} disabled={page === totalPages}>»</button>
          </div>
        )}
      </div>
    </div>
  )
}
