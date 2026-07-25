import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, ReferenceLine
} from 'recharts'
import { COLORS } from '../config'

/* ── Custom Tooltip ─────────────────────────────────────────── */
function CustomTooltip({ active, payload, label, isBull }) {
  if (!active || !payload?.length) return null
  const val = payload[0].value
  return (
    <div style={{
      background: 'rgba(13,21,38,0.95)',
      border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 10,
      padding: '0.6rem 1rem',
      fontSize: '0.85rem'
    }}>
      <p style={{ color: '#94a3b8', marginBottom: 2 }}>{label}</p>
      <p style={{ color: isBull ? COLORS.bullish : COLORS.bearish, fontWeight: 700 }}>
        {val.toFixed(1)}%
      </p>
    </div>
  )
}

/* ── Top 10 Bar Chart (Horizontal) ─────────────────────────── */
export function HBarChart({ data, colorKey = 'bull' }) {
  const isBull  = colorKey === 'bull'
  const color   = isBull ? COLORS.bullish : COLORS.bearish
  const mapped  = data.map(d => ({
    name: d.Symbol,
    pct:  isBull
      ? parseFloat((d.Probability * 100).toFixed(1))
      : parseFloat(((1 - d.Probability) * 100).toFixed(1))
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={mapped} layout="vertical" margin={{ left: 10, right: 30, top: 5, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
        <XAxis
          type="number" domain={[0, 100]}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          tickFormatter={v => `${v}%`}
          axisLine={false} tickLine={false}
        />
        <YAxis
          type="category" dataKey="name"
          tick={{ fill: '#f1f5f9', fontSize: 11, fontWeight: 600 }}
          axisLine={false} tickLine={false} width={52}
        />
        <Tooltip content={<CustomTooltip isBull={isBull} />} />
        <Bar dataKey="pct" radius={[0, 5, 5, 0]} maxBarSize={18}>
          {mapped.map((_, i) => (
            <Cell key={i} fill={color} fillOpacity={0.8 - i * 0.05} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/* ── Donut Chart Bullish/Bearish ────────────────────────────── */
import { PieChart, Pie, Cell as PieCell, Legend } from 'recharts'

export function DonutChart({ bullCount, bearCount }) {
  const data = [
    { name: 'Bullish', value: bullCount, color: COLORS.bullish },
    { name: 'Bearish', value: bearCount, color: COLORS.bearish },
  ]
  const total = bullCount + bearCount
  const pct   = total > 0 ? ((bullCount / total) * 100).toFixed(1) : 0

  return (
    <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <PieChart width={200} height={200}>
        <Pie
          data={data} cx="50%" cy="50%"
          innerRadius={60} outerRadius={85}
          dataKey="value" startAngle={90} endAngle={-270}
          strokeWidth={0}
        >
          {data.map((d, i) => <PieCell key={i} fill={d.color} fillOpacity={0.9} />)}
        </Pie>
      </PieChart>
      {/* Center text */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center', pointerEvents: 'none'
      }}>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: COLORS.bullish }}>{pct}%</div>
        <div style={{ fontSize: '0.65rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Bullish</div>
      </div>
      <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem' }}>
        {data.map(d => (
          <span key={d.name} style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: d.color }} />
            <span style={{ color: '#94a3b8' }}>{d.name}</span>
            <span style={{ fontWeight: 700 }}>{d.value}</span>
          </span>
        ))}
      </div>
    </div>
  )
}

/* ── Symbol Probability Line Chart ─────────────────────────── */
export function ProbLineChart({ data }) {
  const formatted = data.map(d => ({
    date: d.Date,
    prob: parseFloat((d.Probability * 100).toFixed(2)),
    pred: d.Prediction
  }))

  const dotColor = (entry) => entry.pred === 1 ? COLORS.bullish : COLORS.bearish

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={formatted} margin={{ left: 0, right: 20, top: 10, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#94a3b8', fontSize: 10 }}
          tickFormatter={d => d.slice(5)}  /* MM-DD */
          axisLine={false} tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#94a3b8', fontSize: 10 }}
          tickFormatter={v => `${v}%`}
          axisLine={false} tickLine={false} width={40}
        />
        <ReferenceLine y={50} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
        <Tooltip
          formatter={v => [`${v.toFixed(2)}%`, 'Xác suất Tăng']}
          labelFormatter={l => `Ngày ${l}`}
          contentStyle={{
            background: 'rgba(13,21,38,0.95)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: 10,
            fontSize: '0.85rem'
          }}
        />
        <Line
          type="monotone" dataKey="prob"
          stroke={COLORS.primary} strokeWidth={2.5} dot={false}
          activeDot={{ r: 5, fill: COLORS.primary }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

/* ── Symbol Prediction Bar Chart (màu theo tín hiệu) ────────── */
export function PredBarChart({ data }) {
  const formatted = data.map(d => ({
    date: d.Date.slice(5),  /* MM-DD */
    prob: parseFloat((d.Probability * 100).toFixed(2)),
    pred: d.Prediction
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={formatted} margin={{ left: 0, right: 10, top: 5, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }}
          axisLine={false} tickLine={false} interval="preserveStartEnd"
        />
        <YAxis
          domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }}
          tickFormatter={v => `${v}%`} axisLine={false} tickLine={false} width={36}
        />
        <Tooltip
          formatter={v => [`${v}%`, 'Xác suất Tăng']}
          contentStyle={{
            background: 'rgba(13,21,38,0.95)',
            border: '1px solid rgba(255,255,255,0.12)',
            borderRadius: 10, fontSize: '0.85rem'
          }}
        />
        <Bar dataKey="prob" radius={[3, 3, 0, 0]} maxBarSize={20}>
          {formatted.map((d, i) => (
            <Cell key={i} fill={d.pred === 1 ? COLORS.bullish : COLORS.bearish} fillOpacity={0.8} />
          ))}
        </Bar>
        <ReferenceLine y={50} stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" />
      </BarChart>
    </ResponsiveContainer>
  )
}
