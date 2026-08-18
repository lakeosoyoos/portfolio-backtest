import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Portfolio Backtest", layout="wide")

st.title("📊 Portfolio Backtester")
st.markdown("Backtest a portfolio with periodic rebalancing")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Portfolio Setup")

    num_tickers = st.slider("Number of tickers", 1, 10, 3)

    col_tickers, col_weights = st.columns(2)

    tickers = []
    weights = []

    with col_tickers:
        st.markdown("**Tickers**")
        for i in range(num_tickers):
            ticker = st.text_input(f"Ticker {i+1}", placeholder="e.g., AAPL", key=f"ticker_{i}")
            if ticker:
                tickers.append(ticker.upper())

    with col_weights:
        st.markdown("**Weight (%)**")
        for i in range(num_tickers):
            weight = st.number_input(f"Weight {i+1}", min_value=0.0, max_value=100.0, value=100/num_tickers, step=0.1, key=f"weight_{i}")
            weights.append(weight)

    total_weight = sum(weights) if weights else 0
    weight_status = "✅" if abs(total_weight - 100.0) < 0.1 else "❌"
    st.metric("Total Weight", f"{total_weight:.1f}%", delta=f"{total_weight - 100:.1f}%", delta_color="off")

with col2:
    st.subheader("Parameters")
    portfolio_value = st.number_input("Starting Portfolio Value ($)", min_value=1000, value=100000, step=1000)

    lookback_days = st.selectbox("Lookback Period",
        options=[30, 60, 90, 180, 365, 730, 1825],
        format_func=lambda x: f"{x//365}y" if x >= 365 else f"{x}d"
    )

    rebalance_freq = st.selectbox("Rebalance Frequency",
        options=["Daily", "Weekly", "Monthly", "Quarterly", "Annually"],
        index=2
    )

    reinvest = st.checkbox("Reinvest gains at rebalance", value=True,
        help="ON: gains/losses compound — each rebalance reallocates your current portfolio value. "
             "OFF: each rebalance resets to your original starting balance, so period gains/losses don't carry forward.")

