# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- 10 GB free disk space

## Installation (5 minutes)

### 1. Setup Environment (1 min)

```bash
cd "f:\Learning Center\refactored_trading_system"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Database (2 min)

Open pgAdmin or psql:

```sql
CREATE DATABASE "Stock_Data";

\c Stock_Data

CREATE TABLE stock_daily_data (
    date DATE PRIMARY KEY,
    close DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    volume BIGINT
);

CREATE TABLE stock_hourly_data (
    datetime TIMESTAMP WITHOUT TIME ZONE PRIMARY KEY,
    close DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    volume BIGINT
);
```

### 3. Configure Environment (1 min)

```bash
copy .env.example .env
notepad .env
```

Update `.env`:
```env
DB_PASSWORD=your_postgres_password
CAPITAL=10000000
```

### 4. Test Installation (1 min)

```bash
python -c "from utils.database import db_manager; print('✅ Connection successful!')"
```

## First Use (10 minutes)

### Load Sample Data

```python
python
```

```python
from data_management.manager import DataManager

# Initialize
manager = DataManager()

# Add first 5 stocks (test)
test_stocks = ["ADMR", "BBRI", "BBCA", "TLKM", "ASII"]
for stock in test_stocks:
    print(f"Loading {stock}...")
    manager.add_new_stock(stock)

print("✅ Sample data loaded!")
exit()
```

### Train Your First Model

```bash
python main.py train --stock ADMR
```

This will:
1. Load ADMR data
2. Load exogenous data (IHSG, USD/IDR, etc.)
3. Engineer 100+ features
4. Train 5 ensemble models (3 base models × 5 seeds)
5. Save artifacts to `artifacts/ADMR_ensemble.pkl`

**Time:** ~5-10 minutes

### Generate Prediction

```bash
python main.py predict --stock ADMR
```

Output:
```
ADMR 7-day Forecast:
Current price: 1250.00
  Day 1: 1255.30
  Day 2: 1262.15
  Day 3: 1258.40
  Day 4: 1265.80
  Day 5: 1270.25
  Day 6: 1268.50
  Day 7: 1275.90
```

**Time:** ~10 seconds

## Common Workflows

### Daily Data Update

```bash
# Update all stocks
python main.py update

# Or in Python
from data_management.manager import DataManager, load_symbols_from_file

symbols = load_symbols_from_file("Stock_list.txt")
manager = DataManager()
results = manager.bulk_update_stocks(symbols)
```

### Batch Train Multiple Stocks

```python
from ml_prediction.trainer import train_multiseed_ensemble, save_artifacts
from ml_prediction.features import preprocess_stock_data
from utils.database import read_table

stocks = ["ADMR", "BBRI", "BBCA", "TLKM", "ASII"]

for stock in stocks:
    print(f"\n{'='*60}")
    print(f"Training {stock}")
    print(f"{'='*60}")

    # Load data
    stock_data = read_table(f"{stock}_Daily_Data")
    exo_dict = {
        "^JKSE": read_table("^JKSE_Daily_Data"),
        "USDIDR=X": read_table("USDIDR=X_Daily_Data")
    }

    # Preprocess
    processed = preprocess_stock_data(stock_data, exo_dict)
    feature_cols = [c for c in processed.columns
                   if c not in ['close', 'high', 'low', 'open', 'volume']]

    # Train
    artifacts = train_multiseed_ensemble(processed, feature_cols)
    save_artifacts(artifacts, f"artifacts/{stock}_ensemble.pkl")

    print(f"✅ {stock} training complete!")
```

### Generate Multiple Forecasts

```python
from ml_prediction.predictor import MultiSeedPredictor
from ml_prediction.trainer import load_artifacts
from ml_prediction.features import preprocess_stock_data
from utils.database import read_table
import pandas as pd

stocks = ["ADMR", "BBRI", "BBCA", "TLKM", "ASII"]
forecasts = []

for stock in stocks:
    # Load
    artifacts = load_artifacts(f"artifacts/{stock}_ensemble.pkl")
    stock_data = read_table(f"{stock}_Daily_Data")
    exo_dict = {"^JKSE": read_table("^JKSE_Daily_Data")}
    processed = preprocess_stock_data(stock_data, exo_dict)

    # Predict
    predictor = MultiSeedPredictor(artifacts)
    returns, prices = predictor.predict(processed)

    forecasts.append({
        'Stock': stock,
        'Current': processed['close'].iloc[-1],
        'Day_1': prices[0],
        'Day_7': prices[6],
        'Return_7d': ((prices[6] / processed['close'].iloc[-1]) - 1) * 100
    })

df = pd.DataFrame(forecasts)
print(df.to_string(index=False))

# Save to CSV
df.to_csv(f"reports/forecasts_{pd.Timestamp.now():%Y%m%d}.csv", index=False)
```

## Tips & Tricks

### Speed Up Data Loading

```python
# Use parallel processing
manager = DataManager(max_workers=20)  # Increase workers
```

### Reduce Training Time

```python
# Use fewer seeds (faster, less robust)
from config.settings import ml_config
ml_config.SEEDS = [42, 73]  # Instead of [7, 17, 42, 73, 101]
```

### Monitor Training Progress

```bash
# In separate terminal, watch logs
tail -f logs/trading_system.log
```

### Check Disk Usage

```bash
# Show artifact sizes
ls -lh artifacts/

# Clean old artifacts
rm artifacts/*_old.pkl
```

## Troubleshooting

### "ModuleNotFoundError"

Make sure virtual environment is activated:
```bash
venv\Scripts\activate
```

### "Connection refused" (Database)

Check PostgreSQL is running:
```bash
net start postgresql-x64-13  # Windows
```

### "Out of memory"

Reduce batch size:
```python
# In config/settings.py
MLConfig.BATCH_SIZE = 16  # Default is 32
```

### Slow data fetching

Yahoo Finance may rate-limit. Add delays:
```python
import time
for stock in stocks:
    manager.add_new_stock(stock)
    time.sleep(1)  # 1 second delay
```

## Next Steps

1. ✅ Load all 657 stocks: `python main.py update`
2. 📊 Train models for your watchlist
3. 📈 Set up daily prediction pipeline
4. 💰 Implement trading strategies (coming soon)
5. 📉 Run backtests (coming soon)

## Getting Help

- **Errors:** Check `logs/trading_system.log`
- **Questions:** Read `README.md` and `setup_instructions.md`
- **Examples:** Look at test files in `tests/`

## Resources

- [Full Documentation](README.md)
- [Setup Guide](setup_instructions.md)
- [Refactoring Summary](REFACTORING_SUMMARY.md)
- [Changelog](CHANGELOG.md)

---

**Happy Trading! 📈**
