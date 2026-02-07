"""
Centralized Configuration Management
Loads settings from environment variables with fallback defaults
"""
import os
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class DatabaseConfig:
    """Database connection settings"""
    HOST = os.getenv('DB_HOST', 'localhost')
    NAME = os.getenv('DB_NAME', 'Stock_Data')
    USER = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', '')  # SECURITY: No default password - must be set via env
    PORT = int(os.getenv('DB_PORT', '5432'))

    @classmethod
    def get_connection_params(cls) -> Dict[str, str]:
        """Returns database connection parameters"""
        return {
            'host': cls.HOST,
            'database': cls.NAME,
            'user': cls.USER,
            'password': cls.PASSWORD,
            'port': cls.PORT
        }


class TradingConfig:
    """Trading system configuration"""
    # Capital & Risk Management
    CAPITAL = float(os.getenv('CAPITAL', '10000000'))
    MAX_RISK_PER_TRADE = float(os.getenv('MAX_RISK_PER_TRADE', '0.02'))
    MAX_PORTFOLIO_RISK = float(os.getenv('MAX_PORTFOLIO_RISK', '0.12'))
    MAX_POSITION_RISK_PCT = 0.15
    LOT_SIZE = 100
    TOP_N = 5

    # Market Filters
    ADVT_MIN = 10_000_000_000  # 10B IDR minimum liquidity
    MIN_PRICE = 200  # Minimum stock price
    MAX_PRICE = 50_000  # Maximum stock price

    # Strategy Modes
    MODES = ["breakout", "pullback", "mean_reversion", "vol_breakout", "trend_follow"]
    MODE_PRIORITY = {
        "breakout": 5,
        "pullback": 4,
        "trend_follow": 3,
        "vol_breakout": 2,
        "mean_reversion": 1,
    }

    # Technical Parameters
    RES_BUFFER_PCT = 0.002
    FIB_ZONE = (0.382, 0.5)
    N_BACK_SR = 120  # Support/Resistance lookback
    N_BACK_IMPULSE = 180
    LB_SWING = 2  # Swing detection lookback

    # Volatility Breakout
    DONCHIAN_N = 20
    VB_K_ATR = 0.50

    # Trend Following
    TF_FAST = 20
    TF_SLOW = 50

    # Multi-Timeframe
    USE_HOURLY_CONFIRM = True
    HOURLY_EMA_FAST = 20
    HOURLY_EMA_SLOW = 50

    # Validation
    MIN_RR_RATIO = 1.5
    MAX_TRADES_PER_DAY = 3
    MIN_HOLD_BARS = 2

    # Risk Controls
    COOLDOWN_BARS = 10
    MAX_OPEN_POSITIONS = 5
    MAX_CAP_PER_TRADE = 0.20
    MAX_ADTV_PCT = 0.05
    MAX_GAP_PCT = 0.02

    # IHSG Regime
    USE_IHSG_FILTER_LIVE = True
    IHSG_TABLE_NAME = "^JKSE_Daily_Data"
    MIN_MODE_WEIGHT_LIVE = 0.5

    MODE_WEIGHTS_BY_REGIME = {
        "Bull": {
            "breakout": 1.0,
            "pullback": 1.0,
            "trend_follow": 1.0,
            "vol_breakout": 0.8,
            "mean_reversion": 0.4
        },
        "Sideways": {
            "breakout": 0.5,
            "pullback": 0.7,
            "trend_follow": 0.4,
            "vol_breakout": 0.6,
            "mean_reversion": 1.0
        },
        "Bear": {
            "breakout": 0.2,
            "pullback": 0.3,
            "trend_follow": 0.1,
            "vol_breakout": 0.3,
            "mean_reversion": 0.6
        },
    }

    # Backtest
    BACKTEST_START = "2021-01-01"
    BACKTEST_END = "2025-08-22"
    SLIPPAGE_PCT = 0.0005  # 5 basis points
    COMMISSION_PER_TRADE = 0.0

    MAX_HOLD_DAYS = {
        "breakout": 15,
        "pullback": 20,
        "mean_reversion": 8,
        "vol_breakout": 15,
        "trend_follow": 60,
    }


class MLConfig:
    """Machine Learning model configuration"""
    # Data
    DATE_FIELD = "date"
    MIN_TOTAL_ROWS = 250

    # Features
    RSI_PERIOD = 14
    ADX_PERIOD = 20
    VOL_PROXY_WIN = 20
    TREND_REGIME_WIN = 20
    VOL_REGIME_WIN = 60
    EXTENDED_LAGS = [30, 60, 90]

    # Exogenous Features
    EXO_SHIFT = 1
    EXO_LAGS = [1, 3, 5, 10]
    EXO_ROLL_WINDOWS = [5, 20, 60]

    # Model Architecture
    LSTM_CONFIG = {
        "units": [48, 24],
        "dropout": 0.3,
        "l2_reg": 1e-4,
        "lr": 1.5e-3,
        "loss_delta": 0.0025
    }

    CNN_LSTM_CONFIG = {
        "filters": 48,
        "kernel_size": 3,
        "pool_size": 2,
        "lstm_units": 48,
        "dropout": 0.3,
        "lr": 1.5e-3,
        "loss_delta": 0.0025
    }

    SVR_CONFIG = {
        "kernel": "rbf",
        "C": 12.0,
        "epsilon": 0.001,
        "gamma": "scale"
    }

    META_GBR_CONFIG = {
        "n_estimators": 500,
        "max_depth": 3,
        "learning_rate": 0.02,
        "subsample": 0.75,
        "random_state": 42
    }

    # Sequence Parameters
    N_PREV = 60  # Lookback window
    HORIZON = 7  # Forecast horizon

    # Training
    SEEDS = [7, 17, 42, 73, 101]
    N_SPLITS = 5  # Time series CV splits
    TARGET_OOF_FRAC = 0.20
    EPOCHS = 70
    BATCH_SIZE = 32
    PATIENCE = 10

    # Default Stock & Exogenous
    DEFAULT_EXOGENOUS = ["^JKSE", "USDIDR=X", "BZ=F", "GC=F"]


class LoggingConfig:
    """Logging configuration"""
    LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = BASE_DIR / 'logs'
    LOG_FILE = LOG_DIR / 'trading_system.log'

    # Ensure log directory exists
    LOG_DIR.mkdir(exist_ok=True)

    FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


class PathConfig:
    """Path configuration"""
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / 'data'
    ARTIFACTS_DIR = BASE_DIR / 'artifacts'
    REPORTS_DIR = BASE_DIR / 'reports'

    # Ensure directories exist
    for directory in [DATA_DIR, ARTIFACTS_DIR, REPORTS_DIR]:
        directory.mkdir(exist_ok=True)


# Export commonly used configs
db_config = DatabaseConfig()
trading_config = TradingConfig()
ml_config = MLConfig()
logging_config = LoggingConfig()
path_config = PathConfig()
