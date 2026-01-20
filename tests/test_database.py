"""
Test database utilities
"""
import pytest
import pandas as pd
from utils.database import (
    db_manager,
    table_exists,
    read_table,
    validate_dataframe,
    validate_ohlcv
)


def test_connection():
    """Test database connection"""
    with db_manager.get_connection() as conn:
        assert conn is not None
        assert not conn.closed


def test_validate_dataframe():
    """Test DataFrame validation"""
    # Valid DataFrame
    df = pd.DataFrame({
        'close': [100, 101, 102],
        'volume': [1000, 1100, 1200]
    })
    is_valid, msg = validate_dataframe(df, ['close', 'volume'])
    assert is_valid
    assert msg == ""

    # Empty DataFrame
    empty_df = pd.DataFrame()
    is_valid, msg = validate_dataframe(empty_df, ['close'])
    assert not is_valid
    assert "empty" in msg.lower()

    # Missing columns
    is_valid, msg = validate_dataframe(df, ['close', 'open'])
    assert not is_valid
    assert "missing" in msg.lower()


def test_validate_ohlcv():
    """Test OHLCV validation"""
    # Valid OHLCV
    df = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [102, 103, 104],
        'low': [99, 100, 101],
        'close': [101, 102, 103],
        'volume': [1000, 1100, 1200]
    })

    issues = validate_ohlcv(df, "TEST")
    assert len(issues) == 0

    # Invalid OHLC (high < low)
    bad_df = pd.DataFrame({
        'open': [100],
        'high': [99],  # High < Low
        'low': [101],
        'close': [100],
        'volume': [1000]
    })

    issues = validate_ohlcv(bad_df, "BAD")
    assert len(issues) > 0


@pytest.mark.skip(reason="Requires actual database setup")
def test_read_table():
    """Test reading table from database"""
    # This would require an actual table in the database
    df = read_table("^JKSE_Daily_Data")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
