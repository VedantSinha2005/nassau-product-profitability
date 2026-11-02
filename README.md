# Product Line Profitability & Margin Performance Analysis

**Nassau Candy Distributor — educational case-study project**

A standalone Streamlit dashboard + reproducible analysis + research paper + executive summary addressing **Project 1: Product Line Profitability & Margin Performance Analysis for Nassau Candy Distributor**. This is a **different project from the shipping-route efficiency analysis**.

> **Data provenance:** The CSV was supplied by the student for this assignment. Its Wonka-themed product names and figures **are not authenticated as Nassau Candy's actual products, prices, or financial statements**. [Nassau Candy's official website](https://www.nassaucandy.com/) is cited for broad business context *only*. The source does not contain a currency code; dashboard/report labels use **assumed USD**.

## Core results — full dataset (02 Jan 2024–31 Dec 2025)

| KPI | Value |
|---|---:|
| Transaction lines | 10,194 |
| Unique order IDs | 8,549 |
| Distinct products / divisions | 15 / 3 |
| Revenue (assumed USD) | $141,783.63 |
| Cost (manufacturing/direct, assumed USD) | $48,340.83 |
| Gross profit | $93,442.80 |
| **Weighted gross margin** | **65.91%** |
| Gross profit per unit | $2.42 |
| Profit contributed by five Chocolate-bar products | 95.06% |
| Lowest material margin candidate | Kazookles — 7.69% |

The data is dominated by Chocolate (9,844 of 10,194 rows); the Sugar division has only 40 rows. Product gross margins are effectively constant across time because the source data embeds fixed product-level unit economics, so **zero margin volatility does not demonstrate stability in actual operations**.

## Dashboard features

- **Financial overview:** revenue, profit, margin, gross profit per unit and monthly trend.
- **Product profitability:** product ranking by gross profit, revenue vs gross margin, complete product KPI table and product selector.
- **Division performance:** weighted gross margin and revenue/profit share by division.
- **Cost and margin diagnostics:** cost-versus-sales scatter, configurable low-margin threshold and priority risk flags.
- **Pareto / concentration:** interactive revenue/profit rankings with cumulative percentage and minimum product count reaching 80%.
- **Validation + exports:** cleaning audit, detailed metric definitions, filtered transactions and product/division CSV downloads.
- **Interactive filters:** order-date range, division multiselect, product search, gross-margin threshold slider and minimum revenue risk cutoff.
- **Optional CSV upload:** run the same analytical pipeline on another CSV with compatible columns.

## Run locally (Windows / VS Code)

1. Extract this ZIP, open the extracted folder in VS Code.
2. Open **Terminal → New Terminal**. Make sure you are in the folder containing `app.py`.
3. Run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

4. Open the local URL printed in the terminal (typically `http://localhost:8501`). Keep the terminal open while using the app.

If PowerShell blocks activation, skip it and use `.venv\Scripts\python.exe -m pip install -r requirements.txt` followed by `.venv\Scripts\python.exe -m streamlit run app.py`.

## Test the analytics

```bash
python -m pip install pytest
python -m pytest -q tests/
```

Eight tests verify cleaning, accounting consistency, headline figures, weighted margins, division/product reconciliation, 80%-concentration, dates and risk flags.

## Deploy a real website URL (not done automatically)

1. Create a new GitHub repository (e.g. `nassau-product-profitability`).
2. Upload **the extracted project files and folders**, preserving `app.py`, `analytics.py`, `requirements.txt`, `data/`, and `.streamlit/config.toml`. Do **not** upload the ZIP *instead of* extracting its contents, and do not upload your local `.venv`.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/), choose **Create app**, select your GitHub repo, `main` branch, and **entrypoint `app.py`**.
4. After deployment succeeds, copy the URL ending in `.streamlit.app`.
5. Open the URL in an incognito window to verify its charts load. If any issues occur, check the deployment logs.

Official [Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Files

| Path | Purpose |
|---|---|
| `app.py` | Streamlit user interface, charts, controls and exports |
| `analytics.py` | Reusable data validation and financial calculation code |
| `data/Nassau_Candy_Distributor.csv` | Original dataset (unmodified contents, renamed file) |
| `reports/Nassau_Product_Profitability_Research_Paper.docx/.pdf` | Eight-page research report |
| `reports/Nassau_Product_Profitability_Executive_Summary.docx/.pdf` | Two-page stakeholder summary |
| `charts/` | Five supporting research figures |
| `tests/test_analytics.py` | Eight automated checks |
| `scripts/build_reports.py` | Rebuilds charts and Word reports from source CSV |
| `SUBMISSION_GUIDE.md` | How to obtain all four submission URLs |
| `FEEDBACK_VIDEO_SCRIPT.md` | Suggested self-recorded feedback video script |
| `data_dictionary.md` | Source-field reference and KPI definitions |

To rebuild the original Word reports, install `python-docx` and `matplotlib`, then run `python scripts/build_reports.py`. The PDFs are pre-generated; exporting DOCX back to PDF may require Word or LibreOffice.

## Financial definitions and limitations

- Gross margin = 100 × total Gross Profit / total Sales (not simple mean margin).
- Profit/unit = total Gross Profit / total positive Units.
- Gross profit excludes freight, overhead, tax, sales/marketing and other unknown costs.
- Margin volatility is the sample standard deviation across *monthly weighted product margins*, measured in percentage points; use only for products with at least two active months.
- No invalid records were removed from the supplied file. See the dashboard validation tab.
- The default 50% low-margin threshold and $1,000 revenue cutoff are **assumptions for review**, not validated targets.
- No paper approval/publication, GitHub upload, Streamlit deployment, or video recording is represented as complete.

## Sources

- [Nassau Candy official site](https://www.nassaucandy.com/), [confections pages](https://www.nassaucandy.com/confections.html) — general business context, accessed 30 Oct 2026.
- Original student-provided assignment brief and transaction CSV — all project-specific metrics.
