"""
01a_mock_redis.py
-----------------
Generates mock survey responses and exports them into a CSV file.
"""

import csv
import logging
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR if os.path.exists(os.path.join(SCRIPT_DIR, "mock_config.py")) else os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from mock_config import (
    ACADEMIC_POSITIONS,
    CSV_PATH,
    LLM_CLIENTS,
    MODEL_COMBINATIONS,
    NUM_RECORDS,
    REASONING_EFFORTS,
    RESEARCH_FIELDS,
    SIMULATION_LOG_PATH,
    SURVEY_COMPARISON_TYPES,
    TASK_COMPARISON_TYPES,
    USE_CASES,
)

# Logging Configuration
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
    data: List[Dict], fieldnames: List[str], output_path: str
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
        logger.info(f"Successfully exported {len(data)} rows to '{output_path}'.")

    except (OSError, Exception) as e:
        logger.error(f"File writing error during export to '{output_path}': {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)


def generate_redis_data() -> None:
    """Generates synthetic Redis survey records matching production schema."""
    logger.info("Starting Script 01a (Mock): Redis Ingestion Simulation...")

    records = []
    base_time = datetime.now(timezone.utc) - timedelta(days=60)
    
    owner_pool = [str(uuid.uuid4()) for _ in range(20)]

    for _ in range(1, NUM_RECORDS + 1):
        task_id = str(uuid.uuid4())

        random_seconds = random.randint(1, 60 * 24 * 60)
        random_microseconds = random.randint(0, 999999)
        submitted_dt = base_time + timedelta(seconds=random_seconds, microseconds=random_microseconds)
        submitted_at = submitted_dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"

        state = random.choices([1, 0], weights=[0.85, 0.15], k=1)[0]
        skipped = 1 if state == 0 else random.choice([0, 1])
        from_profile = random.choice([0, 1])

        is_signed_in = random.choices([True, False], weights=[0.8, 0.2], k=1)[0]
        owner_id = random.choice(owner_pool) if is_signed_in else None

        record = {
            "task_id": task_id,
            "submitted_at": submitted_at,
            "research_field": random.choice(RESEARCH_FIELDS),
            "academic_position": random.choice(ACADEMIC_POSITIONS),
            "use_case": random.choice(USE_CASES),
            "skipped": skipped,
            "from_profile": from_profile,
            "survey_comparison_type": random.choice(SURVEY_COMPARISON_TYPES),
            "state": state,
            "task_comparison_type": random.choice(TASK_COMPARISON_TYPES),
            "total_dimensions": random.choice([1, 2, 3]),
            "owner_id": owner_id,
            "is_signed_in": is_signed_in,
        }

        if is_signed_in:
            cost_llm = round(random.uniform(0.01, 1.20), 4)
            cost_embedding = round(random.uniform(0.0001, 0.02), 5)
            cost_total = round(cost_llm + cost_embedding, 4)

            record.update({
                "llm_client": random.choice(LLM_CLIENTS),
                "parser_choice": "pymupdf",
                "reasoning_effort": random.choice(REASONING_EFFORTS),
                "cost_total_usd": cost_total,
                "cost_llm_usd": cost_llm,
                "cost_embedding_usd": cost_embedding,
                "input_tokens": round(random.uniform(1500.0, 45000.0), 2),
                "output_tokens": round(random.uniform(200.0, 5000.0), 2),
                "embedding_tokens": round(random.uniform(500.0, 10000.0), 2),
                "llm_calls": random.randint(1, 12),
                "cost_estimate_complete": random.choice([True, False]),
                "models_used": random.choice(MODEL_COMBINATIONS),
            })
        else:
            record.update({
                "llm_client": None,
                "parser_choice": None,
                "reasoning_effort": None,
                "cost_total_usd": None,
                "cost_llm_usd": None,
                "cost_embedding_usd": None,
                "input_tokens": None,
                "output_tokens": None,
                "embedding_tokens": None,
                "llm_calls": None,
                "cost_estimate_complete": None,
                "models_used": None,
            })

        records.append(record)

    fieldnames = [
        "task_id",
        "submitted_at",
        "research_field",
        "academic_position",
        "use_case",
        "skipped",
        "from_profile",
        "survey_comparison_type",
        "state",
        "task_comparison_type",
        "total_dimensions",
        "owner_id",
        "is_signed_in",
        "llm_client",
        "parser_choice",
        "reasoning_effort",
        "cost_total_usd",
        "cost_llm_usd",
        "cost_embedding_usd",
        "input_tokens",
        "output_tokens",
        "embedding_tokens",
        "llm_calls",
        "cost_estimate_complete",
        "models_used",
    ]

    target_file = os.path.join(CSV_PATH, "survey_responses.csv")
    write_csv_atomically(data=records, fieldnames=fieldnames, output_path=target_file)
    logger.info("Script 01a (Mock) finished successfully. Redis simulation CSV updated.")


if __name__ == "__main__":
    generate_redis_data()