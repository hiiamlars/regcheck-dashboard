# regcheck-dashboard

This project crawls user and usage data from the regcheck tool and stores this data in csv-files. The data is then plotted with Tableau.

## Project Structure

```text
.
├── config.py
├── mock_config.py
├── requirements.txt
├── .env.example
├── README.md
│
├── scripts/
│   ├── 00a_mock_redis.py
│   ├── 00b_mock_postgres.py
│   ├── 01a_ingest_redis_to_csv.py
│   ├── 01b_ingest_postgres_to_csv.py
│   └── 02_dashboard.twb
│
├── data/
│   ├── production/
│   └── simulated/
│
└──logs/
```

## Set up

Necessary software:
* **Python**: `3.10+` (to run `.py`-scripts)
* **Tableau Desktop**: `2023.3+` (to view `code/02_dashboard.twb`)

```bash
# Clone Repository
git clone https://github.com/hiiamlars/regcheck-dashboard.git
cd regcheck-dashboard

# Create and Activate Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install Required Dependencies
pip install -r requirements.txt