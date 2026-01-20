"""
Test helper utilities
"""
import pytest
import numpy as np
import pandas as pd
from utils.helpers import (
    set_random_seed,
    validate_dataframe,
    validate_ohlcv,
    chunks,
    format_currency,
    calculate_percentage_change,
    round_to_lot
)


def test_set_random_seed():
    """Test random seed setting"""
    set_random_seed(42)
    r1 = np.random.rand()

    set_random_seed(42)
    r2 = np.random.rand()

    assert r1 == r2


def test_chunks():
    """Test list chunking"""
    data = list(range(10))
    chunked = list(chunks(data, 3))

    assert len(chunked) == 4
    assert chunked[0] == [0, 1, 2]
    assert chunked[-1] == [9]


def test_format_currency():
    """Test currency formatting"""
    assert format_currency(1000000, "IDR") == "Rp 1,000,000"
    assert format_currency(1234.56, "USD") == "USD 1,234.56"


def test_calculate_percentage_change():
    """Test percentage change calculation"""
    assert calculate_percentage_change(100, 110) == 10.0
    assert calculate_percentage_change(100, 90) == -10.0
    assert calculate_percentage_change(0, 100) == 0.0


def test_round_to_lot():
    """Test lot rounding"""
    assert round_to_lot(150) == 100
    assert round_to_lot(250) == 200
    assert round_to_lot(99) == 0
    assert round_to_lot(1050, lot_size=100) == 1000
