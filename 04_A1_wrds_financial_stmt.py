from runtime import Args
from typings.WRDS_Condensed_Financial_Stmt.WRDS_Condensed_Financial_Stmt import Input, Output

def handler(args: Args[Input]) -> Output:
    import json
    import wrds
    import pandas as pd
    import sys
    from io import StringIO

    WRDS_username = getattr(args.input, "WRDS_username", None)
    WRDS_pwd = getattr(args.input, "WRDS_pwd", None)
    stkcd = args.input.stkcd
    start_year = int(args.input.start_year)
    end_year = int(args.input.end_year)
    if not WRDS_username or not WRDS_pwd or not stkcd:
        return {"message": "WRDS_username, WRDS_pwd and stock code are required."}

    fbs = {
        'a001101000': 'Cash and cash equivalents',
        'a001107000': 'Trading Financial Assets',
        'a001109000': 'Net Short-term Investments',
        'a001110000': 'Net Notes Receivable',
        'a001111000': 'Net Accounts Receivable',
        'a001123000': 'Net Inventories',
        'a001100000': 'Total current assets',
        'a001212000': 'Net Fixed Assets',
        'a001218000': 'Net Intangible Assets',
        'a001200000': 'Total Non-current Assets',
        'a001000000': 'Total Assets',
        'a002101000': 'Short-Term Borrowings',
        'a002107000': 'Notes Payable',
        'a002108000': 'Accounts Payable',
        'a002100000': 'Total Current Liabilities',
        'a002201000': 'Long-term Loans',
        'a002200000': 'Total Non-current Liabilities',
        'a002000000': 'Total Liabilities',
        'a003105000': 'Retained Earnings',
        'a003200000': "Minority Shareholders' Interest",
        'a003000000': "Total Shareholders' Equity",
    }
    fis = {
        'b001101000': 'Operating Revenue',
        'b001201000': 'Operating Expenses',
        'b001207000': 'Tax And Additional Fees Of Operations',
        'b001209000': 'Selling Expenses',
        'b001210000': 'General And Administrative Expenses',
        'b001216000': 'R&D Expenses',
        'b001302000': 'Investment Gains',
        'b001212000': 'Asset Impairment Loss',
        'b001307000': 'Credit impairment loss',
        'b001301000': 'Gains/Losses From Fair Value Change',
        'b001308000': 'Income from Assets Disposal',
        'b001211000': 'Finance Expenses',
        'b001211101': 'Including: Interest Expenses',
        'b001211203': 'Including: Interest Income',
        'b001300000': 'Operating Profit',
        'b001400000': 'Non-Operating Income',
        'b001500000': 'Non-Operating Expenses',
        'b001000000': 'Total Profit',
        'b002100000': 'Income Tax Expenses',
        'b002000000': 'Net Profit',
        'b002000101': 'Net Profit Attributable To Owners Of The Parent Company',
    }

    var_bs = ', '.join(fbs.keys())
    var_is = ', '.join(fis.keys())
    filelist = {'bs': (var_bs, fbs), 'is': (var_is, fis)}

    try:
        input_str = f"{WRDS_username}\n{WRDS_pwd}\nn\n"
        old_stdin = sys.stdin
        sys.stdin = StringIO(input_str)
        db = wrds.Connection()
        sys.stdin = old_stdin

        for key, value in filelist.items():
            df = db.raw_sql(
                f"SELECT stkcd, accper, {value[0]} FROM csmar.wrds_csmar_financial_master "
                f"WHERE stkcd='{stkcd}' AND typrep='A'", date_cols=['accper'])
            df = df[df.accper.dt.month == 12]
            df.loc[:, 'year'] = pd.to_datetime(df['accper']).dt.year
            df.pop('accper')
            df = df[(df.year >= start_year) & (df.year <= end_year)]
            df.sort_values(by='year', inplace=True)
            df.rename(columns=value[1], inplace=True)
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
        yr = range(start_year, end_year + 1)
        zero = pd.Series({y: 0.0 for y in yr})

        def bs_get(*names):
            return sum((df_bs.loc[n].reindex(yr, fill_value=0) if n in df_bs.index else zero for n in names), zero)

        def is_get(name):
            if name in df_is.index:
                return df_is.loc[name].reindex(yr, fill_value=0)
            return pd.Series(0.0, index=pd.Index(yr, dtype=int))

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
        bs_df = pd.DataFrame(index=idx, columns=yr, dtype=float)

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
        ], columns=yr, dtype=float)

        is_df.loc['Total Revenue'] = is_get('Operating Revenue')[yr]
        is_df.loc['Cost of goods sold'] = is_get('Operating Expenses')[yr]
        is_df.loc['Main operating expenses'] = (is_get('Tax And Additional Fees Of Operations') + is_get('Selling Expenses') + is_get('General And Administrative Expenses') + is_get('R&D Expenses'))[yr]
        is_df.loc['Non-cash or non-operating items'] = (is_get('Investment Gains') - is_get('Asset Impairment Loss') - is_get('Credit impairment loss') + is_get('Gains/Losses From Fair Value Change') + is_get('Income from Assets Disposal') + is_get('Non-Operating Income') - is_get('Non-Operating Expenses'))[yr]
        is_df.loc['= Net Financial expense/(income)'] = is_get('Finance Expenses')[yr]
        is_df.loc['+ Interest expense'] = is_get('Including: Interest Expenses')[yr]
        is_df.loc['- Interest income'] = is_get('Including: Interest Income')[yr]
        is_df.loc['+ Others (Net financial expense)'] = is_df.loc['= Net Financial expense/(income)'] - is_df.loc['+ Interest expense'] + is_df.loc['- Interest income']
        is_df.loc['Total profit'] = is_get('Total Profit')[yr]
        is_df.loc['All others'] = is_df.loc['Total profit'] - (is_df.loc['Total Revenue'] - is_df.loc['Cost of goods sold'] - is_df.loc['Main operating expenses'] + is_df.loc['Non-cash or non-operating items'] - is_df.loc['= Net Financial expense/(income)'])
        is_df.loc['Income Tax Expenses'] = is_get('Income Tax Expenses')[yr]
        is_df.loc['Net profit'] = is_get('Net Profit')[yr]
        is_df.loc['Net Profit Attributable To Owners Of The Parent Company'] = is_get('Net Profit Attributable To Owners Of The Parent Company')[yr]
        r = is_df.loc['Net Profit Attributable To Owners Of The Parent Company'] / is_df.loc['Net profit'].replace(0, float('nan'))
        is_df.loc['Net Profit Attributable To Owners Of The Parent Company/Net profit'] = r.replace([float('inf'), -float('inf')], 0).fillna(0)

        sales_growth = {}
        rev = is_df.loc['Total Revenue']
        for i in range(1, len(yr)):
            prev_val, curr_val = rev.iloc[i - 1], rev.iloc[i]
            if prev_val and prev_val != 0:
                sales_growth[yr[i]] = (curr_val - prev_val) / prev_val

        other_ratios = {}
        for year in yr:
            revenue = is_df.at['Total Revenue', year] if 'Total Revenue' in is_df.index else 0.0
            if not revenue:
                continue
            total_profit = is_df.at['Total profit', year] if 'Total profit' in is_df.index else 0.0
            yr_dict = {}
            if 'Cost of goods sold' in is_df.index:
                yr_dict['Cost of goods sold/Sales'] = is_df.at['Cost of goods sold', year] / revenue
            if 'Main operating expenses' in is_df.index:
                yr_dict['Main operating expenses/Sales'] = is_df.at['Main operating expenses', year] / revenue
            if total_profit and 'Income Tax Expenses' in is_df.index:
                yr_dict['Income tax expenses/Total profits'] = is_df.at['Income Tax Expenses', year] / total_profit
            for row, key in [
                ('Notes and accounts receivable', 'Notes and accounts receivable/Sales'),
                ('Inventory', 'Inventory/Sales'),
                ('Property, Plant and Equipment', 'Property, Plant and Equipment/Sales'),
                ('Intangible assets', 'Intangible assets/Sales'),
                ('Short debt', 'Short debt/Sales'),
                ('Notes and account payable', 'Notes and account payable/Sales'),
                ('Long-term debt', 'Long-term debt/Sales'),
            ]:
                if row in bs_df.index:
                    yr_dict[key] = bs_df.at[row, year] / revenue
            other_ratios[year] = yr_dict

        return {
            "message": "Financial statements retrieved successfully.",
            "years": list(yr),
            "balance_sheet": bs_df.to_markdown(),
            "income_statement": is_df.to_markdown(),
            "bs_check": json.dumps(bs_df.loc['check'].to_dict()),
            "sales_growth": json.dumps(sales_growth),
            "other_ratios": json.dumps(other_ratios),
        }
    except Exception as e:
        return {"message": f"Failed to build statements. Error: {e}"}
