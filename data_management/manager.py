"""
High-level data management operations
"""
import pandas as pd
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_management.fetcher import DataFetcher
from utils.database import (
    create_table_like,
    insert_dataframe,
    insert_or_update_latest,
    table_exists
)
from utils.logger import get_logger
from utils.helpers import chunks

logger = get_logger(__name__)


class DataManager:
    """Manage stock data fetching and database storage"""

    def __init__(self, max_workers: int = 10):
        """
        Initialize data manager

        Args:
            max_workers: Maximum parallel workers for fetching
        """
        self.fetcher = DataFetcher()
        self.max_workers = max_workers

    def add_new_stock(self, symbol: str) -> bool:
        """
        Add a new stock to the database

        Args:
            symbol: Stock symbol

        Returns:
            True if successful, False otherwise
        """
        daily_table = f"{symbol}_Daily_Data"
        hourly_table = f"{symbol}_Hourly_Data"

        try:
            # Create tables if they don't exist
            if not table_exists(daily_table):
                create_table_like(daily_table, "stock_daily_data")

            if not table_exists(hourly_table):
                create_table_like(hourly_table, "stock_hourly_data")

            # Fetch and insert daily data
            daily_df = self.fetcher.fetch_daily_data(symbol)
            if daily_df is not None:
                insert_dataframe(daily_df, daily_table)
            else:
                logger.warning(f"No daily data available for {symbol}")
                return False

            # Fetch and insert hourly data (optional)
            hourly_df = self.fetcher.fetch_hourly_data(symbol)
            if hourly_df is not None:
                insert_dataframe(hourly_df, hourly_table)

            logger.info(f"Successfully added new stock: {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to add stock {symbol}: {e}")
            return False

    def update_stock_data(self, symbol: str) -> dict:
        """
        Update existing stock data with latest bars

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with update status
        """
        result = {
            'symbol': symbol,
            'daily_updated': False,
            'hourly_updated': False,
            'daily_rows': 0,
            'hourly_rows': 0,
            'error': None
        }

        daily_table = f"{symbol}_Daily_Data"
        hourly_table = f"{symbol}_Hourly_Data"

        try:
            # Update daily data
            daily_df = self.fetcher.fetch_daily_data(symbol)
            if daily_df is not None:
                rows = insert_or_update_latest(daily_df, daily_table, 'date')
                result['daily_rows'] = rows
                result['daily_updated'] = rows > 0

            # Update hourly data
            hourly_df = self.fetcher.fetch_hourly_data(symbol)
            if hourly_df is not None:
                rows = insert_or_update_latest(hourly_df, hourly_table, 'datetime')
                result['hourly_rows'] = rows
                result['hourly_updated'] = rows > 0

        except Exception as e:
            logger.error(f"Failed to update {symbol}: {e}")
            result['error'] = str(e)

        return result

    def bulk_add_stocks(self, symbols: List[str], batch_size: int = 50) -> dict:
        """
        Add multiple new stocks in parallel

        Args:
            symbols: List of stock symbols
            batch_size: Number of stocks to process in each batch

        Returns:
            Summary statistics
        """
        results = {
            'total': len(symbols),
            'success': 0,
            'failed': 0,
            'failed_symbols': []
        }

        # Process in batches to manage memory
        for batch in chunks(symbols, batch_size):
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.add_new_stock, sym): sym for sym in batch}

                for future in as_completed(futures):
                    symbol = futures[future]
                    try:
                        if future.result():
                            results['success'] += 1
                        else:
                            results['failed'] += 1
                            results['failed_symbols'].append(symbol)
                    except Exception as e:
                        logger.error(f"Exception for {symbol}: {e}")
                        results['failed'] += 1
                        results['failed_symbols'].append(symbol)

        logger.info(
            f"Bulk add complete: {results['success']} successful, "
            f"{results['failed']} failed out of {results['total']}"
        )
        return results

    def bulk_update_stocks(self, symbols: List[str], batch_size: int = 50) -> pd.DataFrame:
        """
        Update multiple stocks in parallel

        Args:
            symbols: List of stock symbols
            batch_size: Number of stocks to process in each batch

        Returns:
            DataFrame with update results
        """
        all_results = []

        for batch in chunks(symbols, batch_size):
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.update_stock_data, sym): sym for sym in batch}

                for future in as_completed(futures):
                    try:
                        result = future.result()
                        all_results.append(result)
                    except Exception as e:
                        symbol = futures[future]
                        logger.error(f"Exception updating {symbol}: {e}")
                        all_results.append({
                            'symbol': symbol,
                            'error': str(e)
                        })

        results_df = pd.DataFrame(all_results)

        # Summary
        total_daily = results_df['daily_rows'].sum()
        total_hourly = results_df['hourly_rows'].sum()
        logger.info(
            f"Bulk update complete: {total_daily} daily rows, "
            f"{total_hourly} hourly rows added across {len(symbols)} symbols"
        )

        return results_df


def load_symbols_from_file(file_path: str, column_name: str = 'Stock_Name') -> List[str]:
    """
    Load stock symbols from text/CSV file

    Args:
        file_path: Path to file
        column_name: Column containing symbols

    Returns:
        List of symbols
    """
    try:
        df = pd.read_csv(file_path)
        symbols = df[column_name].dropna().astype(str).str.strip().tolist()
        logger.info(f"Loaded {len(symbols)} symbols from {file_path}")
        return symbols
    except Exception as e:
        logger.error(f"Failed to load symbols from {file_path}: {e}")
        return []
