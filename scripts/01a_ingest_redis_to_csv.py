"""
01a_ingest_redis_to_csv.py
--------------------------
Extracts and flattens RegCheck survey, task execution, and cost metrics 
directly from Redis Hashes and saves them as a deduplicated CSV file.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import pandas as pd
import redis

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import (
    CONNECT_TIMEOUT_SECONDS,
    LOG_FILE_PATH,
    REDIS_CSV_PATH,
    REDIS_SURVEY_HASH_PREFIX,
    REDIS_SURVEY_INDEX,
    REDIS_TASK_FIELDS,
    REDIS_URL,
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


def get_redis_client(redis_url: str) -> redis.Redis:
    """Establishes and tests a connection to Redis with explicit SSL/TLS parameters."""
    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=CONNECT_TIMEOUT_SECONDS,
            decode_responses=True,
            ssl_cert_reqs=None,
        )
        client.ping()
        logger.info("Successfully connected and authenticated with Redis.")
        return client
    except redis.RedisError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)


def parse_json_safely(raw_val: Optional[str]) -> Dict[str, Any]:
    """Safely parses a JSON string, returning an empty dict on failure."""
    if not raw_val:
        return {}
    try:
        parsed = json.loads(raw_val)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        return parsed if isinstance(parsed, dict) else {}
    except (json.JSONDecodeError, TypeError) as e:
        logger.debug(f"Failed to parse raw JSON payload: {e}")
        return {}


def fetch_survey_and_task_metrics(
    client: redis.Redis, batch_size: int = 500
) -> List[Dict[str, Any]]:
    """Iterates through Redis survey keys using pipeline batching and dynamic key definitions.

    Args:
        client (redis.Redis): Active Redis connection.
        batch_size (int): Number of task IDs to process per network round-trip.
    """
    records: List[Dict[str, Any]] = []

    try:
        task_ids = [
            task_id for task_id in client.sscan_iter(REDIS_SURVEY_INDEX, count=batch_size)
        ]

        if not task_ids:
            logger.warning(f"No task IDs found in '{REDIS_SURVEY_INDEX}'.")
            return records

        logger.info(f"Found {len(task_ids)} entries in Redis. Processing in batches of {batch_size}...")

        total_batches = (len(task_ids) - 1) // batch_size + 1

        for batch_idx, i in enumerate(range(0, len(task_ids), batch_size), start=1):
            chunk = task_ids[i : i + batch_size]

            pipe = client.pipeline(transaction=False)
            for task_id in chunk:
                pipe.hgetall(f"{REDIS_SURVEY_HASH_PREFIX}{task_id}")
                pipe.hmget(task_id, REDIS_TASK_FIELDS)

            results = pipe.execute()

            for j, task_id in enumerate(chunk):
                survey_data = results[j * 2] or {}
                task_raw = results[j * 2 + 1] or [None] * len(REDIS_TASK_FIELDS)

                task_data = dict(zip(REDIS_TASK_FIELDS, task_raw))

                settings_json = parse_json_safely(task_data.get("settings_json"))
                result_json = parse_json_safely(task_data.get("result_json"))
                cost_data = result_json.get("cost", {}) if isinstance(result_json, dict) else {}

                owner_id = task_data.get("owner_id")
                models_list = cost_data.get("models")

                record = {
                    "task_id": task_id,
                    "submitted_at": survey_data.get("submitted_at"),
                    "research_field": survey_data.get("research_field"),
                    "academic_position": survey_data.get("academic_position"),
                    "use_case": survey_data.get("use_case"),
                    "skipped": survey_data.get("skipped"),
                    "from_profile": survey_data.get("from_profile"),
                    "survey_comparison_type": survey_data.get("comparison_type"),
                    "state": task_data.get("state"),
                    "task_comparison_type": task_data.get("comparison_type"),
                    "total_dimensions": task_data.get("total_dimensions"),
                    "owner_id": owner_id,
                    "is_signed_in": bool(owner_id and str(owner_id).strip()),
                    "llm_client": settings_json.get("client"),
                    "parser_choice": settings_json.get("parser_choice"),
                    "reasoning_effort": settings_json.get("reasoning_effort"),
                    "cost_total_usd": cost_data.get("total_usd"),
                    "cost_llm_usd": cost_data.get("llm_usd"),
                    "cost_embedding_usd": cost_data.get("embedding_usd"),
                    "input_tokens": cost_data.get("input_tokens"),
                    "output_tokens": cost_data.get("output_tokens"),
                    "embedding_tokens": cost_data.get("embedding_tokens"),
                    "llm_calls": cost_data.get("llm_calls"),
                    "cost_estimate_complete": cost_data.get("estimate_complete"),
                    "models_used": ",".join(str(m) for m in models_list)
                    if isinstance(models_list, list)
                    else None,
                }
                records.append(record)

            if batch_idx % 5 == 0 or batch_idx == total_batches:
                logger.info(f"Processed batch {batch_idx}/{total_batches} ({len(records)} records extracted so far).")

        logger.info(f"Successfully processed {len(records)} total records from Redis.")
        return records

    except redis.RedisError as e:
        logger.error(f"Error reading from Redis: {e}")
        sys.exit(1)


def load_existing_archive(file_path: str) -> Optional[pd.DataFrame]:
    """Reads the existing historical CSV file if present. Hard-fails on read errors to protect historical data."""
    if not os.path.exists(file_path):
        logger.info(f"No existing archive found at '{file_path}'. Starting fresh.")
        return None

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Successfully loaded existing archive with {len(df)} records.")
        return df
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to read existing archive at '{file_path}': {e}. "
            f"Aborting process to prevent data corruption/loss."
        )
        sys.exit(1)


def merge_dataframes(
    existing_df: Optional[pd.DataFrame], new_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """Combines new records with the existing archive DataFrame."""
    new_df = pd.DataFrame(new_records)

    if existing_df is None or existing_df.empty:
        return new_df

    if new_df.empty:
        return existing_df

    return pd.concat([existing_df, new_df], ignore_index=True)


def deduplicate_dataframe(df: pd.DataFrame, primary_key: str = "task_id") -> pd.DataFrame:
    """Deduplicates records by primary key, keeping the latest entry."""
    if df.empty:
        return df

    initial_count = len(df)
    if primary_key in df.columns:
        deduped_df = df.drop_duplicates(subset=[primary_key], keep="last")
    else:
        logger.warning(
            f"Primary key '{primary_key}' not found in columns. Falling back to full-row deduplication."
        )
        deduped_df = df.drop_duplicates()

    retained_count = len(deduped_df)
    logger.info(
        f"Deduplication complete: {initial_count - retained_count} duplicate records removed. "
        f"Retained records: {retained_count}."
    )
    return deduped_df


def save_df_atomically(df: pd.DataFrame, output_path: str) -> None:
    """Writes DataFrame to a temporary file before replacing destination file."""
    temp_path = f"{output_path}.tmp"
    try:
        df.to_csv(temp_path, index=False, encoding="utf-8")
        os.replace(temp_path, output_path)
        logger.info(f"Successfully saved {len(df)} total records to '{output_path}'.")
    except (OSError, Exception) as e:
        logger.error(f"Failed to write file to '{output_path}': {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)


def main() -> None:
    """Main execution flow for Redis to CSV pipeline."""
    logger.info("Starting Script 01a: Redis Hash Ingestion...")

    client = get_redis_client(REDIS_URL)

    records = fetch_survey_and_task_metrics(client, batch_size=500)
    if not records and not os.path.exists(REDIS_CSV_PATH):
        logger.warning("No new records fetched and no existing archive exists. Exiting.")
        return

    existing_df = load_existing_archive(REDIS_CSV_PATH)

    combined_df = merge_dataframes(existing_df, records)

    final_df = deduplicate_dataframe(combined_df, primary_key="task_id")

    save_df_atomically(final_df, REDIS_CSV_PATH)

    logger.info("Script 01a finished successfully.")


if __name__ == "__main__":
    main()