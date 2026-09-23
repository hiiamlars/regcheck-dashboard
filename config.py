"""
config.py
---------
Central configuration for paths, constants, and environment variables.
"""

import logging
import os
import sys
from dotenv import load_dotenv

# Path configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

ENV_FILE_PATH = os.path.join(PROJECT_ROOT, ".env")
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "logs", "pipeline.log")

# Output Paths (Direct CSV Exports)
REDIS_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "production", "survey_responses.csv")
POSTGRES_CSV_PATH = os.path.join(PROJECT_ROOT, "data", "production")

# Ensure required directories exist
for path in [
    LOG_FILE_PATH,
    REDIS_CSV_PATH,
    POSTGRES_CSV_PATH,
]:
    os.makedirs(os.path.dirname(path), exist_ok=True)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("config")

# Environment variables
load_dotenv(ENV_FILE_PATH)

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    logger.critical(f"'REDIS_URL' missing from environment or '{ENV_FILE_PATH}'.")
    sys.exit(1)

POSTGRES_URL = os.getenv("POSTGRES_URL")
if not POSTGRES_URL:
    logger.critical(f"'POSTGRES_URL' missing from environment or '{ENV_FILE_PATH}'.")
    sys.exit(1)

# Constants
REDIS_KEY_PATTERN = "survey:responses*"
CONNECT_TIMEOUT_SECONDS = 10

# Redis key templates
REDIS_SURVEY_INDEX = "survey:task_ids"
REDIS_SURVEY_HASH_PREFIX = "survey:"

# Redis fields to fetch
REDIS_TASK_FIELDS = [
    "state",
    "comparison_type",
    "total_dimensions",
    "owner_id",
    "settings_json",
    "result_json",
]