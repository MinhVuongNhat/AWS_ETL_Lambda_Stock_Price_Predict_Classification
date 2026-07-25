"""
Nasdaq AI Stock Predictor — Streamlit Dashboard
Trang 1: Tổng quan hàng ngày + Bảng xếp hạng nên mua
Trang 2: Chi tiết từng mã — tìm kiếm, lịch sử, đồ thị, dự đoán
"""
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ── Cấu hình trang ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nasdaq AI Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── API Config ────────────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "https://<API_GATEWAY_ID>.execute-api.ap-southeast-1.amazonaws.com/prod"
)

# ── CSS Tuỳ chỉnh ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

/* Dark card */
.metric-card {
    background: rgba(30, 38, 60, 0.85);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}

/* Badge */
.badge-bull { color: #10b981; background: rgba(16,185,129,0.12);
              border: 1px solid rgba(16,185,129,0.3);
              padding: 3px 10px; border-radius: 6px; font-weight: 600; }
.badge-bear { color: #ef4444; background: rgba(239,68,68,0.12);
              border: 1px solid rgba(239,68,68,0.3);
              padding: 3px 10px; border-radius: 6px; font-weight: 600; }

/* Sidebar */
section[data-testid="stSidebar"] { background: #0d1117; }

/* Header */
.page-title { font-size: 2rem; font-weight: 700;
              background: linear-gradient(90deg,#60a5fa,#34d399);
              -webkit-background-clip: text; color: transparent; }
</style>
""", unsafe_allow_html=True)


# ── API helpers ───────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)  # cache 5 phút
def fetch_latest(limit: int = 200, filter_: str = "all") -> pd.DataFrame:
    try:
        resp = requests.get(
            f"{API_BASE_URL}/predictions/latest",
            params={"limit": limit, "filter": filter_},
            timeout=10
        )
        data = resp.json()
        items = data.get("predictions", [])
        if not items:
            return pd.DataFrame()
        df = pd.DataFrame(items)
        df["Probability"] = df["Probability"].astype(float)
        df["Prediction"]  = df["Prediction"].astype(int)
        df["Signal"]      = df["Prediction"].map({1: "🟢 Bullish", 0: "🔴 Bearish"})
        return df
    except Exception as e:
        st.error(f"❌ Lỗi API: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_symbol_history(symbol: str, days: int = 60) -> pd.DataFrame:
    try:
        resp = requests.get(
            f"{API_BASE_URL}/predictions/{symbol}",
            params={"days": days},
            timeout=10
        )
        if resp.status_code == 404:
            return pd.DataFrame()
        data = resp.json()
        history = data.get("history", [])
        if not history:
            return pd.DataFrame()
        df = pd.DataFrame(history)
        df["Probability"] = df["Probability"].astype(float)
        df["Prediction"]  = df["Prediction"].astype(int)
        df["Date"]        = pd.to_datetime(df["Date"])
        return df
    except Exception as e:
        st.error(f"❌ Lỗi API: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_symbol_stats(symbol: str) -> dict:
    try:
        resp = requests.get(f"{API_BASE_URL}/predictions/{symbol}/stats", timeout=10)
        if resp.status_code == 404:
            return {}
        return resp.json()
    except Exception as e:
        st.error(f"❌ Lỗi API: {e}")
        return {}


# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Nasdaq AI Predictor")
    st.markdown("---")
    page = st.radio(
        "Điều hướng",
        ["🏠 Tổng quan hàng ngày", "🔍 Chi tiết mã cổ phiếu"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("**Cài đặt**")
    show_bearish = st.checkbox("Hiện cả tín hiệu Bearish", value=False)
    top_n        = st.slider("Số mã hiển thị", 10, 100, 50, 5)
    st.markdown("---")
    st.markdown(
        f"<small>🔄 Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}</small>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# TRANG 1 — TỔNG QUAN HÀNG NGÀY
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Tổng quan hàng ngày":
    st.markdown('<p class="page-title">📊 Tổng Quan — AI Stock Predictor</p>', unsafe_allow_html=True)

    # Load data
    filter_param = "bullish" if not show_bearish else "all"
    with st.spinner("Đang tải dữ liệu từ API..."):
        df_all = fetch_latest(limit=500, filter_="all")

    if df_all.empty:
        st.warning("⚠️ Không có dữ liệu. Kiểm tra API Gateway và DynamoDB.")
        st.info(f"API URL hiện tại: `{API_BASE_URL}`\nHãy cập nhật biến `API_BASE_URL` trong file `dashboard/streamlit_app.py`.")
        st.stop()

    date_display = df_all["Date"].iloc[0] if "Date" in df_all.columns else "N/A"
    bull_df = df_all[df_all["Prediction"] == 1]
    bear_df = df_all[df_all["Prediction"] == 0]

    # ── Thẻ tổng quan ─────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📅 Ngày dự đoán", date_display)
    col2.metric("📊 Tổng số mã", len(df_all))
    col3.metric("🟢 Tín hiệu Tăng", len(bull_df), delta=f"{len(bull_df)/len(df_all)*100:.1f}%")
    col4.metric("🔴 Tín hiệu Giảm", len(bear_df))

    st.markdown("---")

    # ── Bảng xếp hạng nên mua ─────────────────────────────────────
    left, right = st.columns([3, 2])

    with left:
        st.subheader("🏆 Bảng Xếp Hạng Nên Mua (Xác Suất Tăng Cao Nhất)")

        display_df = bull_df.head(top_n)[["Symbol", "Signal", "Probability", "Date"]].copy()
        display_df["Probability %"] = (display_df["Probability"] * 100).map("{:.2f}%".format)
        display_df["Rank"] = range(1, len(display_df) + 1)
        display_df = display_df[["Rank", "Symbol", "Signal", "Probability %"]]

        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("#", width="small"),
                "Symbol": st.column_config.TextColumn("Mã CK", width="small"),
                "Signal": st.column_config.TextColumn("Tín hiệu"),
                "Probability %": st.column_config.TextColumn("Xác suất tăng", width="medium"),
            }
        )

    with right:
        st.subheader("📈 Phân Phối Xác Suất")
        fig_hist = px.histogram(
            df_all, x="Probability", nbins=40,
            color="Signal",
            color_discrete_map={"🟢 Bullish": "#10b981", "🔴 Bearish": "#ef4444"},
            title="Phân phối xác suất dự đoán",
            labels={"Probability": "Xác suất Tăng", "count": "Số mã"},
            template="plotly_dark"
        )
        fig_hist.update_layout(
            height=300, showlegend=True,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=40, b=20, l=0, r=0)
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        # Pie chart
        bull_count = len(bull_df)
        bear_count = len(bear_df)
        fig_pie = go.Figure(data=[go.Pie(
            labels=["Bullish 🟢", "Bearish 🔴"],
            values=[bull_count, bear_count],
            marker_colors=["#10b981", "#ef4444"],
            hole=0.55,
            textinfo="percent+label"
        )])
        fig_pie.update_layout(
            height=250,
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=20, b=0, l=0, r=0),
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Top 20 xác suất cao nhất ──────────────────────────────────
    if show_bearish:
        st.subheader("🔴 Top Tín Hiệu Bearish (Xác Suất Giảm Cao Nhất)")
        display_bear = bear_df.head(20)[["Symbol", "Probability"]].copy()
        display_bear["Xác suất Giảm %"] = ((1 - display_bear["Probability"]) * 100).map("{:.2f}%".format)
        display_bear = display_bear[["Symbol", "Xác suất Giảm %"]]
        st.dataframe(display_bear, use_container_width=True, hide_index=True)

    # ── Top 10 Bubble chart ────────────────────────────────────────
    st.markdown("---")
    st.subheader("🫧 Top 20 Bullish — Biểu đồ Bubble")
    top20 = bull_df.head(20).copy()
    top20["size"] = top20["Probability"] * 100
    fig_bubble = px.scatter(
        top20, x="Symbol", y="Probability",
        size="size", color="Probability",
        color_continuous_scale=["#f97316", "#10b981"],
        text="Symbol",
        title="Top 20 cổ phiếu có xác suất Tăng cao nhất",
        template="plotly_dark",
        labels={"Probability": "Xác suất Tăng"}
    )
    fig_bubble.update_traces(textposition="top center", textfont_size=11)
    fig_bubble.update_layout(
        height=400,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        xaxis_title="", yaxis_title="Xác suất Tăng",
        margin=dict(t=50, b=30)
    )
    st.plotly_chart(fig_bubble, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TRANG 2 — CHI TIẾT MÃ CỔ PHIẾU
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Chi tiết mã cổ phiếu":
    st.markdown('<p class="page-title">🔍 Chi Tiết Mã Cổ Phiếu</p>', unsafe_allow_html=True)

    # ── Tìm kiếm ──────────────────────────────────────────────────
    col_search, col_days = st.columns([3, 1])
    with col_search:
        symbol_input = st.text_input(
            "Nhập mã cổ phiếu (VD: AAPL, MSFT, NVDA)",
            placeholder="AAPL",
            help="Nhập mã ticker NASDAQ"
        ).strip().upper()
    with col_days:
        days_select = st.selectbox("Khoảng thời gian", [30, 60, 90, 180], index=1)

    if not symbol_input:
        st.info("⬆️ Nhập mã cổ phiếu để xem chi tiết.")
        st.stop()

    with st.spinner(f"Đang tải dữ liệu cho {symbol_input}..."):
        df_hist  = fetch_symbol_history(symbol_input, days=days_select)
        stats    = fetch_symbol_stats(symbol_input)

    if df_hist.empty:
        st.error(f"❌ Không tìm thấy dữ liệu cho mã **{symbol_input}**.")
        st.caption("Hãy kiểm tra mã cổ phiếu hoặc đảm bảo pipeline đã chạy và có dữ liệu trong DynamoDB.")
        st.stop()

    # ── Thẻ thống kê ──────────────────────────────────────────────
    latest = df_hist.iloc[-1]
    pred_emoji = "🟢 TĂNG" if latest["Prediction"] == 1 else "🔴 GIẢM"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📅 Dự đoán mới nhất", pred_emoji, help="Dự đoán ngày giao dịch tiếp theo")
    c2.metric("🎯 Xác suất Tăng", f"{latest['Probability']*100:.2f}%")
    c3.metric(
        "📊 Tỉ lệ Bullish (lịch sử)",
        f"{stats.get('bullish_rate', 0)*100:.1f}%",
        help=f"Trong {stats.get('total_predictions', 0)} ngày gần đây"
    )
    if stats.get("accuracy") is not None:
        c4.metric("✅ Độ chính xác thực tế", f"{stats['accuracy']*100:.1f}%",
                  help="Dựa trên kết quả thực tế đã có")
    else:
        c4.metric("✅ Độ chính xác", "N/A", help="Chưa đủ dữ liệu thực tế")

    st.markdown("---")

    # ── Biểu đồ Lịch sử Dự đoán ───────────────────────────────────
    st.subheader(f"📈 Biểu Đồ Xác Suất Tăng — {symbol_input}")

    fig_line = go.Figure()

    # Vùng tô màu theo ngưỡng 0.5
    fig_line.add_hrect(y0=0.5, y1=1.05, fillcolor="#10b981", opacity=0.06, layer="below", line_width=0)
    fig_line.add_hrect(y0=0.0, y1=0.5,  fillcolor="#ef4444", opacity=0.06, layer="below", line_width=0)

    # Đường ngưỡng 0.5
    fig_line.add_hline(y=0.5, line_dash="dash", line_color="#6b7280", line_width=1)

    # Đường xác suất
    colors = ["#10b981" if p >= 0.5 else "#ef4444" for p in df_hist["Probability"]]
    fig_line.add_trace(go.Scatter(
        x=df_hist["Date"], y=df_hist["Probability"],
        mode="lines+markers",
        name="Xác suất Tăng",
        line=dict(color="#60a5fa", width=2.5),
        marker=dict(color=colors, size=8, line=dict(color="white", width=1)),
        hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Xác suất: %{y:.3f}<extra></extra>"
    ))

    fig_line.update_layout(
        template="plotly_dark",
        height=380,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Ngày",
        yaxis_title="Xác suất Tăng",
        yaxis=dict(range=[0, 1], tickformat=".0%"),
        hovermode="x unified",
        margin=dict(t=20, b=40)
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # ── Biểu đồ Tín hiệu ──────────────────────────────────────────
    st.subheader("🔁 Lịch Sử Tín Hiệu Dự Đoán")

    df_hist["Prediction_Label"] = df_hist["Prediction"].map({1: "Tăng", 0: "Giảm"})
    fig_bar = px.bar(
        df_hist, x="Date", y="Probability",
        color="Prediction_Label",
        color_discrete_map={"Tăng": "#10b981", "Giảm": "#ef4444"},
        labels={"Probability": "Xác suất", "Date": "Ngày", "Prediction_Label": "Tín hiệu"},
        template="plotly_dark",
        barmode="relative"
    )
    fig_bar.update_layout(
        height=280,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 1], tickformat=".0%"),
        margin=dict(t=10, b=30),
        legend_title_text="Tín hiệu"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Bảng lịch sử chi tiết ─────────────────────────────────────
    st.subheader("📋 Bảng Lịch Sử Chi Tiết")

    df_display = df_hist[["Date", "Prediction_Label", "Probability"]].copy()
    df_display = df_display.sort_values("Date", ascending=False)
    df_display["Date"]        = df_display["Date"].dt.strftime("%d/%m/%Y")
    df_display["Probability"] = (df_display["Probability"] * 100).round(2)

    st.dataframe(
        df_display,
        use_container_width=True,
        height=350,
        hide_index=True,
        column_config={
            "Date":             st.column_config.TextColumn("Ngày"),
            "Prediction_Label": st.column_config.TextColumn("Dự đoán"),
            "Probability":      st.column_config.ProgressColumn(
                "Xác suất Tăng (%)", min_value=0, max_value=100, format="%.2f"
            ),
        }
    )

    # ── Nút dự báo tương lai ──────────────────────────────────────
    st.markdown("---")
    st.subheader("🔮 Dự Báo Ngày Giao Dịch Tiếp Theo")

    if st.button(f"🔮 Dự báo ngày tiếp theo cho {symbol_input}", type="primary", use_container_width=True):
        # Lấy dự đoán mới nhất từ API (đây chính là dự đoán cho ngày tiếp theo)
        st.cache_data.clear()
        df_refresh = fetch_symbol_history(symbol_input, days=1)
        if not df_refresh.empty:
            row = df_refresh.iloc[-1]
            pred   = int(row["Prediction"])
            prob   = float(row["Probability"])
            signal = "🟢 TĂNG" if pred == 1 else "🔴 GIẢM"

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                color = "#10b981" if pred == 1 else "#ef4444"
                st.markdown(
                    f"""<div style="background:rgba(30,38,60,0.8);border:1px solid {color};
                    border-radius:12px;padding:2rem;text-align:center;">
                    <div style="font-size:3rem;font-weight:700;color:{color}">{signal}</div>
                    <div style="font-size:1rem;color:#9ca3af;margin-top:0.5rem">
                    Dự đoán ngày giao dịch tiếp theo</div>
                    </div>""",
                    unsafe_allow_html=True
                )
            with col_r2:
                gauge_val = prob * 100
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=gauge_val,
                    title={"text": "Xác suất Tăng (%)"},
                    number={"suffix": "%", "font": {"size": 28}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar":  {"color": "#10b981" if prob >= 0.5 else "#ef4444"},
                        "steps": [
                            {"range": [0, 50],  "color": "rgba(239,68,68,0.15)"},
                            {"range": [50, 100], "color": "rgba(16,185,129,0.15)"}
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 3},
                            "thickness": 0.8,
                            "value": 50
                        }
                    }
                ))
                fig_gauge.update_layout(
                    height=250,
                    template="plotly_dark",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(t=20, b=0)
                )
                st.plotly_chart(fig_gauge, use_container_width=True)
        else:
            st.warning("Không lấy được dự đoán mới nhất từ API.")
