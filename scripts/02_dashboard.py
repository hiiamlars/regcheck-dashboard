"""
02_dashboard.py
---------------------------------
Loads simulated or production data and creates a streamlit based dashboard.
"""

import logging
from pathlib import Path
import sys

import altair as alt
import pandas as pd
import streamlit as st

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR if (SCRIPT_DIR / "config.py").exists() else SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    LOG_FILE_PATH,
    SURVEY_RESPONSE_CSV_PATH,
    ACCOUNTS_PER_DAY_CSV_PATH,
    AUTHENTICATED_RUNS_CSV_PATH,
    REPORTS_PER_USER_CSV_PATH
)

DEFAULT_CHART_HEIGHT = 350
DEFAULT_CORNER_RADIUS = 3
LABEL_SPACE_LIMIT = 400
LABEL_PADDING = 10

LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE_PATH, mode="a", encoding="utf-8"),
    ],
    force=True
)
logger = logging.getLogger("dashboard")

st.set_page_config(page_title="regcheck Dashboard", layout="wide")

@st.cache_data
def load_datasets(file_paths):
    datasets = {}
    for file_path in file_paths:
        path = Path(file_path)
        
        if not path.exists():
            st.warning(f"File not found: {path}")
            continue
        
        datasets[path.stem] = pd.read_csv(path)
        
    return datasets

datasets = load_datasets([
    SURVEY_RESPONSE_CSV_PATH,
    ACCOUNTS_PER_DAY_CSV_PATH,
    AUTHENTICATED_RUNS_CSV_PATH,
    REPORTS_PER_USER_CSV_PATH,
])


