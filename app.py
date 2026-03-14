import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Trading Dashboard", layout="wide")
st.title("Trading Behavior Dashboard")
st.caption("Interactive charts from historical trading data + fear/greed sentiment")

@st.cache_data
def load_data():
    fear = pd.read_csv("fear_greed_index.csv")
    trades = pd.read_csv("historical_data.csv")

    trades["time"] = pd.to_datetime(trades["Timestamp"], unit="ms", errors="coerce")
    trades["date"] = trades["time"].dt.date

    if "Date" in fear.columns:
        fear["date"] = pd.to_datetime(fear["Date"], errors="coerce").dt.date
    elif "date" in fear.columns:
        fear["date"] = pd.to_datetime(fear["date"], errors="coerce").dt.date
    elif "timestamp" in fear.columns:
        fear["date"] = pd.to_datetime(fear["timestamp"], unit="s", errors="coerce").dt.date
    else:
        raise ValueError("No date field found in fear_greed_index.csv")

    data = trades.merge(fear[["date", "classification"]], on="date", how="left")
    data = data.dropna(subset=["classification"]).copy()

    if "win" not in data.columns:
        data["win"] = (data["Closed PnL"] > 0).astype(int)

    data = data[data["Start Position"] > 0].copy()
    data["leverage_proxy"] = data["Size USD"] / data["Start Position"]
    data = data[(data["leverage_proxy"] > 0) & np.isfinite(data["leverage_proxy"])].copy()

    sentiment_l = data["classification"].astype(str).str.lower()
    data["sentiment_fg"] = np.where(
        sentiment_l.str.contains("fear"),
        "Fear",
        np.where(sentiment_l.str.contains("greed"), "Greed", "Other"),
    )

    data["date"] = pd.to_datetime(data["date"])
    return data


data = load_data()

st.sidebar.header("Filters")

fear_greed_only = st.sidebar.checkbox("Fear vs Greed view", value=True)
sentiment_col = "sentiment_fg" if fear_greed_only else "classification"

all_sentiments = sorted(data[sentiment_col].dropna().unique().tolist())
if fear_greed_only:
    all_sentiments = [s for s in all_sentiments if s in ["Fear", "Greed"]]
selected_sentiments = st.sidebar.multiselect(
    "Sentiment",
    options=all_sentiments,
    default=all_sentiments,
)

all_sides = sorted(data["Side"].dropna().unique().tolist())
selected_sides = st.sidebar.multiselect(
    "Side",
    options=all_sides,
    default=all_sides,
)

top_accounts_n = 5

