"""
01b_ingest_postgres_to_csv.py
---------------------------------
Extracts, aggregates, and exports key user and report metrics from PostgreSQL into CSV files.
"""

import logging
import os
from pathlib import Path
import sys

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR if (SCRIPT_DIR / "config.py").exists() else SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    CONNECT_TIMEOUT_SECONDS,
    LOG_FILE_PATH,
    POSTGRES_URL,
    ACCOUNTS_PER_DAY_CSV_PATH,
    AUTHENTICATED_RUNS_CSV_PATH,
    REPORTS_PER_USER_CSV_PATH,
)

LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("dashboard")


def get_postgres_engine(postgres_url: str):
    """Establishes and returns a SQLAlchemy Engine for PostgreSQL."""
    try:
        engine = create_engine(
            postgres_url,
            connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
        )
        with engine.connect() as conn:
            logger.info("Successfully connected and authenticated with PostgreSQL")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        sys.exit(1)


def get_export_queries() -> dict[str, str]:
    """Returns a dictionary mapping target CSV file paths to their SQL queries."""

    return {
        ACCOUNTS_PER_DAY_CSV_PATH: """
            SELECT 
                DATE(created_at) AS date,
                COUNT(*)::INT AS new_accounts,
                SUM(COUNT(*)) OVER (ORDER BY DATE(created_at))::INT AS cumulative_accounts
            FROM users
            GROUP BY DATE(created_at)
            ORDER BY date;
        """,
        REPORTS_PER_USER_CSV_PATH: """
            SELECT 
                owner_id,
                COUNT(*)::INT AS total_reports,
                MIN(created_at) AS first_report_date,
                MAX(created_at) AS latest_report_date
            FROM reports
            WHERE owner_id IS NOT NULL
            GROUP BY owner_id;
        """,
        AUTHENTICATED_RUNS_CSV_PATH: """
            SELECT 
                task_id,
                owner_id,
                comparison_type,
                source,
                created_at AS run_timestamp
            FROM reports;
        """,
    }

def export_query_to_csv(engine, query: str, output_path: str) -> None:
    """Executes a SQL aggregation query and exports the DataFrame to CSV atomically."""

    output_path = Path(output_path)
    
    temp_path = output_path.with_name(f"{output_path.name}.tmp")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df = pd.read_sql(query, con=engine)
        logger.info(f"Query executed successfully ({len(df)} rows fetched)")

        df.to_csv(temp_path, index=False, encoding="utf-8")

        temp_path.replace(output_path)

        logger.info(f"Exported data saved successfully to '{output_path}'")

    except SQLAlchemyError as e:
        logger.error(f"Database query error during export to '{output_path}': {e}")
        if temp_path.exists():
            temp_path.unlink()
        sys.exit(1)
    except (OSError, Exception) as e:
        logger.error(f"File writing error during export to '{output_path}': {e}")
        if temp_path.exists():
            temp_path.unlink()
        sys.exit(1)


def main() -> None:
    """Main execution flow for PostgreSQL extraction to CSV."""

    logger.info("Starting Script 01b_ingest_postgres_to_csv")

    engine = get_postgres_engine(POSTGRES_URL)
    queries = get_export_queries()

    for target_path, query in queries.items():
        filename = os.path.basename(target_path)
        logger.info(f"Processing export for: '{filename}'")
        export_query_to_csv(engine, query, target_path)

    logger.info("Script 01b_ingest_postgres_to_csv ended successfully")


if __name__ == "__main__":
    main()