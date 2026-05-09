from runtime import Args
from typings.Forecast_Condensed_Statements.Forecast_Condensed_Statements import Input, Output

def handler(args: Args[Input]) -> Output:
    import sys
    from io import StringIO
    import wrds
    import pandas as pd
    import json

    try:
        WRDS_username = getattr(args.input, "WRDS_username", None)
        WRDS_pwd = getattr(args.input, "WRDS_pwd", None)
        stkcd = args.input.stkcd
        start_year = int(args.input.start_year)
        end_year = int(args.input.end_year)
        sales_growth = json.loads(args.input.sales_growth)
        dividends_payout_ratio = json.loads(args.input.dividends_payout_ratio)
        depreciation_rate = json.loads(args.input.depreciation_rate)
        other_ratios = json.loads(args.input.other_ratios) if args.input.other_ratios else {}
        if not WRDS_username or not WRDS_pwd or not stkcd:
            return {"message": "WRDS_username, WRDS_pwd and stock code are required."}
    except Exception as e:
        return {"message": f"Failed to read parameters. Error: {e}"}

    fbs = {
        'a001101000': 'Cash and cash equivalents', 'a001107000': 'Trading Financial Assets',
        'a001109000': 'Net Short-term Investments', 'a001110000': 'Net Notes Receivable',
        'a001111000': 'Net Accounts Receivable', 'a001123000': 'Net Inventories',
        'a001100000': 'Total current assets', 'a001212000': 'Net Fixed Assets',
        'a001218000': 'Net Intangible Assets', 'a001200000': 'Total Non-current Assets',
        'a001000000': 'Total Assets', 'a002101000': 'Short-Term Borrowings',
        'a002107000': 'Notes Payable', 'a002108000': 'Accounts Payable',
        'a002100000': 'Total Current Liabilities', 'a002201000': 'Long-term Loans',
        'a002200000': 'Total Non-current Liabilities', 'a002000000': 'Total Liabilities',
        'a003105000': 'Retained Earnings', 'a003200000': "Minority Shareholders' Interest",
        'a003000000': "Total Shareholders' Equity",
    }
    fis = {
        'b001101000': 'Operating Revenue', 'b001201000': 'Operating Costs',
        'b001207000': 'Tax And Additional Fees Of Operations', 'b001209000': 'Selling Expenses',
        'b001210000': 'General And Administrative Expenses', 'b001211000': 'Finance Expenses',
        'b001212000': 'Asset Impairment Loss', 'b001301000': 'Gains/Losses From Fair Value Change',
        'b001302000': 'Investment Gains', 'b001300000': 'Operating Profit',
        'b001400000': 'Non-Operating Income', 'b001500000': 'Non-Operating Expenses',
        'b001000000': 'Total Profit', 'b002100000': 'Income Tax Expenses',
        'b002000000': 'Net Profit', 'b002000101': 'Net Profit Attributable To Owners Of The Parent Company',
        'b001216000': 'R&D Expenses', 'b001211101': 'Including: Interest Expenses',
        'b001211203': 'Including: Interest Income', 'b001307000': 'Credit impairment loss',
        'b001308000': 'Income from Assets Disposal',
    }

    try:
        sys.stdin = StringIO(f"{WRDS_username}\n{WRDS_pwd}\nn\n")
        db = wrds.Connection()
        for key, mapping in [('bs', fbs), ('is', fis)]:
            cols = ', '.join(mapping.keys())
            df = db.raw_sql(
                f"SELECT stkcd, accper, {cols} FROM csmar.wrds_csmar_financial_master "
                f"WHERE stkcd='{stkcd}' AND typrep='A'", date_cols=['accper'])
            df = df[df.accper.dt.month == 12]
            df.loc[:, 'year'] = pd.to_datetime(df['accper']).dt.year
            df.pop('accper')
            df = df[(df.year >= start_year) & (df.year <= end_year)]
            df = df.sort_values('year').rename(columns=mapping)
            df = df.drop(df.columns[0], axis=1).set_index('year').T
            df.fillna(0, inplace=True)
            if key == 'bs':
                df_bs = df.copy()
            else:
                df_is = df.copy()
        db.close()
    except Exception as e:
        return {"message": f"Failed to connect to WRDS. Error: {e}"}

    try:
        yr = list(range(start_year, end_year + 1))
        yr_int = [int(y) for y in yr]
        zero = pd.Series({y: 0.0 for y in yr_int})

        def bs_get(*names):
            return sum((df_bs.loc[n].reindex(yr_int, fill_value=0) if n in df_bs.index else zero for n in names), zero)

        def is_get(name):
            if name in df_is.index:
                return df_is.loc[name].reindex(yr_int, fill_value=0)
            return pd.Series(0.0, index=pd.Index(yr_int, dtype=int))

        idx = [
            'Cash and equivalent', 'Notes and accounts receivable', 'Inventory',
            'Total other current assets', 'Total current assets',
            'Property, Plant and Equipment', 'Intangible assets',
            'Total other non-current assets', 'Total non-current assets', 'Total assets',
            'Short debt', 'Notes and account payable',
            'Total other current liabilities', 'Total current liabilities',
            'Long-term debt', 'Total other non-current liabilities',
            'Total non-current liabilities', 'Total liabilities',
            'Retained earnings', 'Minority interests', 'Others',
            "Total shareholders' equity", "Total liabilities and shareholders' equity", 'check',
        ]
        bs_df = pd.DataFrame(index=idx, columns=yr_int, dtype=float)
        bs_df.loc['Cash and equivalent'] = bs_get('Cash and cash equivalents', 'Trading Financial Assets', 'Net Short-term Investments')
        bs_df.loc['Notes and accounts receivable'] = bs_get('Net Notes Receivable', 'Net Accounts Receivable')
        bs_df.loc['Inventory'] = bs_get('Net Inventories')
        bs_df.loc['Total current assets'] = bs_get('Total current assets')
        bs_df.loc['Property, Plant and Equipment'] = bs_get('Net Fixed Assets')
        bs_df.loc['Intangible assets'] = bs_get('Net Intangible Assets')
        bs_df.loc['Total non-current assets'] = bs_get('Total Non-current Assets')
        bs_df.loc['Total assets'] = bs_get('Total Assets')
        bs_df.loc['Short debt'] = bs_get('Short-Term Borrowings')
        bs_df.loc['Notes and account payable'] = bs_get('Accounts Payable', 'Notes Payable')
        bs_df.loc['Total current liabilities'] = bs_get('Total Current Liabilities')
        bs_df.loc['Long-term debt'] = bs_get('Long-term Loans')
        bs_df.loc['Total non-current liabilities'] = bs_get('Total Non-current Liabilities')
        bs_df.loc['Total liabilities'] = bs_get('Total Liabilities')
        bs_df.loc['Retained earnings'] = bs_get('Retained Earnings')
        bs_df.loc['Minority interests'] = bs_get("Minority Shareholders' Interest")
        bs_df.loc["Total shareholders' equity"] = bs_get("Total Shareholders' Equity")
        bs_df.loc['Total other current assets'] = bs_df.loc['Total current assets'] - bs_df.loc[['Cash and equivalent', 'Notes and accounts receivable', 'Inventory']].sum()
        bs_df.loc['Total other non-current assets'] = bs_df.loc['Total non-current assets'] - bs_df.loc[['Property, Plant and Equipment', 'Intangible assets']].sum()
        bs_df.loc['Total other current liabilities'] = bs_df.loc['Total current liabilities'] - bs_df.loc[['Short debt', 'Notes and account payable']].sum()
        bs_df.loc['Total other non-current liabilities'] = bs_df.loc['Total non-current liabilities'] - bs_df.loc['Long-term debt']
        bs_df.loc['Others'] = bs_df.loc["Total shareholders' equity"] - bs_df.loc[['Retained earnings', 'Minority interests']].sum()
        bs_df.loc["Total liabilities and shareholders' equity"] = bs_df.loc['Total liabilities'] + bs_df.loc["Total shareholders' equity"]
        bs_df.loc['check'] = bs_df.loc['Total assets'] - bs_df.loc["Total liabilities and shareholders' equity"]

        is_df = pd.DataFrame(index=[
            'Total Revenue', 'Cost of goods sold', 'Main operating expenses',
            'Non-cash or non-operating items', '+ Interest expense', '- Interest income',
            '+ Others (Net financial expense)', '= Net Financial expense/(income)',
            'All others', 'Total profit', 'Income Tax Expenses', 'Net profit',
            'Net Profit Attributable To Owners Of The Parent Company',
            'Net Profit Attributable To Owners Of The Parent Company/Net profit',
        ], columns=yr_int, dtype=float)
        is_df.loc['Total Revenue'] = is_get('Operating Revenue')[yr_int]
        is_df.loc['Cost of goods sold'] = is_get('Operating Costs')[yr_int]
        is_df.loc['Main operating expenses'] = (is_get('Tax And Additional Fees Of Operations') + is_get('Selling Expenses') + is_get('General And Administrative Expenses') + is_get('R&D Expenses'))[yr_int]
        is_df.loc['Non-cash or non-operating items'] = (is_get('Investment Gains') - is_get('Asset Impairment Loss') - is_get('Credit impairment loss') + is_get('Gains/Losses From Fair Value Change') + is_get('Income from Assets Disposal') + is_get('Non-Operating Income') - is_get('Non-Operating Expenses'))[yr_int]
        is_df.loc['= Net Financial expense/(income)'] = is_get('Finance Expenses')[yr_int]
        is_df.loc['+ Interest expense'] = is_get('Including: Interest Expenses')[yr_int]
        is_df.loc['- Interest income'] = is_get('Including: Interest Income')[yr_int]
        is_df.loc['+ Others (Net financial expense)'] = is_df.loc['= Net Financial expense/(income)'] - is_df.loc['+ Interest expense'] + is_df.loc['- Interest income']
        is_df.loc['Total profit'] = is_get('Total Profit')[yr_int]
        is_df.loc['All others'] = is_df.loc['Total profit'] - (is_df.loc['Total Revenue'] - is_df.loc['Cost of goods sold'] - is_df.loc['Main operating expenses'] + is_df.loc['Non-cash or non-operating items'] - is_df.loc['= Net Financial expense/(income)'])
        is_df.loc['Income Tax Expenses'] = is_get('Income Tax Expenses')[yr_int]
        is_df.loc['Net profit'] = is_get('Net Profit')[yr_int]
        is_df.loc['Net Profit Attributable To Owners Of The Parent Company'] = is_get('Net Profit Attributable To Owners Of The Parent Company')[yr_int]
        r = is_df.loc['Net Profit Attributable To Owners Of The Parent Company'] / is_df.loc['Net profit'].replace(0, float('nan'))
        is_df.loc['Net Profit Attributable To Owners Of The Parent Company/Net profit'] = r.replace([float('inf'), -float('inf')], 0).fillna(0)
    except Exception as e:
        return {"message": f"[step: bs_is] {e}"}

    try:
        # Sales forecast
        rev_hist = df_is.loc['Operating Revenue']
        forecast_years = list(range(end_year + 1, end_year + 4))
        all_years = sorted(set(int(y) for y in rev_hist.index).union(int(y) for y in forecast_years))
        sales_forecast = pd.DataFrame(index=['Total Revenue', 'YOY Growth Rate'], columns=all_years)
        for y in rev_hist.index:
            sales_forecast.at['Total Revenue', y] = rev_hist[y]
        prev = None
        for y in rev_hist.index:
            if prev is not None and rev_hist[prev] and rev_hist[prev] != 0:
                sales_forecast.at['YOY Growth Rate', y] = (rev_hist[y] - rev_hist[prev]) / rev_hist[prev]
            prev = y
        last_rev = float(rev_hist.iloc[-1])
        for y in sorted(forecast_years):
            g = sales_growth.get(y, sales_growth.get(str(y), sales_growth.get('default', 0.0)))
            last_rev *= (1 + float(g))
            sales_forecast.at['Total Revenue', y] = last_rev
            sales_forecast.at['YOY Growth Rate', y] = float(g)
    except Exception as e:
        return {"message": f"[step: sales_forecast] {e}"}

    try:
        # Assumption table
        def safe_float(v, default=0.0):
            try:
                return 0.0 if v is None or pd.isna(v) else float(v)
            except Exception:
                return default

        yrs_assumption = list(range(start_year + 1, end_year + 1))
        assumption_rows = [
            'Cost of goods sold/Sales', 'Main operating expenses/Sales',
            'Non-cash or non-operating items/Sales', 'All others/Sales',
            'Income tax expenses/Total profits', 'Notes and accounts receivable/Sales',
            'Inventory/Sales', 'Total Other current assets/Sales',
            'Property, Plant and Equipment/Sales', 'Intangible assets/Sales',
            'Total other non-current assets/Sales', 'Short debt/Sales',
            'Notes and account payable/Sales', 'Total Other current liabilities/Sales',
            'Long-term debt/Sales', 'Total Other non-current liabilities/Sales',
            'Interest expense/(Short-debt+long-term debt)', 'Interest revenue/Cash and equivalent',
            'Dividends payout ratio', 'Depreciation rate',
        ]
        assumption_df = pd.DataFrame(index=assumption_rows, columns=yrs_assumption, dtype=float)
        for year in yrs_assumption:
            rev = safe_float(is_df.at['Total Revenue', year])
            tp = safe_float(is_df.at['Total profit', year])
            assumption_df.at['Cost of goods sold/Sales', year] = safe_float(is_df.at['Cost of goods sold', year]) / rev if rev else 0.0
            assumption_df.at['Main operating expenses/Sales', year] = ((safe_float(is_df.at['Main operating expenses', year])) / rev) if rev else 0.0
            assumption_df.at['Non-cash or non-operating items/Sales', year] = safe_float(is_df.at['Non-cash or non-operating items', year]) / rev if rev else 0.0
            assumption_df.at['All others/Sales', year] = 0.0
            assumption_df.at['Income tax expenses/Total profits', year] = safe_float(is_df.at['Income Tax Expenses', year]) / tp if tp else 0.0
            assumption_df.at['Notes and accounts receivable/Sales', year] = safe_float(bs_df.at['Notes and accounts receivable', year]) / rev if rev else 0.0
            assumption_df.at['Inventory/Sales', year] = safe_float(bs_df.at['Inventory', year]) / rev if rev else 0.0
            assumption_df.at['Total Other current assets/Sales', year] = safe_float(bs_df.at['Total other current assets', year]) / rev if rev else 0.0
            assumption_df.at['Property, Plant and Equipment/Sales', year] = safe_float(bs_df.at['Property, Plant and Equipment', year]) / rev if rev else 0.0
            assumption_df.at['Intangible assets/Sales', year] = safe_float(bs_df.at['Intangible assets', year]) / rev if rev else 0.0
            assumption_df.at['Total other non-current assets/Sales', year] = safe_float(bs_df.at['Total other non-current assets', year]) / rev if rev else 0.0
            assumption_df.at['Short debt/Sales', year] = safe_float(bs_df.at['Short debt', year]) / rev if rev else 0.0
            assumption_df.at['Notes and account payable/Sales', year] = safe_float(bs_df.at['Notes and account payable', year]) / rev if rev else 0.0
            assumption_df.at['Total Other current liabilities/Sales', year] = safe_float(bs_df.at['Total other current liabilities', year]) / rev if rev else 0.0
            assumption_df.at['Long-term debt/Sales', year] = safe_float(bs_df.at['Long-term debt', year]) / rev if rev else 0.0
            assumption_df.at['Total Other non-current liabilities/Sales', year] = safe_float(bs_df.at['Total other non-current liabilities', year]) / rev if rev else 0.0
            debt = safe_float(bs_df.at['Short debt', year]) + safe_float(bs_df.at['Long-term debt', year])
            assumption_df.at['Interest expense/(Short-debt+long-term debt)', year] = safe_float(is_df.at['+ Interest expense', year]) / debt if debt else 0.0
            cash_val = safe_float(bs_df.at['Cash and equivalent', year])
            assumption_df.at['Interest revenue/Cash and equivalent', year] = 0.0 if cash_val == 0 else 0.0
            assumption_df.at['Dividends payout ratio', year] = dividends_payout_ratio.get(year, dividends_payout_ratio.get(str(year), 0.0))
            assumption_df.at['Depreciation rate', year] = depreciation_rate.get(year, depreciation_rate.get(str(year), 0.0))
    except Exception as e:
        return {"message": f"[step: assumption_table] {e}"}

    try:
        # Compute scalars for A4
        latest = end_year
        short_debt = safe_float(bs_df.at['Short debt', latest])
        long_debt = safe_float(bs_df.at['Long-term debt', latest])
        D = short_debt + long_debt
        Cash_Latest = safe_float(bs_df.at['Cash and equivalent', latest])
        Minority_Latest = safe_float(bs_df.at['Minority interests', latest])
        tp_val = safe_float(is_df.at['Total profit', latest])
        tax_val = safe_float(is_df.at['Income Tax Expenses', latest])
        TaxRate = tax_val / tp_val if tp_val else 0.0
        nfe_val = safe_float(is_df.at['= Net Financial expense/(income)', latest])
        Rd = nfe_val / D if D else 0.0
    except Exception as e:
        return {"message": f"[step: scalars] {e}"}

    try:
        # FCFF for forecast years
        fcff_list = []
        fcff_table = pd.DataFrame(
            index=['Revenue', 'COGS', 'EBIT', 'Tax', 'NOPAT', 'D&A', 'Non-cash',
                   'Delta_AR', 'Delta_Inventory', 'Delta_AP', 'CAPEX',
                   'Net Fin Exp (1-tax)', 'FCFF'],
            columns=forecast_years, dtype=float)
        prev_rev_val = float(rev_hist.iloc[-1])
        for idx_f, yr_f in enumerate(forecast_years):
            rev_f = safe_float(sales_forecast.at['Total Revenue', yr_f])
            cogs_r = safe_float(assumption_df.loc['Cost of goods sold/Sales', yrs_assumption].mean())
            opex_r = safe_float(assumption_df.loc['Main operating expenses/Sales', yrs_assumption].mean())
            ar_r = safe_float(assumption_df.loc['Notes and accounts receivable/Sales', yrs_assumption].mean())
            inv_r = safe_float(assumption_df.loc['Inventory/Sales', yrs_assumption].mean())
            ap_r = safe_float(assumption_df.loc['Notes and account payable/Sales', yrs_assumption].mean())
            ppe_r = safe_float(assumption_df.loc['Property, Plant and Equipment/Sales', yrs_assumption].mean())
            intan_r = safe_float(assumption_df.loc['Intangible assets/Sales', yrs_assumption].mean())
            depr_r = safe_float(depreciation_rate.get(yr_f, depreciation_rate.get(str(yr_f), depreciation_rate.get('default', 0.05))))
            noncash_r = safe_float(assumption_df.loc['Non-cash or non-operating items/Sales', yrs_assumption].mean())
            tax_r = TaxRate
            cogs = rev_f * cogs_r
            opex = rev_f * opex_r
            ebit = rev_f - cogs - opex
            tax_val_f = ebit * tax_r if ebit > 0 else 0.0
            nopat = ebit - tax_val_f
            depr = rev_f * ppe_r * depr_r
            noncash = rev_f * noncash_r
            ar_now = rev_f * ar_r
            inv_now = rev_f * inv_r
            ap_now = rev_f * ap_r
            ar_prev = prev_rev_val * ar_r
            inv_prev = prev_rev_val * inv_r
            ap_prev = prev_rev_val * ap_r
            ppe_prev = prev_rev_val * ppe_r
            intan_prev = prev_rev_val * intan_r
            capex = (rev_f * ppe_r - ppe_prev) + (rev_f * intan_r - intan_prev)
            netfin = Rd * D * (1 - tax_r) if D else 0.0
            fcff_val = nopat + depr - noncash - (ar_now - ar_prev) - (inv_now - inv_prev) + (ap_now - ap_prev) - capex + netfin
            fcff_table.at['Revenue', yr_f] = rev_f
            fcff_table.at['COGS', yr_f] = cogs
            fcff_table.at['EBIT', yr_f] = ebit
            fcff_table.at['Tax', yr_f] = tax_val_f
            fcff_table.at['NOPAT', yr_f] = nopat
            fcff_table.at['D&A', yr_f] = depr
            fcff_table.at['Non-cash', yr_f] = noncash
            fcff_table.at['Delta_AR', yr_f] = ar_now - ar_prev
            fcff_table.at['Delta_Inventory', yr_f] = inv_now - inv_prev
            fcff_table.at['Delta_AP', yr_f] = ap_now - ap_prev
            fcff_table.at['CAPEX', yr_f] = capex
            fcff_table.at['Net Fin Exp (1-tax)', yr_f] = netfin
            fcff_table.at['FCFF', yr_f] = fcff_val
            fcff_list.append(fcff_val)
            prev_rev_val = rev_f
        FCFF_Stage_1 = json.dumps(fcff_list)
    except Exception as e:
        return {"message": f"[step: fcff] {e}"}

    try:
        # Forward projected BS and IS (course-aligned, with fixed-point cash loop)
        bs_fwd = bs_df.copy()
        is_fwd = is_df.copy()
        for d in (bs_fwd, is_fwd):
            d.columns = d.columns.astype(str)
        yh = list(bs_fwd.columns)
        yf_str = [str(y) for y in forecast_years]
        for d in (bs_fwd, is_fwd):
            for y in yf_str:
                d[y] = float('nan')

        ratio_tbl = {}
        for idx in assumption_df.index:
            ratio_tbl[idx] = float(assumption_df.loc[idx, yrs_assumption].mean())
        for row_name, overrides in other_ratios.items():
            if isinstance(overrides, dict):
                for yr_k, val in overrides.items():
                    ratio_tbl[row_name] = float(val)

        def r(row, yr):
            if row in ratio_tbl:
                return ratio_tbl[row]
            return 0.0

        sales = {}
        for y in forecast_years:
            sales[y] = safe_float(sales_forecast.at['Total Revenue', y])
        mp_val = safe_float(is_df.at['Net Profit Attributable To Owners Of The Parent Company/Net profit', latest]) if latest in is_df.columns else 1.0
        payout = float(dividends_payout_ratio.get('default', 0.0))

        for yr in forecast_years:
            yr_s = str(yr)
            rev = sales[yr]
            is_fwd.at['Total Revenue', yr_s] = rev
            is_fwd.at['Cost of goods sold', yr_s] = r('Cost of goods sold/Sales', yr) * rev
            is_fwd.at['Main operating expenses', yr_s] = r('Main operating expenses/Sales', yr) * rev
            is_fwd.at['Non-cash or non-operating items', yr_s] = r('Non-cash or non-operating items/Sales', yr) * rev
            is_fwd.at['All others', yr_s] = 0.0
            nfe_prev = [is_fwd.at['= Net Financial expense/(income)', y] for y in (yh + yf_str[:yf_str.index(yr_s)]) if y in is_fwd.columns]
            avg_nfe = sum(float(v) for v in nfe_prev if not pd.isna(v)) / max(len(nfe_prev), 1)
            is_fwd.at['+ Others (Net financial expense)', yr_s] = avg_nfe
            slr = r('Interest expense/(Short-debt+long-term debt)', yr)
            cr = r('Interest revenue/Cash and equivalent', yr)
            bs_fwd.at['Notes and accounts receivable', yr_s] = r('Notes and accounts receivable/Sales', yr) * rev
            bs_fwd.at['Inventory', yr_s] = r('Inventory/Sales', yr) * rev
            bs_fwd.at['Total other current assets', yr_s] = r('Total Other current assets/Sales', yr) * rev
            bs_fwd.at['Property, Plant and Equipment', yr_s] = r('Property, Plant and Equipment/Sales', yr) * rev
            bs_fwd.at['Intangible assets', yr_s] = r('Intangible assets/Sales', yr) * rev
            bs_fwd.at['Total other non-current assets', yr_s] = r('Total other non-current assets/Sales', yr) * rev
            bs_fwd.at['Short debt', yr_s] = r('Short debt/Sales', yr) * rev
            bs_fwd.at['Notes and account payable', yr_s] = r('Notes and account payable/Sales', yr) * rev
            bs_fwd.at['Total other current liabilities', yr_s] = r('Total Other current liabilities/Sales', yr) * rev
            bs_fwd.at['Long-term debt', yr_s] = r('Long-term debt/Sales', yr) * rev
            bs_fwd.at['Total other non-current liabilities', yr_s] = r('Total Other non-current liabilities/Sales', yr) * rev
            prev_yr = str(yr - 1)
            ret_beg = safe_float(bs_fwd.at['Retained earnings', prev_yr]) if prev_yr in bs_fwd.columns else safe_float(bs_fwd.at['Retained earnings', yh[-1]])
            cash_val = 0.0
            for _ in range(100):
                prev_cash = cash_val
                ie = slr * (safe_float(bs_fwd.at['Short debt', yr_s]) + safe_float(bs_fwd.at['Long-term debt', yr_s]))
                ii = cr * cash_val
                is_fwd.at['+ Interest expense', yr_s] = ie
                is_fwd.at['- Interest income', yr_s] = ii
                nfe = ie - ii + avg_nfe
                is_fwd.at['= Net Financial expense/(income)', yr_s] = nfe
                tp = rev - safe_float(is_fwd.at['Cost of goods sold', yr_s]) - safe_float(is_fwd.at['Main operating expenses', yr_s]) + safe_float(is_fwd.at['Non-cash or non-operating items', yr_s]) - nfe
                is_fwd.at['Total profit', yr_s] = tp
                tax = r('Income tax expenses/Total profits', yr) * tp if tp > 0 else 0.0
                is_fwd.at['Income Tax Expenses', yr_s] = tax
                net_profit = tp - tax
                is_fwd.at['Net profit', yr_s] = net_profit
                is_fwd.at['Net Profit Attributable To Owners Of The Parent Company', yr_s] = mp_val * net_profit
                is_fwd.at['Net Profit Attributable To Owners Of The Parent Company/Net profit', yr_s] = mp_val
                ret_end = ret_beg + mp_val * net_profit - payout * mp_val * net_profit
                bs_fwd.at['Retained earnings', yr_s] = ret_end
                bs_fwd.at['Minority interests', yr_s] = safe_float(bs_fwd.at['Minority interests', yh[-1]])
                bs_fwd.at['Others', yr_s] = safe_float(bs_fwd.at['Others', yh[-1]])
                bs_fwd.at["Total shareholders' equity", yr_s] = ret_end + safe_float(bs_fwd.at['Minority interests', yr_s]) + safe_float(bs_fwd.at['Others', yr_s])
                bs_fwd.at['Total current assets', yr_s] = cash_val + safe_float(bs_fwd.at['Notes and accounts receivable', yr_s]) + safe_float(bs_fwd.at['Inventory', yr_s]) + safe_float(bs_fwd.at['Total other current assets', yr_s])
                bs_fwd.at['Total non-current assets', yr_s] = safe_float(bs_fwd.at['Property, Plant and Equipment', yr_s]) + safe_float(bs_fwd.at['Intangible assets', yr_s]) + safe_float(bs_fwd.at['Total other non-current assets', yr_s])
                bs_fwd.at['Total assets', yr_s] = bs_fwd.at['Total current assets', yr_s] + bs_fwd.at['Total non-current assets', yr_s]
                bs_fwd.at['Total current liabilities', yr_s] = safe_float(bs_fwd.at['Short debt', yr_s]) + safe_float(bs_fwd.at['Notes and account payable', yr_s]) + safe_float(bs_fwd.at['Total other current liabilities', yr_s])
                bs_fwd.at['Total non-current liabilities', yr_s] = safe_float(bs_fwd.at['Long-term debt', yr_s]) + safe_float(bs_fwd.at['Total other non-current liabilities', yr_s])
                bs_fwd.at['Total liabilities', yr_s] = bs_fwd.at['Total current liabilities', yr_s] + bs_fwd.at['Total non-current liabilities', yr_s]
                cash_val = bs_fwd.at['Total liabilities', yr_s] + bs_fwd.at["Total shareholders' equity", yr_s] - (bs_fwd.at['Total assets', yr_s] - cash_val)
                if abs(cash_val - prev_cash) < 0.01:
                    break
            bs_fwd.at['Cash and equivalent', yr_s] = cash_val
            bs_fwd.at['Total current assets', yr_s] = cash_val + safe_float(bs_fwd.at['Notes and accounts receivable', yr_s]) + safe_float(bs_fwd.at['Inventory', yr_s]) + safe_float(bs_fwd.at['Total other current assets', yr_s])
            bs_fwd.at['Total assets', yr_s] = bs_fwd.at['Total current assets', yr_s] + bs_fwd.at['Total non-current assets', yr_s]
            bs_fwd.at["Total liabilities and shareholders' equity", yr_s] = bs_fwd.at['Total liabilities', yr_s] + bs_fwd.at["Total shareholders' equity", yr_s]
            bs_fwd.at['check', yr_s] = bs_fwd.at['Total assets', yr_s] - bs_fwd.at["Total liabilities and shareholders' equity", yr_s]
    except Exception as e:
        return {"message": f"[step: fwd_bs_is] {e}"}

    return {
        "message": "Forecast tables built successfully.",
        "sales_forecast": sales_forecast.to_markdown(),
        "assumption_table": assumption_df.to_markdown(),
        "forecast_years": forecast_years,
        "bs_forecast": bs_fwd.to_markdown(),
        "is_forecast": is_fwd.to_markdown(),
        "fcff_table": fcff_table.to_markdown(),
        "FCFF_Stage_1": FCFF_Stage_1,
        "Rd": Rd,
        "D": D,
        "TaxRate": TaxRate,
        "Cash_Latest": Cash_Latest,
        "Minority_Latest": Minority_Latest,
    }
