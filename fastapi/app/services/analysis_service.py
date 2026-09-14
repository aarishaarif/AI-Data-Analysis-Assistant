import re
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from app.config import settings
from app.services.dataset_service import read_dataframe


def _column(question: str, columns: list[str]) -> str | None:
    normalized = question.lower()
    return next((column for column in columns if column.lower() in normalized), None)


def _chart(frame: pd.DataFrame, column: str, kind: str = "bar") -> str:
    settings.chart_storage_path.mkdir(parents=True, exist_ok=True)
    chart_id = uuid4().hex
    path = settings.chart_storage_path / f"{chart_id}.png"
    fig, axis = plt.subplots(figsize=(7, 4))
    if kind == "histogram":
        pd.to_numeric(frame[column], errors="coerce").dropna().plot.hist(ax=axis, bins=20, color="#55b99d")
        axis.set_ylabel("Rows")
    else:
        frame[column].value_counts(dropna=False).head(12).sort_values().plot.barh(ax=axis, color="#55b99d")
        axis.set_xlabel("Rows")
    axis.set_title(column)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return chart_id


def answer_question(file_path: str, question: str) -> tuple[str, dict, dict | None]:
    frame = read_dataframe(file_path)
    clean_question = question.strip().lower()
    columns = [str(column) for column in frame.columns]
    matched = _column(clean_question, columns)

    if any(token in clean_question for token in ("overview", "describe", "summary")):
        return (
            f"This dataset has **{len(frame):,} rows** and **{len(columns)} columns**. It contains **{int(frame.isna().sum().sum()):,} missing values** and **{int(frame.duplicated().sum()):,} duplicate rows**.",
            {"type": "profile", "columns": columns}, None,
        )
    if "missing" in clean_question:
        missing = frame.isna().sum()
        present = missing[missing > 0]
        detail = "No missing values were found." if present.empty else "; ".join(f"**{name}**: {int(count):,}" for name, count in present.items())
        return detail, {"type": "missing_values", "columns": [str(name) for name in present.index]}, None
    if not matched:
        return f"I could not match that question to a column. Available columns are: {', '.join(columns)}.", {"type": "validation", "columns": columns}, None

    series = frame[matched]
    numeric = pd.api.types.is_numeric_dtype(series)
    wants_chart = any(token in clean_question for token in ("chart", "graph", "plot", "distribution", "show"))
    if numeric and any(token in clean_question for token in ("average", "mean")):
        value = series.mean()
        return f"The average **{matched}** is **{value:,.2f}**.", {"type": "mean", "columns": [matched], "value": float(value)}, None
    if numeric and "median" in clean_question:
        value = series.median()
        return f"The median **{matched}** is **{value:,.2f}**.", {"type": "median", "columns": [matched], "value": float(value)}, None
    if numeric and wants_chart:
        chart_id = _chart(frame, matched, "histogram")
        return f"Here is the distribution of **{matched}**, calculated from your uploaded dataset.", {"type": "distribution", "columns": [matched]}, {"type": "histogram", "chart_id": chart_id}
    if not numeric:
        top = series.value_counts(dropna=False).head(1)
        value, count = top.index[0], int(top.iloc[0])
        chart = {"type": "bar", "chart_id": _chart(frame, matched)} if wants_chart else None
        return f"The most common **{matched}** value is **{value}** with **{count:,} rows**.", {"type": "value_counts", "columns": [matched]}, chart
    return f"For **{matched}**: mean **{series.mean():,.2f}**, median **{series.median():,.2f}**, minimum **{series.min():,.2f}**, maximum **{series.max():,.2f}**.", {"type": "statistics", "columns": [matched]}, None
