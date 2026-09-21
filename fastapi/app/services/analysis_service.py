"""Dataset-grounded natural-language analysis helpers.

This module deliberately uses pandas for every calculation.  Intent matching is
generic, while field matching is derived from the uploaded dataframe at runtime.
"""
import re
from difflib import get_close_matches
from pathlib import Path
from uuid import uuid4

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from app.config import settings
from app.services.dataset_service import infer_ml_task, read_dataframe


def _words(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def _mentioned(question: str, columns: list[str]) -> list[str]:
    """Resolve fields despite case, spaces, underscores, or small typos."""
    normalized = _words(question)
    hits = [
        column for column in columns
        if _words(column) and re.search(rf"(?:^|\s){re.escape(_words(column))}(?:\s|$)", normalized)
    ]
    if hits:
        return hits
    tokens, names = normalized.split(), {
        _words(column): column for column in columns if len(_words(column).split()) >= 2
    }
    phrases = [" ".join(tokens[left:right]) for left in range(len(tokens)) for right in range(left + 2, len(tokens) + 1)]
    for phrase in sorted(phrases, key=len, reverse=True):
        close = get_close_matches(phrase, names, n=1, cutoff=0.9)
        if close:
            return [names[close[0]]]
    return []


def _number(value: object) -> str:
    if pd.isna(value):
        return "missing"
    return f"{value:,.4g}" if isinstance(value, float) else f"{value:,}" if isinstance(value, int) else str(value)


def _numeric(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.select_dtypes(include="number").columns]


def _categorical(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns if column not in _numeric(frame)]


def _save_chart(figure: plt.Figure) -> str:
    settings.chart_storage_path.mkdir(parents=True, exist_ok=True)
    chart_id = uuid4().hex
    figure.tight_layout()
    figure.savefig(settings.chart_storage_path / f"{chart_id}.png", dpi=150)
    plt.close(figure)
    return chart_id


def _distribution_chart(frame: pd.DataFrame, column: str) -> dict:
    figure, axis = plt.subplots(figsize=(7, 4))
    if pd.api.types.is_numeric_dtype(frame[column]):
        frame[column].dropna().plot.hist(ax=axis, bins=20, color="#55b99d")
        axis.set_ylabel("Rows")
        kind = "histogram"
    else:
        frame[column].value_counts(dropna=False).head(15).sort_values().plot.barh(ax=axis, color="#55b99d")
        axis.set_xlabel("Rows")
        kind = "bar"
    axis.set_title(f"Distribution of {column}")
    return {"type": kind, "chart_id": _save_chart(figure)}


def _group_chart(frame: pd.DataFrame, category: str, value: str, operation: str) -> dict:
    grouped = frame.groupby(category, dropna=False)[value].agg(operation).sort_values().tail(15)
    figure, axis = plt.subplots(figsize=(7, 4))
    grouped.plot.barh(ax=axis, color="#55b99d")
    axis.set(title=f"{operation.title()} {value} by {category}", xlabel=f"{operation.title()} {value}")
    return {"type": "bar", "chart_id": _save_chart(figure)}


def _overview(frame: pd.DataFrame, columns: list[str]) -> str:
    return (
        f"This dataset has **{len(frame):,} rows** and **{len(columns)} columns** "
        f"({len(_numeric(frame))} numerical and {len(_categorical(frame))} categorical/text). It contains "
        f"**{int(frame.isna().sum().sum()):,} missing values** and **{int(frame.duplicated().sum()):,} duplicate rows**.\n\n"
        f"Columns: {', '.join(f'**{column}**' for column in columns)}."
    )


def _correlations(frame: pd.DataFrame, numeric: list[str]) -> tuple[str, dict]:
    if len(numeric) < 2:
        return "I need at least two numerical columns to calculate correlations.", {"type": "correlations", "columns": numeric}
    matrix, pairs = frame[numeric].corr(), []
    for index, left in enumerate(matrix.columns):
        for right in matrix.columns[index + 1:]:
            value = matrix.loc[left, right]
            if pd.notna(value):
                pairs.append((abs(float(value)), float(value), str(left), str(right)))
    strongest = sorted(pairs, reverse=True)[:8]
    if not strongest:
        return "There were not enough non-missing values to calculate correlations.", {"type": "correlations", "columns": numeric}
    result = "; ".join(f"**{left} ↔ {right}**: {_number(value)}" for _, value, left, right in strongest)
    return f"Strongest Pearson correlations: {result}.", {"type": "correlations", "columns": numeric, "pairs": [{"left": left, "right": right, "value": value} for _, value, left, right in strongest]}


def _important(frame: pd.DataFrame, recommendation: dict) -> tuple[list[str], list[str], str | None]:
    target = recommendation.get("target_column")
    if not target or target not in frame:
        return [], [], None
    excluded = {target}
    excluded.update(column for column in frame if str(column).lower().endswith(("_id", "id")) and frame[column].nunique() >= len(frame) * 0.8)
    numeric = frame.select_dtypes(include="number").drop(columns=list(excluded), errors="ignore")
    encoded = pd.Series(pd.factorize(frame[target])[0], index=frame.index).replace(-1, float("nan"))
    ranked = numeric.corrwith(encoded).abs().dropna().sort_values(ascending=False)
    text = [str(column) for column in frame if column not in excluded and any(word in str(column).lower() for word in ("text", "content", "review", "description", "prompt"))]
    return list(dict.fromkeys(text + [str(column) for column in ranked.head(5).index]))[:6], [str(column) for column in excluded if column != target], "absolute correlation" if len(ranked) else None


def _missing_column(question: str) -> str | None:
    match = re.search(r"(?:average|mean|median|minimum|maximum|min|max|sum|total|variance|distribution)\s+(?:of\s+)?([a-zA-Z][\w ]*?)(?:\?|$|\bby\b|\bfor\b)", question, re.I)
    return match.group(1).strip(" ?. ") if match else None


def answer_question(file_path: str, question: str, previous_question: str | None = None) -> tuple[str, dict, dict | None]:
    frame = read_dataframe(file_path)
    clean, columns = _words(question), [str(column) for column in frame.columns]
    mentioned = _mentioned(question, columns)
    if not mentioned and previous_question:  # natural follow-up: "what is the median?"
        mentioned = _mentioned(previous_question, columns)
    numeric, categorical = _numeric(frame), _categorical(frame)
    chart_requested = bool(re.search(r"\b(chart|graph|plot|visuali[sz]e|show)\b", clean))

    if re.search(r"\b(which|what) model\b|recommend model|model architecture|train a model", clean):
        recommendation = infer_ml_task(frame, Path(file_path).suffix.removeprefix("."))
        target = recommendation["target_column"]
        detail = f" using **{target}** as the target" if target else " after you select a target"
        return f"This is likely a **{recommendation['task_type']}** problem{detail}. Recommended model: **{recommendation['recommended_model']}**.\n\n{recommendation['explanation']}", {"type": "model_recommendation", **recommendation}, None

    if re.search(r"\b(most|more|best|important|imp)\b.{0,30}\b(column|columns|feature|features)\b", clean) or "feature importance" in clean:
        recommendation = infer_ml_task(frame, Path(file_path).suffix.removeprefix("."))
        features, excluded, method = _important(frame, recommendation)
        if not recommendation.get("target_column"):
            return "Choose the column you want to predict first; then I can rank training features without guessing a target.", {"type": "feature_guidance", **recommendation}, None
        return f"For predicting **{recommendation['target_column']}**, start with: {', '.join(f'**{value}**' for value in features) or 'non-ID feature columns'}. Avoid: {', '.join(f'**{value}**' for value in excluded) or 'no obvious identifier columns'}." + (f" Numeric fields are ranked by {method}." if method else ""), {"type": "feature_guidance", "target_column": recommendation["target_column"], "recommended_features": features}, None

    if re.search(r"\b(first|top)\s+\d+\s+(rows?|records?)\b|sample (?:data|rows?)|preview", clean):
        match = re.search(r"\b(?:first|top)\s+(\d+)", clean)
        size = min(int(match.group(1)) if match else 5, 50)
        return f"First **{size}** rows:\n\n```\n{frame.head(size).fillna('missing').to_string(index=False)}\n```", {"type": "preview", "rows": size, "columns": columns}, None
    if "data type" in clean or "dtypes" in clean or "types of" in clean:
        return "Column data types:\n\n" + "\n".join(f"**{column}**: {frame[column].dtype}" for column in columns), {"type": "dtypes", "columns": columns}, None
    if re.search(r"\b(numerical|numeric) columns?\b", clean):
        return f"Numerical columns: {', '.join(f'**{column}**' for column in numeric) or 'none'}.", {"type": "numeric_columns", "columns": numeric}, None
    if re.search(r"\b(categorical|category|text) columns?\b", clean):
        return f"Categorical/text columns: {', '.join(f'**{column}**' for column in categorical) or 'none'}.", {"type": "categorical_columns", "columns": categorical}, None
    if "column names" in clean or re.search(r"\b(list|what are)\b.*\bcolumns?\b", clean):
        return f"The columns are: {', '.join(f'**{column}**' for column in columns)}.", {"type": "columns", "columns": columns}, None
    if any(term in clean for term in ("overview", "summary", "describe", "what does this dataset contain", "about this dataset", "about the dataset")):
        return _overview(frame, columns), {"type": "profile", "columns": columns}, None
    if "descriptive statistics" in clean or "describe statistics" in clean:
        if not numeric:
            return "There are no numerical columns for descriptive statistics.", {"type": "descriptive_statistics", "columns": []}, None
        stats = frame[numeric].describe().T
        lines = [f"**{column}** — count {_number(row['count'])}, mean {_number(row['mean'])}, median {_number(row['50%'])}, min {_number(row['min'])}, max {_number(row['max'])}" for column, row in stats.head(12).iterrows()]
        return "Descriptive statistics:\n\n" + "\n".join(lines), {"type": "descriptive_statistics", "columns": numeric}, None
    if "missing" in clean:
        present = frame.isna().sum()
        present = present[present > 0]
        return ("No missing values were found." if present.empty else "Missing values: " + "; ".join(f"**{name}**: {int(value):,}" for name, value in present.items())), {"type": "missing_values", "columns": [str(column) for column in present.index]}, None
    if "duplicate" in clean or "repeated" in clean:
        return f"I found **{int(frame.duplicated().sum()):,} duplicate rows**.", {"type": "duplicate_rows"}, None
    if re.search(r"\b(how many|number of|count)\b.*\b(rows|records|samples)\b", clean) and "column" in clean:
        return f"This dataset contains **{len(frame):,} rows** and **{len(columns)} columns**.", {"type": "shape", "rows": len(frame), "columns": len(columns)}, None
    if re.search(r"\b(how many|number of|count)\b.*\b(rows|records|samples)\b", clean):
        return f"This dataset contains **{len(frame):,} rows**.", {"type": "row_count", "value": len(frame)}, None
    if re.search(r"\b(how many|number of|count)\b.*\bcolumns?\b", clean):
        return f"This dataset contains **{len(columns)} columns**.", {"type": "column_count", "value": len(columns)}, None
    if "correlation" in clean or "correlated" in clean:
        content, metadata = _correlations(frame, numeric)
        return content, metadata, None
    if "outlier" in clean or "unusual" in clean:
        findings = []
        for column in numeric:
            values = frame[column].dropna()
            if len(values) >= 4:
                q1, q3 = values.quantile([.25, .75])
                count = int(((values < q1 - 1.5 * (q3 - q1)) | (values > q3 + 1.5 * (q3 - q1))).sum())
                if count: findings.append(f"**{column}**: {count:,}")
        return ("Potential IQR outliers: " + "; ".join(findings) + ".") if findings else "No potential IQR outliers were found.", {"type": "outliers", "columns": numeric}, None
    if "insight" in clean or "key finding" in clean:
        insights = [f"The dataset has **{len(frame):,} rows** across **{len(columns)} columns**."]
        missing = int(frame.isna().sum().sum())
        insights.append("There are **no missing values**." if not missing else f"There are **{missing:,} missing values** to review.")
        if categorical:
            column = categorical[0]
            top = frame[column].value_counts(dropna=False)
            insights.append(f"The most common **{column}** value is **{top.index[0]}** ({int(top.iloc[0]):,} rows).")
        elif numeric:
            column = numeric[0]
            insights.append(f"**{column}** ranges from **{_number(frame[column].min())}** to **{_number(frame[column].max())}**.")
        return "Here are three data-grounded insights:\n\n1. " + "\n2. ".join(insights[:3]), {"type": "insights", "columns": columns}, None

    named_numeric = [column for column in mentioned if column in numeric]
    named_categories = [column for column in mentioned if column in categorical]
    if len(mentioned) >= 2 and named_numeric and named_categories and re.search(r"\btop\s+\d+\b", clean):
        size = min(int(re.search(r"\btop\s+(\d+)", clean).group(1)), 50)
        category, value = named_categories[0], named_numeric[0]
        ranked = frame[[category, value]].dropna(subset=[value]).sort_values(value, ascending=False).head(size)
        rows = "; ".join(f"**{row[category]}**: {_number(row[value])}" for _, row in ranked.iterrows())
        return f"Top **{size}** by **{value}**: {rows}.", {"type": "ranking", "columns": [category, value], "rows": size}, None
    if named_categories and ("percentage" in clean or "percent" in clean):
        category, counts = named_categories[0], frame[named_categories[0]].value_counts(dropna=False)
        result = "; ".join(f"**{index}**: {count / len(frame) * 100:.1f}% ({count:,})" for index, count in counts.head(15).items())
        return f"Percentage of rows by **{category}**: {result}.", {"type": "category_percentages", "columns": [category]}, _distribution_chart(frame, category) if chart_requested else None
    grouped_question = len(mentioned) >= 2 and named_numeric and named_categories and any(term in clean for term in ("highest", "lowest", "compare", "between", "percentage", "percent", "total", "average", "mean", "by"))
    if grouped_question:
        value, category = named_numeric[0], named_categories[0]
        if "percentage" in clean or "percent" in clean:
            counts = frame[category].value_counts(dropna=False)
            result = "; ".join(f"**{index}**: {count / len(frame) * 100:.1f}% ({count:,})" for index, count in counts.head(15).items())
            return f"Percentage of rows by **{category}**: {result}.", {"type": "category_percentages", "columns": [category]}, _distribution_chart(frame, category) if chart_requested else None
        operation = "mean" if "average" in clean or "mean" in clean else "sum"
        grouped = frame.groupby(category, dropna=False)[value].agg(operation).sort_values(ascending="lowest" in clean)
        if "compare" in clean or "between" in clean:
            result = "; ".join(f"**{index}**: {_number(number)}" for index, number in grouped.head(15).items())
            return f"{operation.title()} **{value}** by **{category}**: {result}.", {"type": "group_comparison", "columns": [category, value]}, _group_chart(frame, category, value, operation) if chart_requested else None
        index, result = grouped.index[0], grouped.iloc[0]
        qualifier = "lowest" if "lowest" in clean else "highest"
        return f"**{index}** has the {qualifier} {operation} **{value}**: **{_number(result)}**.", {"type": "group_ranking", "columns": [category, value]}, _group_chart(frame, category, value, operation) if chart_requested else None

    if len(named_numeric) >= 2 and chart_requested:
        x, y = named_numeric[:2]
        figure, axis = plt.subplots(figsize=(7, 4)); axis.scatter(frame[x], frame[y], color="#258c75", alpha=.7); axis.set(xlabel=x, ylabel=y, title=f"{y} vs {x}")
        return f"Here is the relationship between **{x}** and **{y}**.", {"type": "relationship", "columns": [x, y]}, {"type": "scatter", "chart_id": _save_chart(figure)}

    if mentioned:
        column, series = mentioned[0], frame[mentioned[0]]
        if any(term in clean for term in ("unique", "distinct", "different values", "categories")):
            values = series.dropna().unique()
            if "categories" in clean and len(values) <= 30:
                return f"Unique categories in **{column}** ({len(values):,}): " + ", ".join(f"**{value}**" for value in values), {"type": "unique_values", "columns": [column]}, None
            return f"**{column}** has **{len(values):,} distinct non-empty values**.", {"type": "unique_values", "columns": [column]}, None
        if column not in numeric:
            top = series.value_counts(dropna=False)
            return f"The most common **{column}** category is **{top.index[0]}** with **{int(top.iloc[0]):,} rows**.", {"type": "value_counts", "columns": [column]}, _distribution_chart(frame, column) if chart_requested or "distribution" in clean else None
        if "average" in clean or "mean" in clean:
            return f"The average **{column}** is **{_number(series.mean())}**.", {"type": "mean", "columns": [column], "value": float(series.mean())}, None
        if "median" in clean:
            return f"The median **{column}** is **{_number(series.median())}**.", {"type": "median", "columns": [column], "value": float(series.median())}, None
        if "standard deviation" in clean or re.search(r"\bstd\b", clean):
            return f"The standard deviation of **{column}** is **{_number(series.std())}**.", {"type": "std", "columns": [column]}, None
        if "variance" in clean:
            return f"The variance of **{column}** is **{_number(series.var())}**.", {"type": "variance", "columns": [column]}, None
        if "minimum" in clean or re.search(r"\bmin\b", clean):
            return f"The minimum **{column}** is **{_number(series.min())}**.", {"type": "min", "columns": [column]}, None
        if "maximum" in clean or re.search(r"\bmax\b", clean):
            return f"The maximum **{column}** is **{_number(series.max())}**.", {"type": "max", "columns": [column]}, None
        if chart_requested or "distribution" in clean:
            return f"Here is the distribution of **{column}**.", {"type": "distribution", "columns": [column]}, _distribution_chart(frame, column)
        return f"For **{column}**: mean **{_number(series.mean())}**, median **{_number(series.median())}**, minimum **{_number(series.min())}**, maximum **{_number(series.max())}**.", {"type": "statistics", "columns": [column]}, None

    missing = _missing_column(question)
    if missing:
        return f"I couldn't find a **{missing}** column in the uploaded dataset. Available columns are: {', '.join(f'**{column}**' for column in columns)}.", {"type": "unknown_column", "columns": columns}, None
    return _overview(frame, columns) + "\n\nTell me which column or calculation you want to explore.", {"type": "profile", "columns": columns}, None