date_min = data["date"].min().date()
date_max = data["date"].max().date()
selected_range = st.sidebar.date_input(
    "Date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
else:
    start_date, end_date = date_min, date_max

filtered = data[
    (data[sentiment_col].isin(selected_sentiments))
    & (data["Side"].isin(selected_sides))
    & (data["date"].dt.date >= start_date)
    & (data["date"].dt.date <= end_date)
].copy()

if filtered.empty:
    st.warning("No records found for selected filters.")
    st.stop()

# Top metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Trades", f"{len(filtered):,}")
m2.metric("Active Accounts", f"{filtered['Account'].nunique():,}")
m3.metric("Win Rate", f"{filtered['win'].mean():.2%}")
m4.metric("Avg Trade Size (USD)", f"{filtered['Size USD'].mean():.2f}")

st.divider()

account_daily = (
    filtered.groupby(["Account", "date"], as_index=False)
    .agg(daily_pnl=("Closed PnL", "sum"))
    .sort_values("date")
)

account_priority = (
    account_daily.groupby("Account", as_index=False)
    .agg(
        days=("date", "nunique"),
        trades=("daily_pnl", "size"),
    )
    .sort_values(["days", "trades"], ascending=[False, False])
)
top_accounts = account_priority.head(top_accounts_n)["Account"].tolist()
account_daily_top = account_daily[account_daily["Account"].isin(top_accounts)].copy()
shown_accounts = account_daily_top["Account"].nunique()

fig_account_daily = px.line(
    account_daily_top,
    x="date",
    y="daily_pnl",
    color="Account",
    markers=True,
    title=f"Daily PnL per Account (Top {shown_accounts} Active Accounts)",
)
fig_account_daily.update_layout(hovermode="x unified")
st.plotly_chart(fig_account_daily, use_container_width=True)

daily = (
    filtered.groupby("date", as_index=False)
    .agg(
        daily_pnl=("Closed PnL", "sum"),
        trades=("Closed PnL", "size"),
    )
    .sort_values("date")
)

fig_daily = px.line(
    daily,
    x="date",
    y="trades",
    title="Number of Trades per Day",
    markers=True,
)
st.plotly_chart(fig_daily, use_container_width=True)

drawdown_summary = (
    filtered.assign(loss_only=np.where(filtered["Closed PnL"] < 0, filtered["Closed PnL"], np.nan))
    .groupby(sentiment_col, as_index=False)
    .agg(mean_losing_pnl=("loss_only", "mean"))
)
p05 = (
    filtered.groupby(sentiment_col)["Closed PnL"].quantile(0.05).rename("pnl_p05").reset_index()
)
drawdown_summary = drawdown_summary.merge(p05, on=sentiment_col, how="left")
drawdown_long = drawdown_summary.melt(
    id_vars=[sentiment_col],
    value_vars=["mean_losing_pnl", "pnl_p05"],
    var_name="metric",
    value_name="value",
)

fig_drawdown = px.bar(
    drawdown_long,
    x=sentiment_col,
    y="value",
    color="metric",
    barmode="group",
    title="Drawdown Proxy by Sentiment (Mean Losing PnL and 5th Percentile)",
)
st.plotly_chart(fig_drawdown, use_container_width=True)

c1, c2 = st.columns(2)

with c1:
    fig_lev_hist = px.histogram(
        filtered,
        x="leverage_proxy",
        nbins=50,
        title="Leverage Distribution",
        opacity=0.8,
    )
    st.plotly_chart(fig_lev_hist, use_container_width=True)

with c2:
    long_short_ratio = (
        filtered["Side"].value_counts(normalize=True).rename("ratio").reset_index()
    )
    long_short_ratio.columns = ["Side", "ratio"]
    fig_side_ratio = px.bar(
        long_short_ratio,
        x="Side",
        y="ratio",
        title="Long/Short Ratio",
        text="ratio",
    )
    fig_side_ratio.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig_side_ratio.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig_side_ratio, use_container_width=True)

st.subheader("Win Rate and Average Trade Size by Account")
account_kpis = (
    filtered.groupby("Account", as_index=False)
    .agg(
        trades=("Closed PnL", "size"),
        win_rate=("win", "mean"),
        avg_trade_size=("Size USD", "mean"),
    )
    .sort_values("trades", ascending=False)
)
st.dataframe(account_kpis.round(4), use_container_width=True)

st.subheader("Summary by Sentiment")
sentiment_summary = (
    filtered.groupby(sentiment_col, as_index=False)
    .agg(
        trades=("Closed PnL", "size"),
        win_rate=("win", "mean"),
        avg_pnl=("Closed PnL", "mean"),
        avg_trade_size=("Size USD", "mean"),
        median_leverage=("leverage_proxy", "median"),
    )
    .sort_values("trades", ascending=False)
)
st.dataframe(sentiment_summary.round(4), use_container_width=True)

account_summary = (
    filtered.groupby("Account", as_index=False)
    .agg(
        n_trades=("Account", "size"),
        win_rate=("win", "mean"),
        avg_pnl=("Closed PnL", "mean"),
        total_pnl=("Closed PnL", "sum"),
        pnl_std=("Closed PnL", "std"),
        avg_leverage=("leverage_proxy", "mean"),
    )
)
account_summary["pnl_std"] = account_summary["pnl_std"].fillna(0)

