# Source fields and derived financial indicators

The source case-study CSV contains 18 columns. The dashboard relies directly on `Row ID`, `Order ID`, `Order Date`, `Division`, `Product ID`, `Product Name`, `Sales`, `Units`, `Gross Profit`, `Cost`.

| Raw source field | Description / usage |
|---|---|
| Row ID | Unique CSV row identifier |
| Order ID | Order identifier; may recur on multiple product lines |
| Order Date | Order date, parsed day-first DD-MM-YYYY |
| Ship Date | Source shipping date; not needed for profitability measures |
| Ship Mode | Shipping category, not needed for gross profitability |
| Customer ID | Customer identifier |
| Country/Region | Customer geography |
| City | Customer city |
| State/Province | Customer state |
| Postal Code | Customer postal/ZIP code |
| Division | Chocolate, Other, Sugar; standardized title case |
| Region | Customer region |
| Product ID | Stable product ID / grouping key |
| Product Name | Product label; whitespace normalized |
| Sales | Monetary sales on each line (currency unspecified, presented as assumed USD) |
| Units | Items sold on each line |
| Gross Profit | Supplied line gross profit, verified against Sales – Cost |
| Cost | Direct or manufacturing cost on the source line |

## Computed indicators

- **Weighted gross margin (%)** = 100 × `sum(Gross Profit) / sum(Sales)` for a product, division or selected portfolio.
- **Profit per unit** = `sum(Gross Profit) / sum(Units)` for valid positive quantities.
- **Revenue contribution (%)** = 100 × product sales / selected overall sales.
- **Profit contribution (%)** = 100 × product gross profit / selected overall gross profit.
- **Margin volatility (percentage points)** = sample standard deviation (ddof=1) of product-month weighted gross margins where product appears in at least two active months.
- **Pareto concentration** = products ranked by revenue/profit, with cumulative percentage. `products_to_80_pct` returns the first product count at or above 80% cumulative contribution.
- **Low-margin flag** = weighted gross margin below the dashboard threshold (50% default).
- **Priority margin flag** = low margin and selected product revenue at or above user-chosen amount ($1,000 default).
- **High sales/low margin flag** = low margin and product in top 25% by selected-period product sales.

> The source dataset is not independently authenticated; no claims about official Nassau Candy results should be made.
