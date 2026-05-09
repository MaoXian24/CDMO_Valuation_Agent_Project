from runtime import Args
from typings.Chart_Generator.Chart_Generator import Input, Output

import json
import base64
from io import BytesIO

"""Chart generator for the CDMO agent.

Generates publication-quality financial charts: line, bar, pie, stacked bar,
grouped bar.  All charts use matplotlib with a clean professional style.
Returns a base64-encoded PNG ready for inline display.
"""

# ── professional colour palette ──────────────────────────────────────────
COLOURS = [
    "#2C3E50", "#E74C3C", "#27AE60", "#2980B9", "#F39C12",
    "#8E44AD", "#1ABC9C", "#D35400", "#7F8C8D", "#C0392B",
]
BACKGROUND = "#FFFFFF"
GRID_COLOUR = "#E0E0E0"
TITLE_COLOUR = "#2C3E50"


def _make_figure(figsize=(10, 5.5)):
    """Return (fig, ax) with a clean white background."""
    import matplotlib
    matplotlib.use("Agg")                         # non-interactive backend
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize, facecolor=BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    return fig, ax


def _finalise(fig, ax, title: str, xlabel: str, ylabel: str):
    """Apply titles, grid, tight layout and encode to base64 PNG."""
    import matplotlib.pyplot as plt

    ax.set_title(title, fontsize=14, fontweight="bold", color=TITLE_COLOUR, pad=14)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=11, color="#555555")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=11, color="#555555")
    ax.tick_params(labelsize=10, colors="#444444")
    ax.grid(True, linestyle="--", alpha=0.5, color=GRID_COLOUR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout(pad=2)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


# ═══════════════════════════════════════════════════════════════════════════
#  Chart builders
# ═══════════════════════════════════════════════════════════════════════════

def _line_chart(data, title, xlabel, ylabel):
    """data: {"labels": [...], "series": [{"name":"A","values":[...]}, ...]}"""
    fig, ax = _make_figure()
    for i, s in enumerate(data.get("series", [])):
        ax.plot(data["labels"], s["values"], marker="o", linewidth=2.2,
                color=COLOURS[i % len(COLOURS)], label=s.get("name", f"Series {i+1}"),
                markersize=5)
    if any(s.get("name") for s in data.get("series", [])):
        ax.legend(frameon=True, fontsize=9, loc="best")
    b64 = _finalise(fig, ax, title, xlabel, ylabel)
    return b64


def _bar_chart(data, title, xlabel, ylabel):
    """data: {"labels": [...], "series": [{"name":"A","values":[...]}, ...]}"""
    import numpy as np
    fig, ax = _make_figure()
    series_list = data.get("series", [{"name":"", "values": data.get("values", [])}])
    n_groups = len(data["labels"])
    n_bars = len(series_list)
    bar_w = 0.7 / max(n_bars, 1)
    x = np.arange(n_groups)
    for i, s in enumerate(series_list):
        vals = s.get("values", [])
        offset = (i - (n_bars - 1) / 2) * bar_w
        ax.bar(x + offset, vals, bar_w * 0.88, color=COLOURS[i % len(COLOURS)],
               label=s.get("name", f"Series {i+1}"), edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(data["labels"])
    if any(s.get("name") for s in series_list):
        ax.legend(frameon=True, fontsize=9, loc="best")
    b64 = _finalise(fig, ax, title, xlabel, ylabel)
    return b64


def _pie_chart(data, title, xlabel, ylabel):
    """data: {"labels": [...], "values": [...]}"""
    fig, ax = _make_figure(figsize=(7, 7))
    vals = data.get("values", [])
    labels = data.get("labels", [])
    # Filter out zero / negative values (pie doesn't handle them well)
    filtered = [(l, v) for l, v in zip(labels, vals) if v and v > 0]
    if not filtered:
        raise ValueError("Pie chart requires at least one positive value.")
    lbls, vls = zip(*filtered)
    wedges, texts, autotexts = ax.pie(
        vls, labels=lbls, autopct="%1.1f%%",
        colors=COLOURS[:len(lbls)], startangle=140,
        textprops={"fontsize": 10}, pctdistance=0.75)
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title(title, fontsize=14, fontweight="bold", color=TITLE_COLOUR, pad=14)
    fig.tight_layout(pad=2)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=BACKGROUND)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    import matplotlib.pyplot as _plt
    _plt.close(fig)
    return b64


def _stacked_bar_chart(data, title, xlabel, ylabel):
    """data: {"labels": [...], "series": [{"name":"A","values":[...]}, ...]}"""
    import numpy as np
    fig, ax = _make_figure()
    labels = data["labels"]
    series_list = data.get("series", [])
    x = np.arange(len(labels))
    bottoms = np.zeros(len(labels))
    for i, s in enumerate(series_list):
        vals = s.get("values", [])
        ax.bar(x, vals, 0.55, bottom=bottoms, color=COLOURS[i % len(COLOURS)],
               label=s.get("name", ""), edgecolor="white", linewidth=0.5)
        bottoms = bottoms + np.array(vals)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    if any(s.get("name") for s in series_list):
        ax.legend(frameon=True, fontsize=9, loc="best")
    b64 = _finalise(fig, ax, title, xlabel, ylabel)
    return b64


def _waterfall_chart(data, title, xlabel, ylabel):
    """data: {"labels": [...], "values": [...]} — simple waterfall (bar chart with colour coding)."""
    import numpy as np
    fig, ax = _make_figure(figsize=(10, 5.5))
    labels = data["labels"]
    values = data.get("values", [])
    n = len(labels)
    running = 0.0
    bottoms = []
    colours = []
    for i, v in enumerate(values):
        if i == 0:
            bottoms.append(0)
            colours.append(COLOURS[2])      # starting value — green
            running = v
        elif i == n - 1:
            bottoms.append(0)
            colours.append(COLOURS[0])      # ending value — dark
        elif v >= 0:
            bottoms.append(running)
            colours.append(COLOURS[2])
            running += v
        else:
            bottoms.append(running + v)
            colours.append(COLOURS[1])
            running += v
    ax.bar(range(n), values, 0.55, bottom=bottoms, color=colours,
           edgecolor="white", linewidth=0.5)
    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    b64 = _finalise(fig, ax, title, xlabel, ylabel)
    return b64


# ═══════════════════════════════════════════════════════════════════════════
#  Handler
# ═══════════════════════════════════════════════════════════════════════════

CHART_BUILDERS = {
    "line":        _line_chart,
    "bar":         _bar_chart,
    "pie":         _pie_chart,
    "stacked_bar": _stacked_bar_chart,
    "waterfall":   _waterfall_chart,
}


def handler(args: Args[Input]) -> Output:
    try:
        chart_type = args.input.chart_type
        chart_data = json.loads(args.input.chart_data)
        title = args.input.title or ""
        xlabel = args.input.x_label or ""
        ylabel = args.input.y_label or ""
    except Exception as exc:
        return {"message": f"Failed to parse inputs. Error: {exc}"}

    if chart_type not in CHART_BUILDERS:
        return {"message": f"Unsupported chart_type: '{chart_type}'. Supported: {list(CHART_BUILDERS.keys())}"}

    try:
        builder = CHART_BUILDERS[chart_type]
        image_b64 = builder(chart_data, title, xlabel, ylabel)
        return {
            "message": f"{chart_type} chart generated successfully.",
            "chart_image": image_b64,
        }
    except Exception as exc:
        return {"message": f"Failed to generate chart. Error: {exc}"}
