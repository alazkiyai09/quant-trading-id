"""
Technical indicators for trading strategies
"""
import numpy as np
import pandas as pd
from typing import Tuple

from utils.helpers import safe_calculation


@safe_calculation(default_return=None)
def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(period, min_periods=period).mean()


@safe_calculation(default_return=None)
def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


@safe_calculation(default_return=None)
def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index"""
    try:
        import talib
        return talib.RSI(series.values, timeperiod=period)
    except ImportError:
        delta = series.diff()
        up = delta.clip(lower=0).rolling(period).mean()
        down = (-delta.clip(upper=0)).rolling(period).mean()
        rs = up / down.replace(0, 1e-9)
        return 100 - (100 / (1 + rs))


@safe_calculation(default_return=None)
def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range"""
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0/period, adjust=False).mean()


@safe_calculation(default_return=None)
def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands

    Returns:
        Tuple of (middle, upper, lower)
    """
    middle = sma(series, period)
    std = series.rolling(period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return middle, upper, lower


@safe_calculation(default_return=None)
def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index"""
    try:
        import talib
        return talib.ADX(df['high'].values, df['low'].values, df['close'].values, timeperiod=period)
    except ImportError:
        high, low, close = df['high'], df['low'], df['close']

        tr1 = (high - low).abs()
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        plus_dm = (high - high.shift(1)).clip(lower=0)
        minus_dm = (low.shift(1) - low).clip(lower=0)

        tr_n = tr.ewm(alpha=1/period, adjust=False).mean()
        pdi = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / tr_n)
        mdi = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / tr_n)

        dx = (100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, 1e-9))
        return dx.ewm(alpha=1/period, adjust=False).mean()


@safe_calculation(default_return=None)
def macd(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD indicator

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


@safe_calculation(default_return=None)
def donchian_channel(
    df: pd.DataFrame,
    period: int = 20
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Donchian Channel

    Returns:
        Tuple of (upper, middle, lower)
    """
    upper = df['high'].rolling(period).max()
    lower = df['low'].rolling(period).min()
    middle = (upper + lower) / 2
    return upper, middle, lower


def find_swing_highs(df: pd.DataFrame, lookback: int = 2) -> pd.Series:
    """
    Find swing high points

    Args:
        df: DataFrame with 'high' column
        lookback: Number of bars to look back/forward

    Returns:
        Series with True at swing highs
    """
    high = df['high']
    swing_highs = pd.Series(False, index=df.index)

    for i in range(lookback, len(df) - lookback):
        is_high = True
        for j in range(1, lookback + 1):
            if high.iloc[i] <= high.iloc[i - j] or high.iloc[i] <= high.iloc[i + j]:
                is_high = False
                break
        swing_highs.iloc[i] = is_high

    return swing_highs


def find_swing_lows(df: pd.DataFrame, lookback: int = 2) -> pd.Series:
    """
    Find swing low points

    Args:
        df: DataFrame with 'low' column
        lookback: Number of bars to look back/forward

    Returns:
        Series with True at swing lows
    """
    low = df['low']
    swing_lows = pd.Series(False, index=df.index)

    for i in range(lookback, len(df) - lookback):
        is_low = True
        for j in range(1, lookback + 1):
            if low.iloc[i] >= low.iloc[i - j] or low.iloc[i] >= low.iloc[i + j]:
                is_low = False
                break
        swing_lows.iloc[i] = is_low

    return swing_lows


def find_support_resistance(
    df: pd.DataFrame,
    lookback: int = 120,
    swing_lookback: int = 2,
    buffer_pct: float = 0.002
) -> Tuple[list, list]:
    """
    Find support and resistance levels

    Args:
        df: DataFrame with OHLC data
        lookback: Lookback period for S/R
        swing_lookback: Lookback for swing points
        buffer_pct: Clustering buffer

    Returns:
        Tuple of (support_levels, resistance_levels)
    """
    df_window = df.tail(lookback)

    swing_highs = find_swing_highs(df_window, swing_lookback)
    swing_lows = find_swing_lows(df_window, swing_lookback)

    resistance_points = df_window.loc[swing_highs, 'high'].values
    support_points = df_window.loc[swing_lows, 'low'].values

    # Cluster nearby levels
    def cluster_levels(levels, buffer):
        if len(levels) == 0:
            return []
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if level <= current_cluster[-1] * (1 + buffer):
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]

        if current_cluster:
            clustered.append(np.mean(current_cluster))

        return clustered

    resistance = cluster_levels(resistance_points, buffer_pct)
    support = cluster_levels(support_points, buffer_pct)

    return support, resistance


def calculate_advt(df: pd.DataFrame, period: int = 20) -> float:
    """
    Calculate Average Daily Value Traded

    Args:
        df: DataFrame with close and volume
        period: Lookback period

    Returns:
        ADVT value
    """
    recent = df.tail(period)
    daily_value = recent['close'] * recent['volume']
    return daily_value.mean()
