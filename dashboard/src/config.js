// ⚠️ CẤU HÌNH: thay thế bằng URL bucket S3 thực tế của bạn
// Ví dụ: https://my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an.s3.ap-southeast-1.amazonaws.com
export const S3_BASE_URL = import.meta.env.VITE_S3_BASE_URL || 
  'https://my-nasdaq-stock-processed-2026-430970051812-ap-southeast-1-an.s3.ap-southeast-1.amazonaws.com'

export const API_PATHS = {
  latest:        () => `${S3_BASE_URL}/predictions/latest.json`,
  dailyAll:      (date) => `${S3_BASE_URL}/predictions/${date}/all.json`,
  symbolHistory: (symbol) => `${S3_BASE_URL}/predictions/symbols/${symbol}/history.json`,
}

export const COLORS = {
  bullish:    '#10b981',
  bearish:    '#ef4444',
  neutral:    '#6b7280',
  primary:    '#3b82f6',
  primaryGlow:'rgba(59,130,246,0.4)',
  accent:     '#8b5cf6',
  warning:    '#f59e0b',
}