def daily_responses(df: pd.DataFrame,
                    height: int = DEFAULT_CHART_HEIGHT,
                    corner_radius: int = DEFAULT_CORNER_RADIUS,
                    x_title: str = "Date (DD/MM)",
                    y_title: str = "Number of Submissions") -> None:
    """Builds an Altair bar chart for daily survey submission counts."""
    plot_id = "Plot 1 (Survey Responses over Time)"
    logger.info("[%s] Starting process", plot_id)

    try:
        if "submitted_at" not in df.columns:
            logger.error("[%s] Required column 'submitted_at' missing", plot_id)
            st.error("Column `'submitted_at'` not found in `survey_responses.csv`.")
            return

        logger.info("[%s] Parsing 'submitted_at' ISO timestamps", plot_id)
        timestamps = pd.to_datetime(df["submitted_at"], errors="coerce", utc=True)
        valid_dates = timestamps.dt.date.dropna()

        if valid_dates.empty:
            logger.warning("[%s] No valid date entries found after parsing", plot_id)
            st.warning("No valid timestamps found to plot for survey responses.")
            return

        counts = valid_dates.value_counts()

        start_date = valid_dates.min()
        today = pd.Timestamp.now().date()
        end_date = max(start_date, today)
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D").date

        daily_counts = (
            counts.reindex(full_date_range, fill_value=0)
            .reset_index()
        )
        daily_counts.columns = ["RawDate", "Responses"]

        daily_counts["Date"] = pd.to_datetime(daily_counts["RawDate"]).dt.strftime("%d/%m")

        chart = (
            alt.Chart(daily_counts)
            .mark_bar(cornerRadiusTopLeft=corner_radius, cornerRadiusTopRight=corner_radius)
            .encode(
                x=alt.X("Date:O", sort=None, title=x_title),
                y=alt.Y("Responses:Q", title=y_title),
                tooltip=["Date:O", "Responses:Q"]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def daily_new_accounts(df: pd.DataFrame,
                       height: int = DEFAULT_CHART_HEIGHT,
                       corner_radius: int = DEFAULT_CORNER_RADIUS,
                       x_title: str = "Date (DD/MM)",
                       y_title: str = "Number of New Accounts") -> None:
    """Builds an Altair bar chart for daily account creations"""
    plot_id = "Plot 2 (Daily New Accounts over Time)"
    logger.info("[%s] Starting process", plot_id)

    try:
        required_cols = {"date", "new_accounts"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            logger.error("[%s] Missing required column(s): %s", plot_id, missing_cols)
            st.error(f"Column(s) `{missing_cols}` not found in `accounts_per_day.csv`.")
            return

        df_clean = df.copy()
        df_clean["parsed_date"] = pd.to_datetime(df_clean["date"], errors="coerce").dt.date
        df_clean = df_clean.dropna(subset=["parsed_date"])

        if df_clean.empty:
            logger.warning("[%s] No valid date entries found after parsing", plot_id)
            st.warning("No valid timestamps found to plot for daily new accounts.")
            return

        df_indexed = df_clean.set_index("parsed_date")

        start_date = df_clean["parsed_date"].min()
        today = pd.Timestamp.now().date()
        end_date = max(start_date, today)
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D").date

        df_continuous = (
            df_indexed[["new_accounts"]]
            .reindex(full_date_range, fill_value=0)
            .reset_index()
        )
        df_continuous.columns = ["RawDate", "New Accounts"]

        df_continuous["Date"] = pd.to_datetime(df_continuous["RawDate"]).dt.strftime("%d/%m")

        chart = (
            alt.Chart(df_continuous)
            .mark_bar(cornerRadiusTopLeft=corner_radius, cornerRadiusTopRight=corner_radius)
            .encode(
                x=alt.X("Date:O", sort=None, title=x_title),
                y=alt.Y("New Accounts:Q", title=y_title),
                tooltip=["Date:O", "New Accounts:Q"]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def cumulative_accounts(df: pd.DataFrame,
                        height: int = DEFAULT_CHART_HEIGHT,
                        x_title: str = "Date (DD/MM)",
                        y_title: str = "Cumulative Accounts") -> None:
    """Builds an Altair line chart for cumuluated created accounts"""

    plot_id = "Plot 3 (Cumulative Accounts over Time)"
    logger.info("[%s] Starting process", plot_id)
    try:
        required_cols = {"date", "cumulative_accounts"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            logger.error("[%s] Missing required column(s): %s", plot_id, missing_cols)
            st.error(f"Column(s) `{missing_cols}` not found in `accounts_per_day.csv`.")
            return

        df_clean = df.copy()
        df_clean["parsed_date"] = pd.to_datetime(df_clean["date"], errors="coerce").dt.date
        df_clean = df_clean.dropna(subset=["parsed_date"]).sort_values("parsed_date")

        if df_clean.empty:
            logger.warning("[%s] No valid date entries found after parsing", plot_id)
            st.warning("No valid timestamps found to plot for cumulative accounts.")
            return

        df_indexed = df_clean.set_index("parsed_date")

        start_date = df_clean["parsed_date"].min()
        today = pd.Timestamp.now().date()
        end_date = max(start_date, today)
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D").date

        df_continuous = (
            df_indexed[["cumulative_accounts"]]
            .reindex(full_date_range)
            .ffill()
            .fillna(0)
            .reset_index()
        )
        df_continuous.columns = ["RawDate", "Cumulative accounts"]

        df_continuous["Date"] = pd.to_datetime(df_continuous["RawDate"])

        chart = (
            alt.Chart(df_continuous)
            .mark_line(point=True)
            .encode(
                x=alt.X("Date:T", title=x_title, axis=alt.Axis(format="%d/%m")),
                y=alt.Y("Cumulative accounts:Q", title=y_title),
                tooltip=[alt.Tooltip("Date:T", format="%d/%m"), "Cumulative accounts:Q"]
            )
            .properties(height=height)
            .interactive(bind_y=False)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def research_field_distribution(df: pd.DataFrame,
                                height: int = DEFAULT_CHART_HEIGHT,
                                corner_radius: int = DEFAULT_CORNER_RADIUS,
                                x_title: str = "Number of Responses",
                                y_title: str = "Research Field",
                                label_width: int = LABEL_SPACE_LIMIT,
                                label_space: int = LABEL_PADDING) -> None:
    """Builds an Altair bar chart for research field distribution"""
    plot_id = "Plot 4 (Research Field Distribution)"
    logger.info("[%s] Starting process", plot_id)

    try:
        if "research_field" not in df.columns:
            logger.error("[%s] Required column 'research_field' missing", plot_id)
            st.error("Column `'research_field'` not found in `survey_responses.csv`.")
            return

        counts = df["research_field"].dropna().value_counts().reset_index()
        counts.columns = ["Research Field", "Frequency"]

        if counts.empty:
            logger.warning("[%s] No valid research_field entries found", plot_id)
            st.warning("No data available for research field distribution.")
            return

        chart = (
            alt.Chart(counts)
            .mark_bar(cornerRadiusTopRight=corner_radius, cornerRadiusBottomRight=corner_radius)
            .encode(
                x=alt.X("Frequency:Q", title=x_title),
                y=alt.Y("Research Field:N",
                        sort="-x",
                        title=y_title,
                        axis=alt.Axis(
                            labelLimit=label_width,
                            labelPadding=label_space
                            )
                        ),
                tooltip=["Research Field:N", "Frequency:Q"]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def domain_distribution(df: pd.DataFrame,
                        height: int = DEFAULT_CHART_HEIGHT,
                        corner_radius: int = DEFAULT_CORNER_RADIUS,
                        x_title: str = "Number of Responses",
                        y_title: str = "Dimension",
                        label_width: int = LABEL_SPACE_LIMIT,
                        label_space: int = LABEL_PADDING) -> None:
    """Builds an Altair bar chart for domain distribution"""
    plot_id = "Plot 5 (Domain Distribution)"
    logger.info("[%s] Starting process", plot_id)

    try:
        if "survey_comparison_type" not in df.columns:
            logger.error("[%s] Required column 'survey_comparison_type' missing", plot_id)
            st.error("Column `'survey_comparison_type'` not found in `survey_responses.csv`.")
            return

        df_clean = df.dropna(subset=["survey_comparison_type"]).copy()
        
        df_clean["formatted_type"] = (
            df_clean["survey_comparison_type"]
            .astype(str)
            .str.replace("_", " ")
            .str.title()
        )

        counts = df_clean["formatted_type"].value_counts().reset_index()
        counts.columns = ["Dimension", "Frequency"]

        if counts.empty:
            logger.warning("[%s] No valid survey_comparison_type entries found", plot_id)
            st.warning("No data available for survey comparison type distribution.")
            return

        chart = (
            alt.Chart(counts)
            .mark_bar(cornerRadiusTopRight=corner_radius, cornerRadiusBottomRight=corner_radius)
            .encode(
                x=alt.X("Frequency:Q", title=x_title),
                y=alt.Y(
                    "Dimension:N", 
                    sort="-x", 
                    title=y_title,
                    axis=alt.Axis(
                        labelLimit=label_width,
                        labelPadding=label_space,
                    )
                ),
                tooltip=["Dimension:N", "Frequency:Q"]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def cumulative_cost_total(df: pd.DataFrame,
                          height: int = DEFAULT_CHART_HEIGHT,
                          x_title: str = "Date (DD/MM)",
                          y_title: str = "Cumulative Total Cost (USD)") -> None:
    """Builds an Altair bar chart for cumulative total costs (USD)"""
    plot_id = "Plot 6 (Cumulative Total Cost USD)"
    logger.info("[%s] Starting process", plot_id)

    try:
        required_cols = {"submitted_at", "cost_total_usd"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            logger.error("[%s] Missing required column(s): %s", plot_id, missing_cols)
            st.error(f"Column(s) `{missing_cols}` not found in `survey_responses.csv`.")
            return

        df_clean = df.copy()
        
        df_clean["parsed_date"] = pd.to_datetime(df_clean["submitted_at"], errors="coerce", utc=True).dt.date
        df_clean["cost_total_usd"] = pd.to_numeric(df_clean["cost_total_usd"], errors="coerce").fillna(0.0)
        
        df_clean = df_clean.dropna(subset=["parsed_date"])

        if df_clean.empty:
            logger.warning("[%s] No valid cost data found after parsing", plot_id)
            st.warning("No valid data available for cumulative total costs.")
            return

        daily_sum = df_clean.groupby("parsed_date")["cost_total_usd"].sum()

        start_date = df_clean["parsed_date"].min()
        today = pd.Timestamp.now().date()
        end_date = max(start_date, today)
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D").date

        df_continuous = (
            daily_sum.reindex(full_date_range, fill_value=0.0)
            .cumsum()
            .reset_index()
        )
        df_continuous.columns = ["RawDate", "Cumulative Costs"]

        df_continuous["Date"] = pd.to_datetime(df_continuous["RawDate"]).dt.strftime("%d/%m")

        chart = (
            alt.Chart(df_continuous)
            .mark_line(point=True)
            .encode(
                x=alt.X("Date:O", sort=None, title=x_title),
                y=alt.Y("Cumulative Costs:Q", title=y_title),
                tooltip=[
                    alt.Tooltip("Date:O", title="Date"),
                    alt.Tooltip("Cumulative Costs:Q", title=y_title, format="$.2f")
                ]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def cumulative_cost_llm(df: pd.DataFrame,
                        height: int = DEFAULT_CHART_HEIGHT,
                        x_title: str = "Date (DD/MM)",
                        y_title: str = "Cumulative LLM Cost (USD)") -> None:
    """Builds an Altair bar chart for cumulative LLM costs (USD)"""
    plot_id = "Plot 7 (Cumulative LLM Cost USD)"
    logger.info("[%s] Starting process", plot_id)

    try:
        required_cols = {"submitted_at", "cost_llm_usd"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            logger.error("[%s] Missing required column(s): %s", plot_id, missing_cols)
            st.error(f"Column(s) `{missing_cols}` not found in `survey_responses.csv`.")
            return

        df_clean = df.copy()
        
        df_clean["parsed_date"] = pd.to_datetime(df_clean["submitted_at"], errors="coerce", utc=True).dt.date
        df_clean["cost_llm_usd"] = pd.to_numeric(df_clean["cost_llm_usd"], errors="coerce").fillna(0.0)
        
        df_clean = df_clean.dropna(subset=["parsed_date"])

        if df_clean.empty:
            logger.warning("[%s] No valid LLM cost data found after parsing", plot_id)
            st.warning("No valid data available for cumulative LLM costs.")
            return

        daily_sum = df_clean.groupby("parsed_date")["cost_llm_usd"].sum()

        start_date = df_clean["parsed_date"].min()
        today = pd.Timestamp.now().date()
        end_date = max(start_date, today)
        full_date_range = pd.date_range(start=start_date, end=end_date, freq="D").date

        df_continuous = (
            daily_sum.reindex(full_date_range, fill_value=0.0)
            .cumsum()
            .reset_index()
        )
        df_continuous.columns = ["RawDate", "Cumulative LLM Cost"]

        df_continuous["Date"] = pd.to_datetime(df_continuous["RawDate"]).dt.strftime("%d/%m")

        chart = (
            alt.Chart(df_continuous)
            .mark_line(point=True)
            .encode(
                x=alt.X("Date:O", sort=None, title=x_title),
                y=alt.Y("Cumulative LLM Cost:Q", title=y_title),
                tooltip=[
                    alt.Tooltip("Date:O", title=x_title),
                    alt.Tooltip("Cumulative LLM Cost:Q", title=y_title, format="$.2f")
                ]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")

def reports_per_user_distribution(df: pd.DataFrame,
                                  height: int = DEFAULT_CHART_HEIGHT,
                                  corner_radius: int = DEFAULT_CORNER_RADIUS,
                                  x_title: str = "Reports per User Range",
                                  y_title: str = "Number of Accounts") -> None:
    """Builds an Altair bar chart for number of accounts per user range."""
    plot_id = "Plot 8 (Reports per User Distribution)"
    logger.info("[%s] Starting process", plot_id)

    try:
        required_cols = {"owner_id", "total_reports"}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            logger.error("[%s] Missing required column(s): %s", plot_id, missing_cols)
            st.error(f"Column(s) `{missing_cols}` not found in `reports_per_user.csv`.")
            return

        df_clean = df.copy()

        df_clean["total_reports"] = pd.to_numeric(df_clean["total_reports"], errors="coerce")
        df_clean = df_clean.dropna(subset=["owner_id", "total_reports"])

        if df_clean.empty:
            logger.warning("[%s] No valid data found after parsing", plot_id)
            st.warning("No valid data available for reports per user distribution.")
            return

        bins = [-1, 9, 19, float("inf")]
        labels = ["0–9", "10–19", "20+"]

        df_clean["ReportRange"] = pd.cut(
            df_clean["total_reports"],
            bins=bins,
            labels=labels,
            right=True
        )

        counts = (
            df_clean["ReportRange"]
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )
        counts.columns = ["Report Range", "User Count"]

        chart = (
            alt.Chart(counts)
            .mark_bar(cornerRadiusTopLeft=corner_radius, cornerRadiusTopRight=corner_radius)
            .encode(
                x=alt.X("Report Range:O", sort=labels, title=x_title),
                y=alt.Y("User Count:Q", title=y_title),
                tooltip=[
                    alt.Tooltip("Report Range:O", title=x_title),
                    alt.Tooltip("User Count:Q", title=y_title)
                ]
            )
            .properties(height=height)
        )

        st.altair_chart(chart, width="stretch")
        logger.info("[%s] Render succeeded", plot_id)

    except Exception as e:
        logger.exception("[%s] Execution failed: %s", plot_id, e)
        st.error(f"Failed to generate {plot_id}: {e}")


st.title("regcheck Dashboard")

st.divider()

with st.container():
    st.header("Daily Submissions")
    
    file_key = "survey_responses"
    if file_key in datasets:
        daily_responses(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Daily New Accounts")
    
    file_key = "accounts_per_day"
    if file_key in datasets:
        daily_new_accounts(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Cummulative Accounts")
    
    file_key = "accounts_per_day"
    if file_key in datasets:
        cumulative_accounts(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Research Field Distribution")
    
    file_key = "survey_responses"
    if file_key in datasets:
        research_field_distribution(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Domain Distrubtion")
    
    file_key = "survey_responses"
    if file_key in datasets:
        domain_distribution(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Cumulative Total Cost (USD)")
    
    file_key = "survey_responses"
    if file_key in datasets:
        cumulative_cost_total(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Cumulative LLM Cost (USD)")
    
    file_key = "survey_responses"
    if file_key in datasets:
        cumulative_cost_llm(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")

st.divider()

with st.container():
    st.header("Reports per User Distribution")
    
    file_key = "reports_per_user"
    if file_key in datasets:
        reports_per_user_distribution(datasets[file_key])
    else:
        logger.warning("Dataset '%s' not loaded", file_key)
        st.info(f"Dataset `{file_key}` is missing or not loaded.")