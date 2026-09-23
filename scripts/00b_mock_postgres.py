"""
01b_mock_postgres.py
--------------------
Generates mock PostgreSQL metrics and exports them into CSV files.
"""

import csv
import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR if os.path.exists(os.path.join(SCRIPT_DIR, "mock_config.py")) else os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mock_config import (
    NUM_USERS,
    CSV_PATH,
    SIMULATION_LOG_PATH,
    COMPARISON_TYPES,
    EXECUTION_SOURCES
)

# Logging configuration
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]
os.makedirs(os.path.dirname(SIMULATION_LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] [ENV: SIMULATION] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(SIMULATION_LOG_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(SCRIPT_NAME)


def write_csv_atomically(
    data: list, fieldnames: list, output_path: str
) -> None:
    """Exports a list of dictionary records to a CSV file using an atomic write pattern."""
    temp_path = f"{output_path}.tmp"

    try:
        target_dir = os.path.dirname(output_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        with open(temp_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        os.replace(temp_path, output_path)
        logger.info(
            f"Successfully exported {len(data)} rows to '{output_path}'."
        )

    except (OSError, Exception) as e:
        logger.error(
            f"File writing error during mock export to '{output_path}': {e}"
        )
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)


def generate_accounts_per_day() -> list:
    """Generates synthetic daily account creation metrics."""
    records = []
    base_time = datetime.now() - timedelta(days=60)
    cumulative = 0

    for day in range(60):
        current_date = (base_time + timedelta(days=day)).strftime("%Y-%m-%d")
        new_acc = random.randint(1, 10)
        cumulative += new_acc

        records.append(
            {
                "date": current_date,
                "new_accounts": int(new_acc),
                "cumulative_accounts": int(cumulative),
            }
        )
    return records


def generate_reports_per_user(owner_pool: list) -> list:
    """Generates synthetic aggregated report activity metrics per user account."""
    records = []
    base_time = datetime.now() - timedelta(days=60)

    for owner_id in owner_pool:
        total_reports = random.randint(1, 25)
        first_date = (
            base_time + timedelta(days=random.randint(0, 20))
        ).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00"
        
        latest_date = (
            datetime.now() - timedelta(days=random.randint(0, 5))
        ).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00"

        records.append(
            {
                "owner_id": owner_id,
                "total_reports": int(total_reports),
                "first_report_date": first_date,
                "latest_report_date": latest_date,
            }
        )
    return records


def generate_authenticated_runs(owner_pool: list) -> list:
    """Generates granular event execution logs for individual report runs.

    Simulates task execution instances, linking each run to a specific owner, 
    comparison evaluation type, execution source, and ISO timestamp.

    Args:
        owner_pool (List[str]): A list of string user identifiers (e.g., 'usr_100').

    Returns:
        List[Dict]: A list of dictionaries containing 'task_id', 'owner_id', 
            'comparison_type', 'source', and 'run_timestamp' keys.
    """
    records = []
    base_time = datetime.now() - timedelta(days=60)

    for i in range(1, 150):
        records.append(
            {
                "task_id": str(uuid.uuid4()),
                "owner_id": random.choice(owner_pool),
                "comparison_type": random.choice(COMPARISON_TYPES),
                "source": random.choice(EXECUTION_SOURCES),
                "run_timestamp": (
                    base_time + timedelta(hours=random.randint(1, 1440))
                ).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00",
            }
        )
    return records


def main() -> None:
    logger.info("Starting Script 01b (Mock): PostgreSQL Simulation Export...")

    owner_pool = [str(uuid.uuid4()) for _ in range(NUM_USERS)]

    accounts_data = generate_accounts_per_day()
    write_csv_atomically(
        data=accounts_data,
        fieldnames=["date",
                    "new_accounts",
                    "cumulative_accounts"
        ],
        output_path=os.path.join(CSV_PATH, "accounts_per_day.csv"),
    )

    reports_user_data = generate_reports_per_user(owner_pool)
    write_csv_atomically(
        data=reports_user_data,
        fieldnames=[
            "owner_id",
            "total_reports",
            "first_report_date",
            "latest_report_date",
        ],
        output_path=os.path.join(CSV_PATH, "reports_per_user.csv"),
    )

    runs_data = generate_authenticated_runs(owner_pool)
    write_csv_atomically(
        data=runs_data,
        fieldnames=[
            "task_id",
            "owner_id",
            "comparison_type",
            "source",
            "run_timestamp",
        ],
        output_path=os.path.join(CSV_PATH, "authenticated_runs.csv"),
    )

    logger.info(
        "Script 01b (Mock) finished successfully. All simulation CSVs updated."
    )


if __name__ == "__main__":
    main()