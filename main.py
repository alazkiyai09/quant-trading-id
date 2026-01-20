"""
Main entry point for the trading system
"""
import argparse
import sys
from pathlib import Path

from config.settings import path_config, trading_config, ml_config
from utils.logger import get_logger
from utils.database import db_manager

logger = get_logger(__name__)


def update_data(symbols_file: str = None, max_workers: int = 10):
    """Update stock data from Yahoo Finance"""
    from data_management.manager import DataManager, load_symbols_from_file

    logger.info("Starting data update process")

    # Load symbols
    if symbols_file:
        symbols = load_symbols_from_file(symbols_file)
    else:
        symbols_path = path_config.BASE_DIR / "Stock_list.txt"
        if symbols_path.exists():
            symbols = load_symbols_from_file(str(symbols_path))
        else:
            logger.error("No symbols file found. Please specify with --symbols")
            return

    if not symbols:
        logger.error("No symbols loaded")
        return

    # Update data
    manager = DataManager(max_workers=max_workers)
    results = manager.bulk_update_stocks(symbols)

    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("Update Summary:")
    logger.info(f"  Total symbols: {len(symbols)}")
    logger.info(f"  Daily rows added: {results['daily_rows'].sum()}")
    logger.info(f"  Hourly rows added: {results['hourly_rows'].sum()}")
    logger.info(f"{'='*60}")

    # Save report
    report_path = path_config.REPORTS_DIR / f"data_update_{pd.Timestamp.now():%Y%m%d_%H%M%S}.csv"
    results.to_csv(report_path, index=False)
    logger.info(f"Report saved to {report_path}")


def train_models(stock: str, exo_tickers: list = None):
    """Train ML models for a stock"""
    import pandas as pd
    from utils.database import read_table
    from ml_prediction.features import preprocess_stock_data
    from ml_prediction.trainer import train_multiseed_ensemble, save_artifacts

    logger.info(f"Training models for {stock}")

    # Load stock data
    stock_table = f"{stock}_Daily_Data"
    logger.info(f"Loading data from {stock_table}")
    stock_data = read_table(stock_table)

    if stock_data.empty:
        logger.error(f"No data found for {stock}")
        return

    # Load exogenous data
    if exo_tickers is None:
        exo_tickers = ml_config.DEFAULT_EXOGENOUS

    exo_dict = {}
    for ticker in exo_tickers:
        try:
            exo_table = f"{ticker}_Daily_Data"
            exo_data = read_table(exo_table)
            if not exo_data.empty:
                exo_dict[ticker] = exo_data
        except Exception as e:
            logger.warning(f"Could not load exogenous data for {ticker}: {e}")

    # Preprocess
    logger.info("Preprocessing data")
    processed = preprocess_stock_data(stock_data, exo_dict)

    # Get feature columns
    feature_cols = [c for c in processed.columns
                   if c not in ['close', 'high', 'low', 'open', 'volume']]

    logger.info(f"Using {len(feature_cols)} features")

    # Train
    logger.info("Starting multi-seed training")
    artifacts = train_multiseed_ensemble(
        data=processed,
        feature_cols=feature_cols
    )

    # Save
    output_path = path_config.ARTIFACTS_DIR / f"{stock}_ensemble.pkl"
    save_artifacts(artifacts, str(output_path))

    logger.info(f"\nTraining complete! Artifacts saved to {output_path}")


def predict(stock: str, n_days: int = 7):
    """Generate predictions for a stock"""
    import pandas as pd
    from utils.database import read_table
    from ml_prediction.features import preprocess_stock_data
    from ml_prediction.predictor import MultiSeedPredictor, walk_forward_forecast
    from ml_prediction.trainer import load_artifacts

    logger.info(f"Generating {n_days}-day forecast for {stock}")

    # Load artifacts
    artifact_path = path_config.ARTIFACTS_DIR / f"{stock}_ensemble.pkl"
    if not artifact_path.exists():
        logger.error(f"No trained model found at {artifact_path}")
        logger.info(f"Please run: python main.py train --stock {stock}")
        return

    artifacts = load_artifacts(str(artifact_path))

    # Load and preprocess data
    stock_data = read_table(f"{stock}_Daily_Data")

    exo_tickers = ml_config.DEFAULT_EXOGENOUS
    exo_dict = {ticker: read_table(f"{ticker}_Daily_Data")
                for ticker in exo_tickers}

    processed = preprocess_stock_data(stock_data, exo_dict)

    # Generate forecast
    if n_days <= 7:
        # Single prediction
        predictor = MultiSeedPredictor(artifacts)
        returns, prices = predictor.predict(processed, aggregation='weighted')

        logger.info(f"\n{stock} {n_days}-day Forecast:")
        logger.info(f"Current price: {processed['close'].iloc[-1]:.2f}")
        for i, price in enumerate(prices[:n_days], 1):
            logger.info(f"  Day {i}: {price:.2f}")
    else:
        # Walk-forward forecast
        returns, prices = walk_forward_forecast(processed, artifacts, n_days)

        logger.info(f"\n{stock} {n_days}-day Walk-Forward Forecast:")
        logger.info(f"Current price: {processed['close'].iloc[-1]:.2f}")
        logger.info(f"Day 7: {prices[6]:.2f}")
        logger.info(f"Day 14: {prices[13]:.2f}" if len(prices) > 13 else "")
        logger.info(f"Day 30: {prices[29]:.2f}" if len(prices) > 29 else "")
        logger.info(f"Final ({n_days} days): {prices[-1]:.2f}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Indonesian Stock Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Update data command
    update_parser = subparsers.add_parser('update', help='Update stock data')
    update_parser.add_argument('--symbols', type=str, help='Path to symbols file')
    update_parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train ML models')
    train_parser.add_argument('--stock', type=str, required=True, help='Stock symbol')
    train_parser.add_argument('--exo', nargs='+', help='Exogenous tickers')

    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Generate predictions')
    predict_parser.add_argument('--stock', type=str, required=True, help='Stock symbol')
    predict_parser.add_argument('--days', type=int, default=7, help='Forecast horizon')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'update':
            update_data(args.symbols, args.workers)

        elif args.command == 'train':
            train_models(args.stock, args.exo)

        elif args.command == 'predict':
            predict(args.stock, args.days)

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        # Cleanup
        db_manager.close_all()


if __name__ == '__main__':
    main()
