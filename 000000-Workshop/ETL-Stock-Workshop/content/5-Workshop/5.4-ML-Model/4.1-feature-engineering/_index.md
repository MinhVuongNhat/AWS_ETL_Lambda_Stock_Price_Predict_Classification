---
title : "Feature Engineering"
date: ""
weight : 1
chapter : false
pre : " <b> 5.4.1. </b> "
---

#### Feature Engineering — 16 Technical Indicators

Feature Engineering is the most critical step in the ML pipeline. `src/transform.py` computes **16 technical indicators** from historical OHLCV data using **Polars**.

---

#### 16 Technical Indicators

**Group 1: Trend**

| Indicator | Formula | Meaning |
|:---|:---|:---|
| `SMA_5` | Simple Moving Average (5-day) | Short-term trend |
| `SMA_20` | Simple Moving Average (20-day) | Medium-term trend |
| `EMA_12` | Exponential Moving Average span=12 | Fast reaction to price changes |
| `EMA_26` | Exponential Moving Average span=26 | Slower long-term trend |

**Group 2: Momentum**

| Indicator | Formula | Meaning |
|:---|:---|:---|
| `MACD` | EMA_12 - EMA_26 | Trend confirmation & reversal signals |
| `MACD_Signal` | EMA_9 of MACD | MACD signal line |
| `MACD_Hist` | MACD - MACD_Signal | MACD histogram bar |
| `RSI_14` | Wilder's Smoothing, window=14 | Overbought (>70) / Oversold (<30) indicator |

**Group 3: Volatility**

| Indicator | Formula | Meaning |
|:---|:---|:---|
| `BB_Upper` | SMA_20 + 2 × STD_20 | Bollinger Bands upper band |
| `BB_Lower` | SMA_20 - 2 × STD_20 | Bollinger Bands lower band |
| `BB_Width` | (BB_Upper - BB_Lower) / SMA_20 | Band width — measures volatility |
| `Intraday_Volatility` | (High - Low) / Open | Intraday price swing range |

**Group 4: Lag & Return**

| Indicator | Formula | Meaning |
|:---|:---|:---|
| `Lag_Close_1` | Close at T-1 | Pattern from yesterday |
| `Lag_Close_2` | Close at T-2 | Pattern from 2 days ago |
| `Lag_Close_3` | Close at T-3 | Pattern from 3 days ago |
| `Daily_Return` | Adj_Close / Adj_Close(T-1) - 1 | Daily return rate |

---

#### Label — Classification Target

```
Label = 1  if Close(T+1) > Close(T)   → PRICE UP prediction
Label = 0  if Close(T+1) ≤ Close(T)  → PRICE DOWN prediction
```

![Technical Indicators Chart](/images/4.1/technical-indicators-chart.png)
