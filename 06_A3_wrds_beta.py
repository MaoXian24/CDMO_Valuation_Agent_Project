from runtime import Args
from typings.WRDS_Beta.WRDS_Beta import Input, Output

def handler(args: Args[Input]) -> Output:
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

    try:
        input_str = f"{WRDS_username}\n{WRDS_pwd}\nn\n"
        old_stdin = sys.stdin
        sys.stdin = StringIO(input_str)
        db = wrds.Connection()
        sys.stdin = old_stdin

        df = db.raw_sql(f"SELECT stkcd, trdmnt, clsdt, mclsprc FROM csmar.trd_mnth WHERE stkcd = '{stkcd}'")
        index = db.raw_sql("SELECT trddt, clsindex FROM csmar.trd_index WHERE indexcd = '000300'")
        db.close()
    except Exception as e:
        return {"message": f"Failed to connect to WRDS. Error: {e}"}

    try:
        df = df.rename(columns={"mclsprc": stkcd, "clsdt": "day"})
        df['year'] = (df['trdmnt'] / 100).astype(int)
        df['month'] = df['trdmnt'].astype(str).str[4:6].astype(int)
        df['trddt'] = pd.to_datetime(df[['year', 'month', 'day']])
        df = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
        df = df[['trddt', 'year', 'month', 'day', stkcd]]
        df['trddt'] = pd.to_datetime(df['trddt']).dt.date

        index = index.rename(columns={"clsindex": "CSI300"})
        index['trddt'] = pd.to_datetime(index['trddt']).dt.date

        prices = df.merge(index, on='trddt', how='left').sort_values('trddt')
        prices = prices.rename(columns={"trddt": "Date"})
        prices = prices[['Date', stkcd, 'CSI300']]
        df_p = prices.copy()
        df_p['Stock_Return'] = df_p[stkcd].pct_change()
        df_p['Index_Return'] = df_p['CSI300'].pct_change()
        df_p = df_p.dropna()

        if df_p.empty:
            return {"message": "Not enough data to estimate beta."}

        covariance = df_p['Stock_Return'].cov(df_p['Index_Return'])
        variance = df_p['Index_Return'].var()
        beta = covariance / variance if variance not in (0, None) else None
        latest_price = df_p[stkcd].iloc[-1]

        return {
            "message": "Beta estimated successfully.",
            "beta": beta,
            "price": latest_price,
            "sample_size": int(len(df_p)),
        }
    except Exception as e:
        return {"message": f"Failed to estimate beta. Error: {e}"}
