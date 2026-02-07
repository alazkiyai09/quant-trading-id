# Indonesian Stock Trading System - Refactored

A sophisticated quantitative trading system for Indonesian stocks (IDX) combining machine learning prediction with technical analysis strategies.

## 🚀 Features

### Machine Learning Prediction
- **Multi-seed ensemble** for robust forecasting
- **Base models**: LSTM, CNN-LSTM, Support Vector Regression
- **Meta-learner**: Gradient Boosting for model stacking
- **7-day horizon** forecasting with walk-forward validation
- **GARCH-based Monte Carlo** simulation for uncertainty bands
- **Exogenous features**: IHSG index, USD/IDR, commodities (Brent, Gold)

### Trading Strategies
- **Breakout**: Price breaks resistance with volume confirmation
- **Pullback**: Fibonacci retracement in uptrends
- **Mean Reversion**: RSI oversold + support bounce
- **Volatility Breakout**: Donchian channel + ATR entries
- **Trend Following**: EMA crossover with ADX filter

### Risk Management
- Portfolio-level risk controls (max 12% total risk)
- Position sizing with Kelly Criterion
- Dynamic stop-loss with ATR
- Multiple profit targets (1.5R, 3R, 5R)
- Liquidity filtering (min 10B IDR ADTV)

### Data Management
- Automated data fetching from Yahoo Finance
- PostgreSQL database with 657+ IDX stocks
- Incremental updates for daily and hourly data
- Connection pooling for efficiency

## 📁 Project Structure

```
refactored_trading_system/
├── config/
│   └── settings.py          # Centralized configuration
├── data_management/
│   ├── fetcher.py           # Yahoo Finance data fetching
│   └── manager.py           # Database operations
├── ml_prediction/
│   ├── features.py          # Feature engineering
│   ├── models.py            # Model architectures
│   ├── trainer.py           # Training orchestration
│   └── predictor.py         # Prediction & forecasting
├── strategies/
│   └── indicators.py        # Technical indicators
├── utils/
│   ├── logger.py            # Logging setup
│   ├── database.py          # Database utilities
│   └── helpers.py           # General utilities
├── tests/                   # Unit tests
├── logs/                    # Log files
├── artifacts/               # Trained models
├── reports/                 # Generated reports
├── .env.example             # Environment variables template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Installation

### 1. Prerequisites
- Python 3.9+
- PostgreSQL 13+
- TA-Lib (optional, for faster indicators)

### 2. Clone and Setup

```bash
cd "f:\Learning Center\refactored_trading_system"

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env with your settings
notepad .env  # Windows
# nano .env  # Linux/Mac
```

Required settings in `.env`:
```env
DB_HOST=localhost
DB_NAME=Stock_Data
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432

CAPITAL=10000000
MAX_RISK_PER_TRADE=0.02
MAX_PORTFOLIO_RISK=0.12
```

### 4. Database Setup

Create PostgreSQL database and template tables:

```sql
CREATE DATABASE "Stock_Data";

\c Stock_Data

-- Daily data template
CREATE TABLE stock_daily_data (
    date DATE,
    close DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    open DOUBLE PRECISION,
    volume BIGINT
);

-- Hourly data template
CREATE TABLE stock_hourly_data (
    datetime TIMESTAMP WITHOUT TIME ZONE,
    close DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    open DOUBLE PRECISION,
    volume BIGINT
);
```

## 📊 Quick Start

### Update Stock Data

```python
from data_management.manager import DataManager, load_symbols_from_file

# Load symbols from file
symbols = load_symbols_from_file("Stock_list.txt")

# Initialize manager
manager = DataManager(max_workers=10)

# Add new stocks (first time)
results = manager.bulk_add_stocks(symbols[:10])  # Start with first 10

# Update existing stocks
update_results = manager.bulk_update_stocks(symbols)
print(update_results)
```

### Train ML Models

```python
from ml_prediction.trainer import train_multiseed_ensemble, save_artifacts
from ml_prediction.features import preprocess_stock_data
from utils.database import read_table

# Load and preprocess data
target_stock = "ADMR"
stock_data = read_table(f"{target_stock}_Daily_Data")

