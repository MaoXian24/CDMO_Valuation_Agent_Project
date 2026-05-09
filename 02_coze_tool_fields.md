# Coze Tool Field Mapping

> The NAME you give each tool in Coze MUST exactly match the Python import path in line 2 of the .py file.
> Wrong name = ModuleNotFoundError at runtime.

Coze supports these field types: **string, integer, number, object, array, boolean**.

---

## A1 — WRDS_Condensed_Financial_Stmt

| Field | Type | English Description |
|-------|------|---------------------|
| **Input** | | |
| WRDS_username | string | WRDS account username for database connection |
| WRDS_pwd | string | WRDS account password |
| stkcd | string | 6-digit CSMAR stock code, e.g. 603259 (no .SH suffix) |
| start_year | number | First year of historical data, e.g. 2019 |
| end_year | number | Last year of historical data, e.g. 2024 |
| company_dict | string | (Optional) JSON string of stock-code:company-name pairs for multi-company mode, e.g. "{'600519': 'Moutai', '000858': 'Wuliangye'}" |
| **Output** | | |
| message | string | Status message indicating success or failure |
| `years` | array | List of integer years retrieved, e.g. [2019,2020,2021,2022,2023,2024]（Item type: number） |
| balance_sheet | string | Condensed balance sheet in Markdown table format |
| income_statement | string | Condensed income statement in Markdown table format |
| bs_check | string | JSON string of balance sheet identity check row (Assets − Liabilities − Equity), keyed by year |
| sales_growth | string | JSON string of historical year-over-year revenue growth rates, keyed by year |
| other_ratios | string | JSON string of historical financial ratios by year, nested dict |

## A2 — Forecast_Condensed_Statements

| Field | Type | English Description |
|-------|------|---------------------|
| **Input** | | |
| WRDS_username | string | WRDS account username |
| WRDS_pwd | string | WRDS account password |
| stkcd | string | 6-digit CSMAR stock code |
| start_year | number | First historical year, e.g. 2019 |
| end_year | number | Last historical year, e.g. 2024 |
| sales_growth | string | JSON string dict of forecast growth rates, e.g. {"2025":0.10,"2026":0.09} |
| dividends_payout_ratio | string | JSON string dict of dividend payout ratios, e.g. {"default":0.3} |
| depreciation_rate | string | JSON string dict of depreciation rates, e.g. {"default":0.05} |
| other_ratios | string | JSON string dict for manual ratio overrides, use {} for defaults |
| **Output** | | |
| message | string | Status message |
| sales_forecast | string | Sales forecast table (historical + projected) in Markdown |
| assumption_table | string | Historical and forecast ratio assumption table in Markdown |
| `forecast_years` | array | List of forecast years（Item type: number） |
| fcff_table | string | FCFF breakdown table for forecast years in Markdown |
| bs_forecast | string | Forward projected condensed balance sheet in Markdown |
| is_forecast | string | Forward projected condensed income statement in Markdown |
| FCFF_Stage_1 | string | JSON-encoded list of FCFF values, passed to A4 DCF plugin |
| Rd | number | Cost of debt (interest expense / total debt) |
| D | number | Total debt (short-term + long-term) |
| TaxRate | number | Effective tax rate |
| Cash_Latest | number | Most recent cash balance |
| Minority_Latest | number | Most recent minority interest |

## A3 — WRDS_Beta

| Field | Type | English Description |
|-------|------|---------------------|
| **Input** | | |
| WRDS_username | string | WRDS account username |
| WRDS_pwd | string | WRDS account password |
| stkcd | string | 6-digit CSMAR stock code |
| start_year | number | First year for beta estimation, e.g. 2019 |
| end_year | number | Last year for beta estimation, e.g. 2024 |
| **Output** | | |
| message | string | Status message |
| beta | number | Historical beta (Cov/var vs CSI 300) |
| price | number | Latest closing price |
| sample_size | integer | Number of valid monthly return observations |

## A4 — Get_DCF

| Field | Type | English Description |
|-------|------|---------------------|
| **Input** | | |
| shares_outstanding | number | Total shares outstanding |
| current_price | number | Current stock price for market cap calculation |
| n_years_2nd_stage | number | Number of years in Stage 2 (fade period) |
| growth_rate_2nd_stage | number | Growth rate during Stage 2 as decimal, e.g. 0.04 = 4% |
| long_term_growth | number | Perpetual growth rate as decimal, e.g. 0.02 = 2% |
| Rf | number | Risk-free rate as decimal, e.g. 0.03 = 3% |
| beta | number | Stock beta (from A3) |
| E_Rm | number | Expected market return as decimal, default 0.065 |
| Rd | number | Cost of debt as decimal |
| D | number | Total debt amount |
| TaxRate | number | Effective tax rate as decimal |
| FCFF_Stage_1 | string | JSON string list of Stage 1 FCFF values, e.g. "[100,108,116,124]" |
| end_year | number | Last historical year |
| Cash_Latest | number | Most recent cash balance |
| Minority_Latest | number | Most recent minority interest |
| **Output** | | |
| dcf | string | DCF valuation table in Markdown |
| vps | number | Intrinsic value per share |
| wacc | number | Weighted Average Cost of Capital |
| sensitivity | string | JSON string of sensitivity parameters: WACC, Re, terminal_growth |

## A5 — Chart_Generator

| Field | Type | English Description |
|-------|------|---------------------|
| **Input** | | |
| chart_type | string | Chart type: line / bar / pie / stacked_bar / waterfall |
| chart_data | string | JSON string with chart data (see format below) |
| title | string | Chart title |
| x_label | string | X-axis label (leave empty for pie charts) |
| y_label | string | Y-axis label (leave empty for pie charts) |
| **Output** | | |
| message | string | Status message |
| chart_image | string | Base64-encoded PNG image |

### chart_data JSON format

| chart_type | chart_data structure |
|-----------|---------------------|
| line | {"labels":["2019","2020","2021"], "series":[{"name":"Revenue","values":[100,120,140]}]} |
| bar | {"labels":["Company A","Company B"], "series":[{"name":"Gross Margin","values":[0.4,0.35]}]} |
| pie | {"labels":["COGS","SG&A","R&D","Net Profit"], "values":[45,15,8,32]} |
| stacked_bar | Same as bar; multiple series stack automatically |
| waterfall | {"labels":["Start","+Revenue","-COGS","-OPEX","End"], "values":[100,50,-30,-20,100]} |