if st.button("Run Backtest", type="primary", use_container_width=True):
    if not tickers or abs(total_weight - 100.0) > 0.1:
        st.error("⚠️ Please enter tickers and ensure weights sum to 100%")
    else:
        with st.spinner("Fetching data and running backtest..."):
            try:
                # Get historical data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=lookback_days)

                data = yf.download(tickers, start=start_date, end=end_date, progress=False, auto_adjust=True)["Close"]

                # yfinance returns a Series (not DataFrame) when only one ticker is requested
                if isinstance(data, pd.Series):
                    data = data.to_frame(name=tickers[0])

                # Tickers yfinance couldn't find (bad symbol, delisted) either never appear as a column,
                # or appear as a column that's entirely NaN — treat both as missing
                missing_tickers = [t for t in tickers if t not in data.columns or data[t].isna().all()]

                # Keep only the tickers we actually got data for, preserving order, and carry their
                # matching weights along so normalized_weights and data.columns stay aligned by index
                valid_tickers = [t for t in tickers if t not in missing_tickers]
                valid_weights = [weights[tickers.index(t)] for t in valid_tickers]
                data = data[valid_tickers]

                # Keep only dates where EVERY remaining ticker has a price — a single missing quote
                # (rate limit, holiday mismatch) would otherwise poison the portfolio value calc with NaN
                data = data.dropna(how="any")

                if missing_tickers:
                    st.warning(f"⚠️ No data found for: {', '.join(missing_tickers)}. Check the ticker symbol(s).")

                if not valid_tickers or len(data) < 2:
                    st.error("Not enough data for selected period. Try a longer lookback, check your tickers, or retry (Yahoo Finance may be rate-limiting).")
                else:
                    tickers = valid_tickers
                    # Normalize weights
                    normalized_weights = np.array(valid_weights) / sum(valid_weights)

                    # Determine rebalance frequency in days
                    if rebalance_freq == "Daily":
                        rebalance_days = 1
                    elif rebalance_freq == "Weekly":
                        rebalance_days = 7
                    elif rebalance_freq == "Monthly":
                        rebalance_days = 30
                    elif rebalance_freq == "Quarterly":
                        rebalance_days = 91
                    else:  # Annually
                        rebalance_days = 365

                    # Initialize portfolio
                    portfolio_values = []
                    dates = []
                    shares = None
                    last_rebalance = data.index[0]

                    # Calculate portfolio value over time
                    for idx, date in enumerate(data.index):
                        current_prices = data.iloc[idx]

                        if idx == 0:
                            # Initial buy-in
                            shares = (normalized_weights * portfolio_value) / current_prices.values
                        elif (date - last_rebalance).days >= rebalance_days:
                            if reinvest:
                                # Compound: reallocate using CURRENT portfolio value
                                current_value = np.sum(shares * current_prices.values)
                                shares = (normalized_weights * current_value) / current_prices.values
                            else:
                                # No reinvestment: reset to the ORIGINAL starting balance each period
                                shares = (normalized_weights * portfolio_value) / current_prices.values
                            last_rebalance = date

                        portfolio_val = np.sum(shares * current_prices.values)
                        portfolio_values.append(portfolio_val)
                        dates.append(date)

                    portfolio_df = pd.DataFrame({
                        "Date": dates,
                        "Portfolio Value": portfolio_values
                    })

                    # Calculate metrics
                    total_return = (portfolio_values[-1] - portfolio_value) / portfolio_value * 100
                    annualized_return = ((portfolio_values[-1] / portfolio_value) ** (365 / lookback_days) - 1) * 100
                    max_val = max(portfolio_values)
                    min_val = min(portfolio_values)
                    max_drawdown = (max_val - min_val) / max_val * 100 if max_val > 0 else 0

                    daily_returns = pd.Series(portfolio_values).pct_change().dropna()
                    sharpe_ratio = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0

                    # Display metrics
                    st.divider()
                    metric_cols = st.columns(5)

                    with metric_cols[0]:
                        st.metric("Total Return", f"{total_return:+.2f}%")
                    with metric_cols[1]:
                        st.metric("Annualized Return", f"{annualized_return:+.2f}%")
                    with metric_cols[2]:
                        st.metric("Max Drawdown", f"{max_drawdown:.2f}%", delta_color="inverse")
                    with metric_cols[3]:
                        st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
                    with metric_cols[4]:
                        st.metric("Final Value", f"${portfolio_values[-1]:,.0f}")

                    st.divider()

                    # Plot performance
                    fig = go.Figure()

                    fig.add_trace(go.Scatter(
                        x=portfolio_df["Date"],
                        y=portfolio_df["Portfolio Value"],
                        mode="lines",
                        name="Portfolio Value",
                        line=dict(color="rgb(31, 119, 180)", width=2),
                        fill="tozeroy",
                        fillcolor="rgba(31, 119, 180, 0.1)"
                    ))

                    fig.update_layout(
                        title="Portfolio Value Over Time",
                        xaxis_title="Date",
                        yaxis_title="Portfolio Value ($)",
                        hovermode="x unified",
                        template="plotly_white",
                        height=500
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Individual ticker performance table
                    st.subheader("Individual Ticker Performance")

                    ticker_returns = []
                    for ticker in tickers:
                        if ticker in data.columns:
                            ticker_data = data[ticker]
                            ticker_return = (ticker_data.iloc[-1] - ticker_data.iloc[0]) / ticker_data.iloc[0] * 100
                            ticker_returns.append({
                                "Ticker": ticker,
                                "Return": f"{ticker_return:+.2f}%",
                                "Weight": f"{normalized_weights[tickers.index(ticker)] * 100:.1f}%",
                                "Start Price": f"${ticker_data.iloc[0]:.2f}",
                                "End Price": f"${ticker_data.iloc[-1]:.2f}"
                            })

                    ticker_df = pd.DataFrame(ticker_returns)
                    st.dataframe(ticker_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Error: {str(e)}")

st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.markdown("""
This tool backtests a portfolio with:
- **Up to 10 tickers** with custom weights
- **Periodic rebalancing** (daily to annually)
- **Historical price data** from Yahoo Finance

Returns are calculated including rebalancing at your chosen frequency.
""")
