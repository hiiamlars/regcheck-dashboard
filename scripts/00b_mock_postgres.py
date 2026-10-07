"""
01b_mock_postgres.py
--------------------
Generates mock PostgreSQL metrics and exports them into CSV files.
"""

import csv
import logging
from pathlib import Path
import random
import sys
from typing import Union
import uuid
from datetime import datetime, timedelta, timezone

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR if (SCRIPT_DIR / "config.py").exists() else SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    ACCOUNTS_PER_DAY_CSV_PATH,
    AUTHENTICATED_RUNS_CSV_PATH,
    REPORTS_PER_USER_CSV_PATH,
    LOG_FILE_PATH,
    DAYS,
    get_shared_owner_pool,
)

COMPARISON_TYPES = [
    "general_preregistration",
    "clinical trials",
]

EXECUTION_SOURCES = [
    "api",
    "ui",
]

FIRST_REPORT_DAY_OFFSET_RANGE = (0, max(1, int(0.15 * DAYS)))

LATEST_REPORT_DAY_OFFSET_RANGE = (0, max(1, int(0.85 * DAYS)))

NEW_ACCOUNTS_DAILY_RANGE = (1, 10)

REPORTS_PER_USER_RANGE = (1, 50)

TOTAL_AUTHENTICATED_RUNS = 150

LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] [ENV: SIMULATION] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("dashboard")


def write_csv_atomically(data: list[dict], output_path: Union[str, Path]) -> None:
    """Exports a list of dictionary records to a CSV file using an atomic write pattern."""

    output_path = Path(output_path)

    if not data:
        logger.warning(f"No records provided to export for '{output_path}'. Skipping")
        return

    fieldnames = list(data[0].keys())
    temp_path = output_path.with_name(f"{output_path.name}.tmp")
    
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        temp_path.replace(output_path)
        logger.info(
            f"Successfully exported {len(data)} rows to '{output_path}'"
        )

    except Exception:
        logger.exception(
            f"File writing error during mock export to '{output_path}'")
        if temp_path.exists():
            temp_path.unlink()
        sys.exit(1)


def generate_accounts_per_day() -> list[dict]:
    """Generates synthetic daily account creation metrics."""
    records = []
    base_time = datetime.now(timezone.utc) - timedelta(days=DAYS)
    cumulative = 0

    for day in range(DAYS):
        current_date = (base_time + timedelta(days=day)).strftime("%Y-%m-%d")
        new_acc = random.randint(*NEW_ACCOUNTS_DAILY_RANGE)
        cumulative += new_acc

        records.append(
            {
                "date": current_date,
                "new_accounts": new_acc,
                "cumulative_accounts": cumulative,
            }
        )
    return records


def generate_reports_per_user(owner_pool: list[str]) -> list[dict]:
    """Generates synthetic aggregated report activity metrics per user account."""
    records = []
    base_time = datetime.now(timezone.utc) - timedelta(days=DAYS)

    for owner_id in owner_pool:
        total_reports = random.randint(*REPORTS_PER_USER_RANGE)
        first_offset = random.randint(*FIRST_REPORT_DAY_OFFSET_RANGE)
        first_date = (
            base_time + timedelta(days=first_offset)
        ).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00"

        latest_offset = random.randint(*LATEST_REPORT_DAY_OFFSET_RANGE)
        latest_date = (
            datetime.now(timezone.utc) - timedelta(days=latest_offset)
        ).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00"

        records.append(
            {
                "owner_id": owner_id,
                "total_reports": total_reports,
                "first_report_date": first_date,
                "latest_report_date": latest_date,
            }
        )
    return records


def generate_authenticated_runs(owner_pool: list[str]) -> list[dict]:
    """Generates granular event execution logs for individual report runs."""
    records = []
    base_time = datetime.now(timezone.utc) - timedelta(days=DAYS)
    max_offset_hours = DAYS * 24

    for _ in range(TOTAL_AUTHENTICATED_RUNS):
        records.append(
            {
                "task_id": str(uuid.uuid4()),
                "owner_id": random.choice(owner_pool),
                "comparison_type": random.choice(COMPARISON_TYPES),
                "source": random.choice(EXECUTION_SOURCES),
                "run_timestamp": (
                    base_time + timedelta(hours=random.randint(1, max_offset_hours))
                ).strftime("%Y-%m-%d %H:%M:%S.%f") + "+00:00",
            }
        )
    return records


def main() -> None:
    logger.info("Starting Script 00b_mock_postgres")

    owner_pool = get_shared_owner_pool()

    write_csv_atomically(
        data=generate_accounts_per_day(),
        output_path=ACCOUNTS_PER_DAY_CSV_PATH,
    )

    write_csv_atomically(
        data=generate_reports_per_user(owner_pool),
        output_path=REPORTS_PER_USER_CSV_PATH,
    )

    write_csv_atomically(
        data=generate_authenticated_runs(owner_pool),
        output_path=AUTHENTICATED_RUNS_CSV_PATH,
    )

    logger.info(
        "Script 00b_mock_postgres ended successfully"
    )


if __name__ == "__main__":
    main()