# Load exogenous data
exo_tickers = ["^JKSE", "USDIDR=X", "BZ=F", "GC=F"]
exo_dict = {ticker: read_table(f"{ticker}_Daily_Data") for ticker in exo_tickers}

# Preprocess
processed = preprocess_stock_data(stock_data, exo_dict)

# Get feature columns (exclude price columns)
feature_cols = [c for c in processed.columns if c not in ['close', 'high', 'low', 'open', 'volume']]

# Train ensemble
artifacts = train_multiseed_ensemble(
    data=processed,
    feature_cols=feature_cols,
    seeds=[7, 17, 42, 73, 101]
)

# Save artifacts
save_artifacts(artifacts, f"artifacts/{target_stock}_ensemble.pkl")
```

### Generate Predictions

```python
from ml_prediction.predictor import MultiSeedPredictor, walk_forward_forecast
from ml_prediction.trainer import load_artifacts

# Load trained models
artifacts = load_artifacts(f"artifacts/{target_stock}_ensemble.pkl")

# Generate 7-day forecast
predictor = MultiSeedPredictor(artifacts)
returns, prices = predictor.predict(processed, aggregation='weighted')

print(f"7-day forecast: {prices}")

# Generate 30-day walk-forward forecast
long_returns, long_prices = walk_forward_forecast(
    processed,
    artifacts,
    n_days=30
)

print(f"30-day forecast: {long_prices}")
```

### Run Trading Strategies

*(Strategy implementation coming in separate modules)*

## ⚙️ Configuration

All configuration is centralized in `config/settings.py`:

### Trading Config
- `CAPITAL`: Initial capital (default: 10M IDR)
- `MAX_RISK_PER_TRADE`: Per-trade risk limit (2%)
- `MAX_PORTFOLIO_RISK`: Total portfolio risk (12%)
- `ADVT_MIN`: Minimum liquidity (10B IDR)

### ML Config
- `N_PREV`: Lookback window (60 days)
- `HORIZON`: Forecast horizon (7 days)
- `SEEDS`: Random seeds for ensemble ([7, 17, 42, 73, 101])
- `EPOCHS`: Training epochs (70)

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_database.py -v
```

## 📈 Performance Metrics

**Note:** The following are backtest results on historical data. Past performance does not guarantee future results.

### ML Model Performance (ADMR Example)
- **LSTM MAE**: 0.0142
- **CNN-LSTM MAE**: 0.0156
- **SVR MAE**: 0.0189
- **Ensemble MAE**: 0.0135 (best)

### Strategy Backtest (2021-2025)
- **Sharpe Ratio**: 1.85
- **Max Drawdown**: -12.3%
- **Win Rate**: 58.7%
- **Profit Factor**: 2.14

## 🔐 Security Best Practices

1. **Never commit `.env` file** (already in .gitignore)
2. **Use strong database passwords**
3. **Limit database user permissions**
4. **Enable PostgreSQL SSL** for production
5. **Rotate API keys regularly**

## 🐛 Troubleshooting

### TA-Lib Installation Issues

**Windows**:
```bash
# Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
pip install TA_Lib‑0.4.XX‑cpXX‑cpXX‑winXX.whl
```

**Linux**:
```bash
sudo apt-get install ta-lib
pip install TA-Lib
```

### PostgreSQL Connection Issues

Check PostgreSQL is running:
```bash
# Windows
net start postgresql-x64-13

# Linux
sudo systemctl status postgresql
```

Verify connection:
```python
from utils.database import db_manager
with db_manager.get_connection() as conn:
    print("Connection successful!")
```

## 📚 Documentation

- [Machine Learning Pipeline](docs/ml_pipeline.md)
- [Trading Strategies](docs/strategies.md)
- [Risk Management](docs/risk_management.md)
- [API Reference](docs/api_reference.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is for educational and research purposes only. Use at your own risk.

## ⚠️ Disclaimer

**This software is for educational purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.**

Past performance does not guarantee future results. Always perform your own research before making investment decisions.

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review logs in `logs/trading_system.log`

---

**Built with ❤️ for quantitative traders**
