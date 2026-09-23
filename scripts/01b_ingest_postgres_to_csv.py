"""
01b_export_postgres_to_tableau.py
---------------------------------
Extracts, aggregates, and exports key user and report metrics from PostgreSQL
into CSV files.
"""

import logging
import os
import sys
from typing import Dict

from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    CONNECT_TIMEOUT_SECONDS,
    LOG_FILE_PATH,
    POSTGRES_URL,
    POSTGRES_CSV_PATH,
)

# Logging configuration
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(SCRIPT_NAME)


def get_postgres_engine(postgres_url: str):
    """Establishes and returns a SQLAlchemy Engine for PostgreSQL."""
    try:
        engine = create_engine(
            postgres_url,
            connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
        )
        with engine.connect() as conn:
            logger.info("Successfully connected and authenticated with PostgreSQL.")
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Failed to connect to PostgreSQL database: {e}")
        sys.exit(1)


def get_export_queries() -> Dict[str, str]:
    """Returns a dictionary mapping target CSV filenames to their SQL queries."""

    return {
            "accounts_per_day.csv": """
                SELECT 
                    DATE(created_at) AS date,
                    COUNT(*)::INT AS new_accounts,
                    SUM(COUNT(*)) OVER (ORDER BY DATE(created_at))::INT AS cumulative_accounts
                FROM users
                GROUP BY DATE(created_at)
                ORDER BY date;
            """,
            "reports_per_user.csv": """
                SELECT 
                    owner_id,
                    COUNT(*)::INT AS total_reports,
                    MIN(created_at) AS first_report_date,
                    MAX(created_at) AS latest_report_date
                FROM reports
                WHERE owner_id IS NOT NULL
                GROUP BY owner_id;
            """,
            "authenticated_runs.csv": """
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
    temp_path = f"{output_path}.tmp"

    try:
        target_dir = os.path.dirname(output_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        df = pd.read_sql(query, con=engine)
        logger.info(f"Query executed successfully ({len(df)} rows fetched).")

        df.to_csv(temp_path, index=False, encoding="utf-8")
        os.replace(temp_path, output_path)

        logger.info(f"Exported data saved successfully to '{output_path}'.")

    except SQLAlchemyError as e:
        logger.error(f"Database query error during export to '{output_path}': {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)
    except (OSError, Exception) as e:
        logger.error(f"File writing error during export to '{output_path}': {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)


def main() -> None:
    """Main execution flow for PostgreSQL extraction to Tableau CSVs."""
    logger.info("Starting Script 01b: PostgreSQL Export to Tableau CSVs...")

    engine = get_postgres_engine(POSTGRES_URL)
    queries = get_export_queries()

    for filename, query in queries.items():
        target_path = os.path.join(POSTGRES_CSV_PATH, filename)
        logger.info(f"Processing export for: '{filename}'")
        export_query_to_csv(engine, query, target_path)

    logger.info("Script 01b finished successfully. All Tableau CSV files updated.")


if __name__ == "__main__":
    main()