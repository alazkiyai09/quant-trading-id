# Setup Instructions

## Quick Setup Guide

### Step 1: Environment Setup

```bash
# Navigate to project directory
cd "f:\Learning Center\refactored_trading_system"

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Database Setup

**Option A: Using pgAdmin**

1. Open pgAdmin
2. Right-click on PostgreSQL server → Create → Database
3. Name: `Stock_Data`
4. Click Save
5. Open Query Tool and run:

```sql
-- Create daily data template
CREATE TABLE stock_daily_data (
    date DATE PRIMARY KEY,
    close DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    volume BIGINT
);

-- Create hourly data template
CREATE TABLE stock_hourly_data (
    datetime TIMESTAMP WITHOUT TIME ZONE PRIMARY KEY,
    close DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    volume BIGINT
);

-- Create symbol status tracking
CREATE TABLE symbol_data_status (
    symbol TEXT PRIMARY KEY,
    has_daily BOOLEAN,
    has_hourly BOOLEAN,
    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    note TEXT
);
```

**Option B: Using psql Command Line**

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE "Stock_Data";

# Connect to new database
\c Stock_Data

# Run the same CREATE TABLE commands as above
```

### Step 3: Environment Configuration

```bash
# Copy template
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit with your settings
notepad .env  # Windows
# nano .env  # Linux/Mac
```

Update these values in `.env`:
```env
DB_HOST=localhost
DB_NAME=Stock_Data
DB_USER=postgres
DB_PASSWORD=YOUR_ACTUAL_PASSWORD_HERE
DB_PORT=5432

CAPITAL=10000000
MAX_RISK_PER_TRADE=0.02
```

### Step 4: Copy Stock List

```bash
# Copy stock list from old folder
copy "..\Stock_list.txt" "."  # Windows
# cp ../Stock_list.txt .  # Linux/Mac
```

### Step 5: Initial Data Load

```python
# Run Python interpreter
python

# Execute initial data load
from data_management.manager import DataManager, load_symbols_from_file

# Load first 10 symbols for testing
symbols = load_symbols_from_file("Stock_list.txt")[:10]
manager = DataManager()

# Add stocks to database
results = manager.bulk_add_stocks(symbols)
print(results)

# Exit Python
exit()
```

### Step 6: Verify Installation

```bash
# Run tests
pytest tests/ -v

# If tests pass, you're ready!
```

## Usage Examples

### Update All Stock Data

```bash
python main.py update
```

### Train Model for Specific Stock

```bash
python main.py train --stock ADMR
```

### Generate Prediction

```bash
# 7-day forecast
python main.py predict --stock ADMR

# 30-day forecast
python main.py predict --stock ADMR --days 30
```

### Python API Usage

```python
from data_management.manager import DataManager
from ml_prediction.trainer import train_multiseed_ensemble, save_artifacts
from ml_prediction.predictor import MultiSeedPredictor
from ml_prediction.features import preprocess_stock_data
from utils.database import read_table

# 1. Update data
manager = DataManager()
manager.update_stock_data("ADMR")

# 2. Load and preprocess
stock_data = read_table("ADMR_Daily_Data")
exo_dict = {
    "^JKSE": read_table("^JKSE_Daily_Data"),
    "USDIDR=X": read_table("USDIDR=X_Daily_Data")
}
processed = preprocess_stock_data(stock_data, exo_dict)

# 3. Train
feature_cols = [c for c in processed.columns
                if c not in ['close', 'high', 'low', 'open', 'volume']]
artifacts = train_multiseed_ensemble(processed, feature_cols)
save_artifacts(artifacts, "artifacts/ADMR_ensemble.pkl")

# 4. Predict
predictor = MultiSeedPredictor(artifacts)
returns, prices = predictor.predict(processed)
print(f"7-day forecast: {prices}")
```

## Troubleshooting

### Import Error: No module named 'config'

Make sure you're in the project root directory:
```bash
cd "f:\Learning Center\refactored_trading_system"
python main.py
```

### Database Connection Failed

1. Check PostgreSQL is running:
   ```bash
   # Windows
   net start postgresql-x64-13
   ```

2. Verify credentials in `.env`

3. Test connection:
   ```python
   from utils.database import db_manager
   with db_manager.get_connection() as conn:
       print("Success!")
   ```

### TA-Lib Not Found

TA-Lib is optional. The system will use pandas fallbacks if not installed.

To install on Windows:
1. Download wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
2. Install: `pip install TA_Lib-0.4.XX-cpXX-cpXX-winXX.whl`

### Out of Memory During Training

Reduce batch size or number of features:
```python
# In config/settings.py
ML_CONFIG['BATCH_SIZE'] = 16  # Reduce from 32
```

## Next Steps

1. ✅ Setup complete
2. 📊 Load historical data for all stocks
3. 🤖 Train models for your target stocks
4. 📈 Generate predictions
5. 💰 Implement trading strategies (coming soon)
6. 📉 Run backtests (coming soon)

## Need Help?

- Check logs: `logs/trading_system.log`
- Review README.md for detailed documentation
- Check existing tests for usage examples
