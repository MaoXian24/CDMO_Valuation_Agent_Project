from runtime import Args
from typings.Get_DCF.Get_DCF import Input, Output

import json

"""DCF tool for the CDMO agent.

The tool calculates a standard FCFF-based valuation with a multi-stage setup.
"""


def _calculate_npv(rate: float, cashflows: list[float]) -> float:
    total = 0.0
    for period, cashflow in enumerate(cashflows, start=1):
        total += cashflow / ((1 + rate) ** period)
    return total


def _parse_json_list(text: str, field_name: str) -> list:
    if not text:
        raise ValueError(f"{field_name} is required.")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be a valid JSON list. Error: {exc}") from exc
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON list.")
    return value


def handler(args: Args[Input]) -> Output:
    import pandas as pd

    try:
        shares_outstanding = float(args.input.shares_outstanding)
        current_price = float(args.input.current_price)
        n_years_2nd_stage = int(args.input.n_years_2nd_stage)
        growth_rate_2nd_stage = float(args.input.growth_rate_2nd_stage)
        long_term_growth = float(args.input.long_term_growth)
        Rf = float(args.input.Rf)
        beta = float(args.input.beta)
        E_Rm = float(args.input.E_Rm) if args.input.E_Rm is not None else 0.065
        Rd = float(args.input.Rd)
        D = float(args.input.D)
        TaxRate = float(args.input.TaxRate)
        FCFF_Stage_1 = _parse_json_list(args.input.FCFF_Stage_1, "FCFF_Stage_1")
        end_year = int(args.input.end_year)
        Cash_Latest = float(args.input.Cash_Latest)
        Minority_Latest = float(args.input.Minority_Latest)
    except Exception as exc:
        return {"message": f"Failed to read the parameters. Error: {exc}"}

    try:
        Re = Rf + beta * (E_Rm - Rf)
        market_value_of_equity = current_price * shares_outstanding
        WACC = (Re * market_value_of_equity + Rd * D * (1 - TaxRate)) / (market_value_of_equity + D) if (market_value_of_equity + D) else 0.0

        # Extend stage 1 into stage 2 using the user-approved growth bridge.
        fcff_stage_2 = []
        for _ in range(end_year + 1, end_year + n_years_2nd_stage + 1):
            if not fcff_stage_2:
                fcff_stage_2.append(FCFF_Stage_1[-1] * (1 + growth_rate_2nd_stage))
            else:
                fcff_stage_2.append(fcff_stage_2[-1] * (1 + growth_rate_2nd_stage))

        first_stage = _calculate_npv(WACC, FCFF_Stage_1)
        second_stage = _calculate_npv(WACC, fcff_stage_2) / ((1 + WACC) ** len(FCFF_Stage_1))
        # Course plugin convention: TV is computed AT the end of the forecast horizon + 1 year,
        # then discounted back by (N1+N2) years.  Equivalent to multiplying by (1+WACC) in the numerator.
        third_stage = (fcff_stage_2[-1] * (1 + long_term_growth) * (1 + WACC)) / (WACC - long_term_growth) / ((1 + WACC) ** (len(FCFF_Stage_1) + len(fcff_stage_2))) if WACC > long_term_growth else 0.0
        enterprise_value = first_stage + second_stage + third_stage
        equity_value = enterprise_value + Cash_Latest - Minority_Latest - D
        value_per_share = equity_value / shares_outstanding if shares_outstanding else 0.0

        valuation_table = pd.DataFrame(
            {
                "Description": [
                    "First stage",
                    "Second stage",
                    "Third stage (Terminal value)",
                    "Enterprise Value",
                    "+ Cash at latest reporting date",
                    "- Minority interests at latest reporting date",
                    "- (Short-term debt + Long-term debt)",
                    "= Value to shareholders of the company",
                    "Total shares",
                    "Value per share",
                ],
                "Discounted FCFF": [
                    first_stage,
                    second_stage,
                    third_stage,
                    enterprise_value,
                    Cash_Latest,
                    Minority_Latest,
                    D,
                    equity_value,
                    shares_outstanding,
                    value_per_share,
                ],
            }
        )
        valuation_table = valuation_table.set_index("Description")

        sensitivity = json.dumps({
            "WACC": WACC,
            "Re": Re,
            "terminal_growth": long_term_growth,
        })
        return {
            "dcf": valuation_table.to_markdown(),
            "vps": value_per_share,
            "wacc": WACC,
            "sensitivity": sensitivity,
        }
    except Exception as exc:
        return {"message": f"Failed to calculate DCF. Error: {exc}"}
