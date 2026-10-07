# regcheck-dashboard

## Project description

This project crawls user and usage data from the [regcheck tool](https://github.com/JamieCummins/regcheck), processes the data into CSV files, and generates an automated dashboard using Quarto and Python.

The repository also contains alternative dashboard implementations using Streamlit and Tableau.

## Requirements

The following software is required to run the project:

- Python 3.14
- Quarto 1.9

## Project Structure

```text
.
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variable template
├── config.py                           # Global paths and variables
├── run_pipeline.py                     # Project orchestrator script / entry point for pipeline automation
├── _quarto.yml                         # Quarto project configuration / entry point for rendering
├── setup_task_scheduler.example.ps1    # Windows Task Scheduler template
├── README.md                           # Project documentation
├── LICENSE                             # License
│
├── scripts/
│   ├── 00a_mock_redis.py               # Mocks Redis data
│   ├── 00b_mock_postgres.py            # Mocks PostgreSQL data
│   ├── 01a_ingest_redis_to_csv.py      # Fetches Redis production data
│   ├── 01b_ingest_postgres_to_csv.py   # Fetches PostgreSQL data
│   ├── 02_dashboard.twb                # Creates Tableau dashboard
│   ├── 02_dashboard.py                 # Creates Streamlit dashboard
│   └── 02_dashboard.qmd                # Creates Quarto dashboard
│
├── data/
│   ├── production/
│   └── simulated/
│
├── output/
│   ├── scripts/                        # Generated dashboard report
│   └── figures/                        # Generated dashboard figures
│
└── logs/
    └── pipeline.log                    # Pipeline logs
```

## Setup

```powershell
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt

# Register the jupyter kernel
python -m ipykernel install --user --name python --display-name "python"
```

### Environment variables

Create a `.env` file based on `.env.example` and add the required Redis and PostgreSQL configuration values.

## Simulation vs. production

The pipeline can be executed in one of the modes:

Simulation: uses mock Redis/PostgreSQL data for testing the dashboard
Production: uses production Redis/PostgreSQL data for rendering the dashboard

The default is the simulation mode.

### Simulation mode

```powershell
python run_pipeline.py --mode simulation
```

### Production mode

```powershell
python run_pipeline.py --mode production
```

## Automation

The `run_pipeline.py` script can be setup to run automatically.
For this, create a new `.ps1` file based on `.\setup_task_scheduler.example.ps1` and add the project route and python exectuor.
The scheduler runs in --mode production, every three hours and only while the user is signed in.

```text
# Initialize the task scheduler
.\setup_task_scheduler.ps1
```

## Alternative dashboards

The Tableau and Streamlit based dashboards are not included in the automated pipeline. They have to be executed separately.

### Tableau dashboard

Requires a separate installation of Tableau Desktop, manually loading `scripts/02_dashboard.twb` and refreshing the data source.

### Streamlit dashboard

```
streamlit run scripts/02_dashboard.py
```