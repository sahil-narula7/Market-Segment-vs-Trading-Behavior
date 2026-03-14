# Market Sentiment vs Trading Behavior

## Overview
This project analyzes how market sentiment (Fear/Greed) is related to trading outcomes and trader behavior using:
- `historical_data.csv`
- `fear_greed_index.csv`

The output is provided as:
- an analysis notebook (`data.ipynb`)
- an interactive Streamlit dashboard (`app.py`)

## Executive Summary
- Sentiment regime is associated with measurable changes in performance, risk, and behavior.
- Traders appear to size larger and use different directional bias depending on market mood.
- Segment-level differences are strong: leverage discipline and trading consistency matter more than raw activity alone.
- Recommended operating approach: tighten risk in Fear regimes and for high-volatility profiles.
- Recommended operating approach: scale activity for lower-leverage, more consistent profiles.
- Recommended operating approach: monitor long/short skew as a crowding signal.

---

## Graphs Included
The Streamlit app and notebook include the following key visuals.

### 1) Daily PnL per Account (Top 5 Active Accounts)
Purpose:
- Shows how account-level PnL changes over time.
- Highlights concentration risk (a few accounts driving most variation).

How to interpret:
- Large spikes indicate account-level volatility.
- Diverging lines show uneven trader performance.

### 2) Number of Trades per Day
Purpose:
- Tracks trading activity over time.
- Helps compare active vs quieter market periods.

How to interpret:
- Peaks indicate high participation days.
- Low periods suggest reduced activity or selectivity.

### 3) Leverage Distribution
Purpose:
- Shows the distribution of leverage proxy across filtered trades.
- Detects risk concentration and outliers.

How to interpret:
- Right-skewed distributions imply a minority using very high leverage.
- A tighter distribution implies more consistent risk-taking.

### 4) Long/Short Ratio
Purpose:
- Shows directional bias (long vs short).

How to interpret:
- Near 50/50 suggests balanced positioning.
- Persistent skew suggests conviction or sentiment bias.

### 5) Drawdown Proxy by Sentiment
(Mean losing trade and 5th percentile PnL)

Purpose:
- Compares downside behavior across sentiment conditions.

How to interpret:
- More negative mean losing PnL implies worse typical downside.
- More negative 5th percentile implies worse tail risk.

### 6) Win Rate and Average Trade Size by Account (Table)
Purpose:
- Summarizes account quality and sizing behavior.

How to interpret:
- High win rate + controlled trade size often indicates better consistency.

### 7) Summary by Sentiment (Table)
Purpose:
- Aggregates win rate, average PnL, trade size, and leverage by sentiment.

How to interpret:
- Makes Fear vs Greed comparisons explicit and auditable.

---

## Analysis Summary
Based on the current workflow and generated tables/charts:

1. Performance differs by sentiment.
- Win rate and average PnL are not constant across sentiment regimes.
- Downside proxies indicate that risk characteristics also shift with sentiment.

2. Trader behavior changes with sentiment.
- Position sizing, leverage usage, and directional bias (long/short) vary with market mood.
- Activity levels (trades/day) also move with sentiment context.

3. Segment effects are meaningful.
- High vs low leverage traders show different risk-return profiles.
- Frequent vs infrequent traders differ in total outcome and consistency.
- Consistent vs inconsistent winners separate stability from raw upside.

---

## Recommendations

### Recommendation 1: Sentiment-Aware Risk Controls
- During Fear conditions, reduce leverage caps for high-risk profiles and tighten loss controls.
- During Greed conditions, keep tail-risk guardrails active (do not increase risk only because average outcomes improve).

### Recommendation 2: Segment-Aware Execution
- Increase activity only for historically consistent, lower-leverage profiles.
- For infrequent or high-volatility profiles, prioritize trade quality and smaller sizing over frequency.

### Recommendation 3: Keep Directional Bias Monitored
- Use long/short ratio drift as an early warning signal for crowding.
- When directional skew becomes extreme, lower exposure and require stronger entry confirmation.

---

## How to Run
From the project folder:

```bash
streamlit run app.py
```

Notebook analysis:
- Open `data.ipynb` and run cells top-to-bottom.

---

## Project Structure
- `app.py`: Streamlit dashboard
- `data.ipynb`: exploratory analysis and written findings
- `fear_greed_index.csv`: sentiment input data
- `historical_data.csv`: trade-level input data

---

## Notes
- Results are filter-dependent in the dashboard (sentiment, side, date range).
- Drawdown metrics used here are proxies, not full portfolio-level max drawdown calculations.
