"""
Database utilities and connection management
"""
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import execute_values
from contextlib import contextmanager
from typing import Optional, List, Tuple, Dict, Any
import pandas as pd

from config.settings import DatabaseConfig
from utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Database connection pool manager for PostgreSQL
    """
    _instance = None
    _pool = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, min_conn: int = 1, max_conn: int = 10):
        """
        Initialize connection pool

        Args:
            min_conn: Minimum connections in pool
            max_conn: Maximum connections in pool
        """
        if self._pool is None:
            try:
                self._pool = pool.SimpleConnectionPool(
                    min_conn,
                    max_conn,
                    **DatabaseConfig.get_connection_params()
                )
                logger.info("Database connection pool initialized")
            except psycopg2.Error as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections

        Yields:
            Connection object from pool
        """
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._pool.putconn(conn)

    def close_all(self):
        """Close all connections in pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("All database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


def read_table(table_name: str) -> pd.DataFrame:
    """
    Read entire table into DataFrame

    Args:
        table_name: Name of the table

    Returns:
        DataFrame with table contents
    """
    with db_manager.get_connection() as conn:
        query = sql.SQL('SELECT * FROM public.{}').format(sql.Identifier(table_name))
        df = pd.read_sql(query, conn)
        logger.info(f"Read {len(df)} rows from table '{table_name}'")
        return df


def read_table_with_query(query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
    """
    Execute custom query and return DataFrame

    Args:
        query: SQL query string
        params: Optional query parameters

    Returns:
        DataFrame with query results
    """
    with db_manager.get_connection() as conn:
        df = pd.read_sql(query, conn, params=params)
        logger.debug(f"Query returned {len(df)} rows")
        return df


def table_exists(table_name: str) -> bool:
    """
    Check if table exists in database

    Args:
        table_name: Name of the table

    Returns:
        True if table exists, False otherwise
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s)",
                (table_name.lower(),)
            )
            return cur.fetchone()[0]


def create_table_like(new_table_name: str, template_table: str) -> bool:
    """
    Create new table with same structure as template

    Args:
        new_table_name: Name for the new table
        template_table: Existing table to copy structure from

    Returns:
        True if created, False if already exists
    """
    if table_exists(new_table_name):
        logger.info(f"Table '{new_table_name}' already exists")
        return False

    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get column definitions from template
            cur.execute(f'SELECT * FROM public."{template_table}" LIMIT 0')
            columns = [desc[0] for desc in cur.description]
            oid_types = [desc[1] for desc in cur.description]

            # Map OID to PostgreSQL types
            type_mapping = {
                16: "boolean", 20: "bigint", 21: "smallint",
                23: "integer", 25: "text", 700: "real",
                701: "double precision", 1114: "timestamp without time zone",
                1700: "numeric", 1082: "date", 1083: "time without time zone"
            }

            data_types = [type_mapping.get(oid, "text") for oid in oid_types]

            # Build CREATE TABLE statement
            column_defs = [
                sql.SQL('{} {}').format(sql.Identifier(col), sql.SQL(dt))
                for col, dt in zip(columns, data_types)
            ]

            create_query = sql.SQL("CREATE TABLE {} ({})").format(
                sql.Identifier(new_table_name),
                sql.SQL(',\n').join(column_defs)
            )

            cur.execute(create_query)
            conn.commit()
            logger.info(f"Table '{new_table_name}' created successfully")
            return True


def insert_dataframe(df: pd.DataFrame, table_name: str) -> int:
    """
    Insert DataFrame into table using COPY for efficiency

    Args:
        df: DataFrame to insert
        table_name: Target table name

    Returns:
        Number of rows inserted
    """
    if df.empty:
        logger.warning("Attempted to insert empty DataFrame")
        return 0

    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Convert datetime columns to strings
            df_copy = df.copy()
            for col in df_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')

            # Use StringIO for COPY
            from io import StringIO
            buffer = StringIO()
            df_copy.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
            buffer.seek(0)

            cur.copy_from(buffer, f'"{table_name}"', null='\\N', columns=df.columns.tolist())
            conn.commit()

            rows_inserted = len(df)
            logger.info(f"Inserted {rows_inserted} rows into '{table_name}'")
            return rows_inserted


def insert_or_update_latest(
    df: pd.DataFrame,
    table_name: str,
    date_column: str = 'date'
) -> int:
    """
    Insert only records newer than the latest date in table

    Args:
        df: DataFrame with new data
        table_name: Target table name
        date_column: Name of the date/datetime column

    Returns:
        Number of rows inserted
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            # Get latest date in table
            cur.execute(f'SELECT MAX({date_column}) FROM public."{table_name}"')
            last_date = cur.fetchone()[0]

            df = df.copy()
            df[date_column] = pd.to_datetime(df[date_column])

            if last_date is not None:
                # Filter for newer records
                new_data = df[df[date_column] > pd.Timestamp(last_date)]

                if new_data.empty:
                    logger.info(f"No new records to insert into '{table_name}'")
                    return 0

                # Prepare for batch insert
                if date_column == 'date':
                    new_data[date_column] = new_data[date_column].dt.date
                else:
                    new_data[date_column] = new_data[date_column].dt.strftime('%Y-%m-%d %H:%M:%S')

                # Batch insert using execute_values
                columns = new_data.columns.tolist()
                values = [tuple(row) for row in new_data.itertuples(index=False, name=None)]

                query = f'INSERT INTO public."{table_name}" ({", ".join(columns)}) VALUES %s'
                execute_values(cur, query, values)
                conn.commit()

                logger.info(f"Inserted {len(new_data)} new records into '{table_name}'")
                return len(new_data)
            else:
                # Table is empty, insert all
                return insert_dataframe(df, table_name)


def execute_query(query: str, params: Optional[Tuple] = None) -> None:
    """
    Execute a query without returning results (INSERT, UPDATE, DELETE, etc.)

    Args:
        query: SQL query string
        params: Optional query parameters
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            logger.debug(f"Executed query successfully")


def list_tables() -> List[str]:
    """
    Get list of all tables in public schema

    Returns:
        List of table names
    """
    with db_manager.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            tables = [row[0] for row in cur.fetchall()]
            return tables
