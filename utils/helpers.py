"""
General utility functions
"""
import os
import random
import numpy as np
import tensorflow as tf
from typing import Optional
import functools
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def set_random_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility across all libraries

    Args:
        seed: Random seed value
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    logger.info(f"Random seed set to {seed}")


def safe_calculation(default_return=None):
    """
    Decorator for safe calculations with error handling

    Args:
        default_return: Value to return on error (None, pd.Series, etc.)

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                if default_return is not None:
                    return default_return
                # Infer appropriate return type
                if args and isinstance(args[0], pd.Series):
                    return pd.Series(dtype=float, index=args[0].index)
                elif args and isinstance(args[0], pd.DataFrame):
                    return pd.DataFrame(index=args[0].index)
                return None
        return wrapper
    return decorator


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: list,
    min_rows: int = 1
) -> tuple[bool, str]:
    """
    Validate DataFrame has required structure

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required

    Returns:
        Tuple of (is_valid, error_message)
    """
    if df.empty:
        return False, "DataFrame is empty"

    if len(df) < min_rows:
        return False, f"Insufficient rows: {len(df)} < {min_rows}"

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        return False, f"Missing columns: {missing_cols}"

    return True, ""


def validate_ohlcv(df: pd.DataFrame, symbol: str = "") -> list[str]:
    """
    Validate OHLCV data quality

    Args:
        df: DataFrame with OHLCV data
        symbol: Stock symbol for logging

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    required_cols = ['open', 'high', 'low', 'close', 'volume']
    is_valid, msg = validate_dataframe(df, required_cols)
    if not is_valid:
        issues.append(msg)
        return issues

    # Check OHLC relationships
    invalid_bars = (
        (df['high'] < df['low']) |
        (df['close'] > df['high']) |
        (df['close'] < df['low']) |
        (df['open'] > df['high']) |
        (df['open'] < df['low'])
    )

    if invalid_bars.any():
        count = invalid_bars.sum()
        issues.append(f"{symbol}: {count} invalid OHLC bars detected")

    # Check for zero volume
    zero_vol_pct = (df['volume'] == 0).sum() / len(df)
    if zero_vol_pct > 0.1:
        issues.append(f"{symbol}: {zero_vol_pct:.1%} zero-volume days")

    # Check for extreme moves
    returns = df['close'].pct_change()
    extreme_pct = (returns.abs() > 0.5).sum() / len(df)
    if extreme_pct > 0.02:
        issues.append(f"{symbol}: {extreme_pct:.1%} extreme price moves (>50%)")

    return issues


def chunks(lst: list, n: int):
    """
    Yield successive n-sized chunks from list

    Args:
        lst: List to chunk
        n: Chunk size

    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def format_currency(amount: float, currency: str = "IDR") -> str:
    """
    Format currency amount for display

    Args:
        amount: Numeric amount
        currency: Currency code

    Returns:
        Formatted string
    """
    if currency == "IDR":
        return f"Rp {amount:,.0f}"
    return f"{currency} {amount:,.2f}"


def calculate_percentage_change(old: float, new: float) -> float:
    """
    Calculate percentage change between two values

    Args:
        old: Original value
        new: New value

    Returns:
        Percentage change
    """
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100


def round_to_lot(shares: float, lot_size: int = 100) -> int:
    """
    Round shares to nearest lot

    Args:
        shares: Number of shares
        lot_size: Lot size (default 100 for IDX)

    Returns:
        Rounded shares
    """
    return int(shares // lot_size) * lot_size
