"""
Data fetching from external sources (Yahoo Finance, etc.)
"""
import yfinance as yf
import pandas as pd
from typing import Optional
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class DataFetcher:
    """Fetch stock data from Yahoo Finance"""

    def __init__(self, market_suffix: str = ".JK"):
        """
        Initialize data fetcher

        Args:
            market_suffix: Market suffix for Yahoo Finance (e.g., ".JK" for Jakarta)
        """
        self.market_suffix = market_suffix

    def fetch_daily_data(
        self,
        symbol: str,
        period: str = "max",
        auto_adjust: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Fetch daily OHLCV data

        Args:
            symbol: Stock symbol (without market suffix)
            period: Time period (max, 1y, 5y, etc.)
            auto_adjust: Whether to auto-adjust prices

        Returns:
            DataFrame with daily data or None if failed
        """
        try:
            ticker_symbol = symbol + self.market_suffix
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period=period, interval="1d", auto_adjust=auto_adjust)

            if df.empty:
                logger.warning(f"No daily data returned for {symbol}")
                return None

            # Standardize columns
            df = df.reset_index().rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Clean timezone
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)

            df['date'] = df['timestamp'].dt.date

            result = df[['date', 'close', 'high', 'low', 'open', 'volume']].copy()
            logger.info(f"Fetched {len(result)} daily bars for {symbol}")
            return result

        except Exception as e:
            logger.error(f"Failed to fetch daily data for {symbol}: {e}")
            return None

    def fetch_hourly_data(
        self,
        symbol: str,
        period: str = "30d",
        interval: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch hourly OHLCV data

        Args:
            symbol: Stock symbol (without market suffix)
            period: Time period
            interval: Data interval (1h, 90m, etc.)

        Returns:
            DataFrame with hourly data or None if failed/unavailable
        """
        ticker_symbol = symbol + self.market_suffix

        # Try multiple combinations for illiquid stocks
        attempts = [
            (period, interval),
            ("60d", "1h"),
            ("30d", "90m")
        ]

        for p, i in attempts:
            try:
                ticker = yf.Ticker(ticker_symbol)
                df = ticker.history(period=p, interval=i, auto_adjust=False)

                if df is not None and not df.empty:
                    df = df.reset_index().rename(columns={
                        'Datetime': 'timestamp',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })

                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
                    df['timestamp'] = df['timestamp'].dt.tz_localize(None)
                    df['datetime'] = df['timestamp']

                    result = df[['datetime', 'close', 'high', 'low', 'open', 'volume']].copy()
                    logger.info(f"Fetched {len(result)} hourly bars for {symbol}")
                    return result

            except Exception as e:
                logger.debug(f"Hourly fetch attempt failed for {symbol} ({p}/{i}): {e}")
                continue

        logger.info(f"No hourly data available for {symbol} (suspended/illiquid)")
        return None

    def fetch_multiple_daily(self, symbols: list[str]) -> dict[str, pd.DataFrame]:
        """
        Fetch daily data for multiple symbols

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        results = {}
        for symbol in symbols:
            df = self.fetch_daily_data(symbol)
            if df is not None:
                results[symbol] = df

        logger.info(f"Fetched daily data for {len(results)}/{len(symbols)} symbols")
        return results
