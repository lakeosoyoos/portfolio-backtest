# Portfolio Backtester

A Streamlit app to backtest a multi-ticker portfolio with periodic rebalancing.

## Features

- **Up to 10 tickers** with custom weights
- **Flexible lookback periods** (30 days to 5 years)
- **Rebalancing frequencies** (daily, weekly, monthly, quarterly, annually)
- **Key metrics** including total return, annualized return, max drawdown, and Sharpe ratio
- **Interactive charts** showing portfolio value over time
- **Individual ticker performance** breakdown

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Cloud (Free, Easiest)

1. Create a GitHub repo with these files
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account and select this repo
4. Get a public URL instantly

### Option 2: Heroku

1. Add `Procfile`:
```
web: streamlit run --server.port=$PORT app.py
```

2. Deploy:
```bash
heroku create your-app-name
git push heroku main
```

### Option 3: AWS (EC2)

1. Launch an EC2 instance
2. Install Python 3.9+
3. Install dependencies and run:
```bash
nohup streamlit run app.py --server.port 80 &
```

### Option 4: Railway.app (Simple)

1. Connect your GitHub repo
2. Deploy automatically from main branch
3. Get a public URL

## Usage

1. Enter up to 10 stock tickers (e.g., AAPL, MSFT, GOOGL)
2. Set the weight for each ticker (must sum to 100%)
3. Choose the starting portfolio value
4. Select lookback period (30 days to 5 years)
5. Choose rebalance frequency
6. Click "Run Backtest"

The app will:
- Fetch historical price data
- Simulate portfolio with periodic rebalancing
- Show total returns and key metrics
- Display performance chart
- Break down individual ticker returns

## Metrics Explained

- **Total Return**: Percentage gain/loss over the entire period
- **Annualized Return**: Return annualized (what it would be if sustained for 1 year)
- **Max Drawdown**: Largest peak-to-trough decline (%)
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Final Value**: Dollar amount at end of backtest period

## Notes

- Data is from Yahoo Finance
- Past performance does not guarantee future results
- This is for backtesting/analysis only, not financial advice
- Rebalancing accounts for price changes only (no trading costs simulated)