leverage_cut = account_summary["avg_leverage"].median()
activity_cut = account_summary["n_trades"].median()
consistency_cut = account_summary["pnl_std"].median()

account_summary["leverage_segment"] = np.where(
    account_summary["avg_leverage"] >= leverage_cut, "High Leverage", "Low Leverage"
)
account_summary["activity_segment"] = np.where(
    account_summary["n_trades"] >= activity_cut, "Frequent", "Infrequent"
)
account_summary["winner_consistency_segment"] = np.select(
    [
        (account_summary["win_rate"] >= 0.55)
        & (account_summary["avg_pnl"] > 0)
        & (account_summary["pnl_std"] <= consistency_cut),
        (account_summary["win_rate"] >= 0.55)
        & (account_summary["avg_pnl"] > 0)
        & (account_summary["pnl_std"] > consistency_cut),
    ],
    ["Consistent Winners", "Inconsistent Winners"],
    default="Others",
)

seg_leverage = account_summary.groupby("leverage_segment").agg(
    avg_win_rate=("win_rate", "mean"),
    avg_total_pnl=("total_pnl", "mean"),
)
seg_activity = account_summary.groupby("activity_segment").agg(
    avg_win_rate=("win_rate", "mean"),
    avg_total_pnl=("total_pnl", "mean"),
)
seg_consistency = account_summary.groupby("winner_consistency_segment").agg(
    avg_win_rate=("win_rate", "mean"),
    avg_total_pnl=("total_pnl", "mean"),
)

st.subheader("Segment Snapshot")
s1, s2, s3 = st.columns(3)

with s1:
    if set(["Low Leverage", "High Leverage"]).issubset(seg_leverage.index):
        win_delta = seg_leverage.loc["Low Leverage", "avg_win_rate"] - seg_leverage.loc["High Leverage", "avg_win_rate"]
        st.metric("Low vs High Leverage Win Rate", f"{seg_leverage.loc['Low Leverage', 'avg_win_rate']:.2%}", f"{win_delta:+.2%} vs high")

with s2:
    if set(["Frequent", "Infrequent"]).issubset(seg_activity.index):
        pnl_delta = seg_activity.loc["Frequent", "avg_total_pnl"] - seg_activity.loc["Infrequent", "avg_total_pnl"]
        st.metric("Frequent Avg Total PnL", f"{seg_activity.loc['Frequent', 'avg_total_pnl']:.2f}", f"{pnl_delta:+.2f} vs infrequent")

with s3:
    if "Consistent Winners" in seg_consistency.index:
        st.metric("Consistent Winners Win Rate", f"{seg_consistency.loc['Consistent Winners', 'avg_win_rate']:.2%}")

st.subheader("Key Insights")
st.markdown(
    "\n".join(
        [
            f"- Win rate in current filters: **{filtered['win'].mean():.2%}**.",
            f"- Avg trade size in current filters: **{filtered['Size USD'].mean():.2f}**.",
            "- Compare Fear vs Greed using the sidebar toggle to align with the report narrative.",
            "- Drawdown proxy chart highlights both mean losing trade and 5th percentile downside by sentiment.",
        ]
    )
)

st.subheader("Strategy Rules of Thumb")
st.markdown(
    "\n".join(
        [
            "- On Fear days, reduce leverage and tighten loss controls for high-leverage and infrequent trader profiles.",
            "- Increase activity primarily for low-leverage or consistent-winner profiles; avoid scaling frequency for volatile profiles.",
        ]
    )
)

st.subheader("Downloads")
st.download_button(
    "Download filtered trades (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_trades.csv",
    mime="text/csv",
)
st.download_button(
    "Download sentiment summary (CSV)",
    data=sentiment_summary.to_csv(index=False).encode("utf-8"),
    file_name="sentiment_summary.csv",
    mime="text/csv",
)

st.caption("Run command: streamlit run app.py")

with st.expander("Show filtered raw data"):
    st.dataframe(filtered.head(200), use_container_width=True)
