import os

# Output Directories
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
SIMULATION_LOG_PATH = os.path.join(LOGS_DIR, "simulation.log")
CSV_PATH = os.path.join(PROJECT_ROOT, "data", "simulation")

# Simulation Volume Controls
NUM_USERS = 25
NUM_RECORDS = 250

# Redis Mock Values
RESEARCH_FIELDS = [
    "Psychology",
    "Medicine",
    "Other",
    None,
]

ACADEMIC_POSITIONS = [
    "Postdoc",
    "Masters",
    "Professor",
    None,
]

USE_CASES = [
    "Literature Review & Synthesis",
    "Data Extraction & Analysis",
    "Hypothesis Generation",
    "Drafting & Proofreading",
    "Code Generation for Experiments",
    None,
]

SURVEY_COMPARISON_TYPES = [
    "general preregistration",
    "clinical trials",
]

TASK_COMPARISON_TYPES = [
    0,
    1
]

LLM_CLIENTS = ["openai", "claude", "qwen"]

REASONING_EFFORTS = ["low", "medium", "high"]

MODEL_COMBINATIONS = [
    "gpt-5.5,text-embedding-3-large",
    "qwen/qwen3.6-27b,text-embedding-3-large",
    "claude-opus-4-8,text-embedding-3-large",
]

# Postgres Mock Values
COMPARISON_TYPES = [
    "general_preregistration",
    "clinical trials",
]

EXECUTION_SOURCES = [
    "api",
    "ui",
]