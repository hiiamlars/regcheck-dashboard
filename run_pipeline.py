"""
run_pipeline.py
---------------------------------
Automatically runs simulated or live data updates when executed.
"""


import argparse
import logging
import os
import sys
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="Run regcheck ETL pipeline.")
    parser.add_argument(
        "--mode",
        choices=["simulation", "production"],
        default=os.getenv("RUN_MODE", "simulation"),
        help="Pipeline execution mode (default: simulation)",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    os.environ["RUN_MODE"] = args.mode

    import config

    log_dir = os.path.dirname(config.LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE_PATH, mode="a", encoding="utf-8"),
        ],
        force=True,
    )
    logger = logging.getLogger("dashboard")

    logger.info(f"Starting ETL Pipeline in [{config.RUN_MODE.upper()}] mode")
    logger.info(f"Log Path   : {config.LOG_FILE_PATH}")
    logger.info(f"Output Path: {config.DATA_PATH}")

    for script_path in config.ACTIVE_PIPELINE_SCRIPTS:
        if not os.path.exists(script_path):
            logger.error(f"Script not found: '{script_path}'")
            sys.exit(1)

        script_name = os.path.basename(script_path)
        logger.info(f"Executing step: {script_name}...")
        
        result = subprocess.run(
            [sys.executable, script_path],
            env=os.environ.copy(),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error(f"Execution failed for '{script_name}':\n{result.stderr}")
            sys.exit(1)


    dashboard_path = config.DASHBOARD_PATH

    if not os.path.exists(dashboard_path):
        logger.error(f"Dashboard not found: '{dashboard_path}'")
        sys.exit(1)

    logger.info(f"Rendering dashboard: {dashboard_path}...")

    result = subprocess.run(
        ["quarto", "render", str(dashboard_path)],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(
            f"Dashboard rendering failed:\n{result.stderr}"
        )
        sys.exit(1)

    logger.info("Dashboard rendered successfully")

    logger.info("ETL Pipeline Finished Successfully")

if __name__ == "__main__":
    main()