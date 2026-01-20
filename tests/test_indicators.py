"""
Test technical indicators
"""
import pytest
import pandas as pd
import numpy as np
from strategies.indicators import (
    sma, ema, rsi, atr, bollinger_bands,
    find_support_resistance, calculate_advt
)


@pytest.fixture
def sample_data():
    """Create sample OHLCV data"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100)
    close = 100 + np.cumsum(np.random.randn(100) * 2)
    high = close + np.abs(np.random.randn(100))
    low = close - np.abs(np.random.randn(100))
    open_price = close + np.random.randn(100) * 0.5
    volume = np.random.randint(1000000, 5000000, 100)

    return pd.DataFrame({
        'date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }).set_index('date')


def test_sma(sample_data):
    """Test Simple Moving Average"""
    result = sma(sample_data['close'], 20)

    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    # First 19 values should be NaN
    assert pd.isna(result.iloc[:19]).all()
    # Later values should not be NaN
    assert not pd.isna(result.iloc[20:]).any()


def test_ema(sample_data):
    """Test Exponential Moving Average"""
    result = ema(sample_data['close'], 20)

    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    # EMA should have values after first period
    assert not pd.isna(result.iloc[20:]).any()


def test_rsi(sample_data):
    """Test RSI calculation"""
    result = rsi(sample_data['close'], 14)

    assert isinstance(result, pd.Series)
    # RSI should be between 0 and 100
    valid_values = result.dropna()
    assert (valid_values >= 0).all()
    assert (valid_values <= 100).all()


def test_atr(sample_data):
    """Test ATR calculation"""
    result = atr(sample_data, 14)

    assert isinstance(result, pd.Series)
    assert len(result) == len(sample_data)
    # ATR should be positive
    assert (result.dropna() > 0).all()


def test_bollinger_bands(sample_data):
    """Test Bollinger Bands"""
    middle, upper, lower = bollinger_bands(sample_data['close'], 20, 2.0)

    assert isinstance(middle, pd.Series)
    assert isinstance(upper, pd.Series)
    assert isinstance(lower, pd.Series)

    # Upper should be above middle, middle above lower
    valid_idx = middle.dropna().index
    assert (upper[valid_idx] > middle[valid_idx]).all()
    assert (middle[valid_idx] > lower[valid_idx]).all()


def test_find_support_resistance(sample_data):
    """Test S/R level detection"""
    support, resistance = find_support_resistance(sample_data, lookback=50)

    assert isinstance(support, list)
    assert isinstance(resistance, list)
    # Should find some levels
    assert len(support) > 0 or len(resistance) > 0


def test_calculate_advt(sample_data):
    """Test ADVT calculation"""
    advt = calculate_advt(sample_data, period=20)

    assert isinstance(advt, (int, float))
    assert advt > 0
