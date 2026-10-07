"""
config.py
---------------------------------
Central script for all data path definitions, script path definitions,
setup of environment variables and hardcoded values.
"""

import os
from pathlib import Path
import sys
import uuid
from dotenv import load_dotenv

# Environment path
PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"
if ENV_FILE_PATH.exists():
    load_dotenv(ENV_FILE_PATH)
else:
    print(f"[WARNING] Config: '.env' file not found at {ENV_FILE_PATH}. Using system environment variables.")

# Log path
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE_PATH = LOGS_DIR / "pipeline.log"

# Data paths
RUN_MODE = os.getenv("RUN_MODE", "simulation").lower()

if RUN_MODE == "production":
    DATA_PATH = PROJECT_ROOT / "data" / "production"
else:
    DATA_PATH = PROJECT_ROOT / "data" / "simulation"

DATA_PATH.mkdir(parents=True, exist_ok=True)

SURVEY_RESPONSE_CSV_PATH = DATA_PATH / "survey_responses.csv"
ACCOUNTS_PER_DAY_CSV_PATH = DATA_PATH / "accounts_per_day.csv"
AUTHENTICATED_RUNS_CSV_PATH = DATA_PATH / "authenticated_runs.csv"
REPORTS_PER_USER_CSV_PATH = DATA_PATH / "reports_per_user.csv"

# Script paths
SCRIPT_PATH = PROJECT_ROOT / "scripts"
SCRIPT_PATH.mkdir(parents=True, exist_ok=True)

MOCK_PIPELINE_SCRIPTS = [
    SCRIPT_PATH / "mock_00a_mock_redis.py",
    SCRIPT_PATH / "mock_00b_mock_postgres.py",
]

PRODUCTION_PIPELINE_SCRIPTS = [
    SCRIPT_PATH / "01a_ingest_redis_to_csv.py",
    SCRIPT_PATH / "01b_ingest_postgres_to_csv.py",
]

# Relevant piepline
ACTIVE_PIPELINE_SCRIPTS = (
    PRODUCTION_PIPELINE_SCRIPTS if RUN_MODE == "production" else MOCK_PIPELINE_SCRIPTS
)

DASHBOARD_PATH = PROJECT_ROOT / "scripts" / "02_dashboard.qmd"

# Environment variables
load_dotenv(ENV_FILE_PATH)

POSTGRES_URL = os.getenv("POSTGRES_URL")
if not POSTGRES_URL:
    print(f"'POSTGRES_URL' missing from '{ENV_FILE_PATH}'.")
    sys.exit(1)

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    print(f"'REDIS_URL' missing from '{ENV_FILE_PATH}'.")
    sys.exit(1)

# Production data constants
BATCH_SIZE = 500
CONNECT_TIMEOUT_SECONDS = 10

# Redis keys
REDIS_KEY_PATTERN = "survey:responses*"
REDIS_SURVEY_HASH_PREFIX = "survey:"
REDIS_SURVEY_INDEX = "survey:task_ids"
REDIS_SURVEY_ID = "task_id"

# Redis fields to fetch
REDIS_TASK_FIELDS = [
    "state",
    "comparison_type",
    "total_dimensions",
    "owner_id",
    "settings_json",
    "result_json",
]

# Simulation data constants
DAYS = 180
NUM_USERS = 100

def get_shared_owner_pool() -> list[str]:
    """Generates a deterministic pool of user UUID strings shared across mock generators."""
    namespace = uuid.NAMESPACE_DNS
    return [str(uuid.uuid5(namespace, f"user_{i}")) for i in range(NUM_USERS)]
