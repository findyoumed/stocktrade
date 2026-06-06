# Repository Guidelines

## Project Structure & Module Organization

This repository contains Python stock-trading and market-data examples plus a nested dividend chart service.

- `chapter2/` through `chapter5/`: learning scripts and experiments, many with Korean filenames.
- `stock/`: Streamlit dashboards and notebook-derived scripts.
- `chapter3/`: strategy, prediction, charting, and backtest modules such as `data_loader.py`, `charts.py`, and `backtest_engine.py`.
- `plus_dividend-master/`: deployable dividend app. Backend code is in `backend/`, API entrypoint in `api/index.py`, browser assets in `frontend/`, and fallback data in `data/`.
- `scratch/` and root `test_app.py`: ad hoc tests and Streamlit behavior checks.

Keep new reusable code near the module it supports. Avoid mixing tutorial scripts with deployable app code unless the change is explicitly instructional.

## Build, Test, and Development Commands

Create and activate a local environment before running project code:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run Streamlit examples with:

```powershell
streamlit run stock/app.py
streamlit run chapter3/stock_prediction_dashboard.py
```

Run the dividend backend from `plus_dividend-master/`:

```powershell
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

Use `pytest` for Python tests when present:

```powershell
pytest
```

## Coding Style & Naming Conventions

Use Python 3, 4-space indentation, and descriptive snake_case names for functions, variables, and modules. Existing tutorial files may use Korean names; keep those intact unless renaming is part of the task. Prefer small pure functions for data loading, scoring, and backtest logic so they can be tested without launching Streamlit or FastAPI.

No repository-wide formatter is configured. If adding one, document it and avoid unrelated formatting churn.

## Testing Guidelines

Favor `pytest` tests for reusable logic in `chapter3/`, `stock/`, and `plus_dividend-master/backend/`. Name tests `test_*.py` and place narrow experimental tests in `scratch/` or stable tests beside the relevant package. For UI-heavy Streamlit changes, include at least a smoke run command and keep data dependencies explicit.

## Commit & Pull Request Guidelines

Recent commits use Conventional Commit-style prefixes, especially `fix:`. Continue that pattern, for example `fix: improve ticker matching` or `feat: add dividend cache fallback`.

Pull requests should include a short problem statement, summary of changes, commands run, and screenshots for visible UI changes. Link related issues when available and call out any data-source, environment-variable, or deployment impact.

## Security & Configuration Tips

Do not commit credentials, downloaded Excel files, virtual environments, or cache directories. Configure external dividend files with `DIVIDENDS_EXCEL_PATH`; otherwise the dividend app should rely on `plus_dividend-master/data/dividends_fallback.csv`.
