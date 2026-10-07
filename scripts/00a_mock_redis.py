"""
00a_mock_redis.py
-----------------
Generates mock survey responses from REDIS and exports them into a CSV file.
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
    SURVEY_RESPONSE_CSV_PATH,
    LOG_FILE_PATH,
    DAYS,
    get_shared_owner_pool,
)

ACADEMIC_POSITIONS = [
    "Postdoc",
    "Masters",
    "Professor",
    None,
]

COST_PER_EMBEDDING = 0.00005

COST_PER_INPUT_TOKEN = 0.000003

COST_PER_OUTPUT_TOKEN = 0.000015

EMBEDDING_TOKEN_RANGE = (500, 10000)

FIELDNAMES = [
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

INPUT_TOKEN_RANGE = (1500, 4500)

LLM_CALLS_RANGE = (1, 12)

LLM_CLIENTS = ["openai", "claude", "qwen"]

MICROSECOND_RANGE = (0, 999999)

MODEL_COMBINATIONS = [
    "gpt-5.5,text-embedding-3-large",
    "qwen/qwen3.6-27b,text-embedding-3-large",
    "claude-opus-4-8,text-embedding-3-large",
]

NUM_RECORDS = 250

OUTPUT_TOKEN_RANGE = (200, 500)

PARSER = ["pymupdf"]

RANDOM_WEIGHTS = [0.8, 0.2]

REASONING_EFFORTS = ["low", 
                    "medium",
                    "high",]

RESEARCH_FIELDS = [
    "Psychology",
    "Medicine",
    "Other",
    None,
]

SURVEY_COMPARISON_TYPES = [
    "general preregistration",
    "clinical trials",
]

TASK_COMPARISON_TYPES = [0,1]

TOTAL_SIMULATION_SECONDS = 60 * 60 * 24 * DAYS

USE_CASES = [
    "Literature Review & Synthesis",
    "Data Extraction & Analysis",
    "Hypothesis Generation",
    "Drafting & Proofreading",
    "Code Generation for Experiments",
    None,
]

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


def write_csv_atomically(data: list[dict], fieldnames: list[str], output_path: Union[str, Path]) -> None:
    """Exports a list of dictionary records to a CSV file using an atomic write pattern."""

    output_path = Path(output_path)
    temp_path = output_path.with_name(f"{output_path.name}.tmp")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        temp_path.replace(output_path)
        logger.info(f"Successfully exported {len(data)} rows to '{output_path}'")

    except (OSError, Exception) as e:
        logger.error(f"File writing error during export to '{output_path}': {e}")
        if temp_path.exists():
            temp_path.unlink()
        sys.exit(1)

def generate_redis_data() -> None:
    """Generates synthetic Redis survey records matching production schema."""
    logger.info("Starting Script 00a_mock_redis")

    records = []
    base_time = datetime.now(timezone.utc) - timedelta(days=DAYS)
    
    owner_pool = get_shared_owner_pool()

    for _ in range(1, NUM_RECORDS + 1):
        task_id = str(uuid.uuid4())

        random_seconds = random.randint(1, TOTAL_SIMULATION_SECONDS)
        random_microseconds = random.randint(*MICROSECOND_RANGE)
        submitted_dt = base_time + timedelta(seconds=random_seconds, microseconds=random_microseconds)
        submitted_at = submitted_dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"

        state = random.choices([1, 0], weights=RANDOM_WEIGHTS, k=1)[0]
        skipped = 1 if state == 0 else random.choice([0, 1])
        from_profile = random.choice([0, 1])

        is_signed_in = random.choices([True, False], weights=RANDOM_WEIGHTS, k=1)[0]
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
            input_tokens = random.randint(*INPUT_TOKEN_RANGE)
            output_tokens = random.randint(*OUTPUT_TOKEN_RANGE)
            embedding_tokens = random.randint(*EMBEDDING_TOKEN_RANGE)
            cost_llm = round((input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN), 4)
            cost_embedding = round(embedding_tokens * COST_PER_EMBEDDING, 4)
            cost_total = round(cost_llm + cost_embedding, 4)

            record.update({
                "llm_client": random.choice(LLM_CLIENTS),
                "parser_choice": random.choice(PARSER),
                "reasoning_effort": random.choice(REASONING_EFFORTS),
                "cost_total_usd": cost_total,
                "cost_llm_usd": cost_llm,
                "cost_embedding_usd": cost_embedding,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "embedding_tokens": embedding_tokens,
                "llm_calls": random.randint(*LLM_CALLS_RANGE),
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

    write_csv_atomically(data=records, fieldnames=FIELDNAMES, output_path=SURVEY_RESPONSE_CSV_PATH)
    logger.info("Script 00a_mock_redis ended successfully")


if __name__ == "__main__":
    generate_redis_data()