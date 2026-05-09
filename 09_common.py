"""Shared helpers for the CDMO valuation agent tools.

These helpers are written to be copied into a Coze Python tool project or used
as the shared source for local testing. Keep the code English-only so the
platform prompt can reuse it directly.
"""

from __future__ import annotations

from contextlib import contextmanager
from io import StringIO
from typing import Iterator, Optional

import pandas as pd


@contextmanager
def temporary_stdin(text: str) -> Iterator[None]:
    """Temporarily replace stdin for libraries that expect interactive login."""
    import sys

    original_stdin = sys.stdin
    sys.stdin = StringIO(text)
    try:
        yield
    finally:
        sys.stdin = original_stdin


@contextmanager
def wrds_connection(username: str, password: str):
    """Open a WRDS connection using non-interactive credentials."""
    import wrds

    login_text = f"{username}\n{password}\nn\n"
    with temporary_stdin(login_text):
        connection = wrds.Connection()
    try:
        yield connection
    finally:
        try:
            connection.close()
        except Exception:
            pass


def safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float and fall back to a default on failure."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def normalize_year_range(start_year: int, end_year: int) -> list[int]:
    """Return a closed year range."""
    return list(range(int(start_year), int(end_year) + 1))


def build_zero_series(years: list[int]) -> pd.Series:
    """Create a zero-filled series indexed by years."""
    return pd.Series({year: 0.0 for year in years}, dtype=float)


def first_available_row(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first matching row label in a dataframe index."""
    for candidate in candidates:
        if candidate in df.index:
            return candidate
    return None


def format_message_list(items: list[str]) -> list[str]:
    """Remove empty items and trim the rest."""
    cleaned = []
    for item in items:
        text = str(item).strip()
        if text:
            cleaned.append(text)
    return cleaned


def yearly_growth_table(series: pd.Series) -> pd.Series:
    """Convert a yearly series into a year-over-year growth series."""
    growth = series.pct_change()
    growth = growth.replace([float("inf"), float("-inf")], pd.NA)
    return growth

