from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Dataset

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".txt", ".json", ".jsonl", ".zip"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
TARGET_HINTS = ("target", "label", "class", "outcome", "response", "result", "status", "churn", "default", "fraud", "diagnosis", "y")


def read_dataframe(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    try:
        suffix = source.suffix.lower()
        if suffix == ".csv":
            frame = pd.read_csv(source)
        elif suffix in {".xlsx", ".xls"}:
            frame = pd.read_excel(source)
        elif suffix == ".txt":
            frame = pd.DataFrame({"text": source.read_text(encoding="utf-8", errors="replace").splitlines()})
        elif suffix in {".json", ".jsonl"}:
            frame = pd.read_json(source, lines=suffix == ".jsonl")
        elif suffix == ".zip":
            with ZipFile(source) as archive:
                images = [entry for entry in archive.infolist() if not entry.is_dir() and Path(entry.filename).suffix.lower() in IMAGE_EXTENSIONS]
                frame = pd.DataFrame([{"image": Path(entry.filename).name, "format": Path(entry.filename).suffix.lower().removeprefix("."), "file_size_bytes": entry.file_size} for entry in images])
        else:
            raise ValueError("Unsupported dataset type")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file could not be read as a dataset. For CV uploads, use a ZIP containing image files.") from exc
    if frame.empty or not len(frame.columns):
        raise HTTPException(status_code=400, detail="The dataset must contain at least one row and one column.")
    return frame


async def save_upload(upload: UploadFile, db: Session) -> Dataset:
    original_name = Path(upload.filename or "dataset").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Supported files: CSV, XLSX, XLS, TXT, JSON, JSONL, and ZIP image datasets.")

    settings.dataset_storage_path.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = settings.dataset_storage_path / stored_name
    size = 0
    with stored_path.open("wb") as destination:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_size:
                destination.close()
                stored_path.unlink(missing_ok=True)
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The uploaded file is too large.")
            destination.write(chunk)
    if not size:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    try:
        frame = read_dataframe(stored_path)
    except Exception:
        stored_path.unlink(missing_ok=True)
        raise

    now = datetime.utcnow()
    dataset = Dataset(
        original_filename=original_name,
        stored_filename=stored_name,
        file_path=str(stored_path),
        file_type=suffix.removeprefix("."),
        file_size=size,
        row_count=len(frame),
        column_count=len(frame.columns),
        uploaded_at=now,
        expires_at=now + timedelta(hours=settings.default_data_ttl_hours),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset(db: Session, dataset_id: str) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


def infer_ml_task(frame: pd.DataFrame, file_type: str = "") -> dict:
    """Infer a likely learning task without pretending an arbitrary column is a target."""
    if file_type.lower() == "zip" and "image" in frame.columns:
        return {
            "task_type": "Computer vision dataset",
            "target_column": None,
            "confidence": "needs labels",
            "explanation": "This ZIP contains image metadata. Add a label column or folder-per-class labels to train a supervised vision model.",
            "recommended_model": "Transfer learning with EfficientNet-B0 or ResNet-50",
            "model_architecture": "image → resize/normalize → pretrained CNN backbone → global average pooling → dropout → dense output layer",
        }

    named_columns = [column for column in frame.columns if str(column).strip().lower() in TARGET_HINTS or any(hint in str(column).strip().lower() for hint in TARGET_HINTS if len(hint) > 1)]
    # A target-like name is required: guessing that a random low-cardinality field is
    # the label creates misleading model advice.
    if not named_columns:
        modality = "NLP text dataset" if "text" in frame.columns and len(frame.columns) == 1 else "Tabular exploratory dataset"
        return {
            "task_type": modality,
            "target_column": None,
            "confidence": "needs target selection",
            "explanation": "No target/label column was detected. Choose the column you want to predict to set up supervised training.",
            "recommended_model": "PCA + clustering for exploration; choose a target for supervised learning",
            "model_architecture": "clean features → encode/scale → optional PCA → clustering or dimensionality reduction",
        }

    target = named_columns[0]
    series = frame[target].dropna()
    unique = int(series.nunique())
    is_numeric = pd.api.types.is_numeric_dtype(series)
    classification = (not is_numeric) or unique <= max(20, int(len(series) * 0.05))
    if classification:
        classes = max(unique, 2)
        return {
            "task_type": "Classification",
            "target_column": str(target),
            "confidence": "high" if unique >= 2 else "needs validation",
            "explanation": f"'{target}' has {unique} distinct target value{'s' if unique != 1 else ''}, so the likely goal is assigning one of {classes} classes.",
            "recommended_model": "CatBoost or Random Forest classifier",
            "model_architecture": "features → imputation → categorical encoding → CatBoost/Random Forest → class probability output",
        }
    return {
        "task_type": "Regression",
        "target_column": str(target),
        "confidence": "high",
        "explanation": f"'{target}' is numeric with {unique} distinct values, so the likely goal is predicting a continuous value.",
        "recommended_model": "CatBoost Regressor or Gradient Boosting Regressor",
        "model_architecture": "features → imputation → categorical encoding → gradient-boosted trees → one continuous prediction",
    }


def profile_dataset(dataset: Dataset) -> dict:
    frame = read_dataframe(dataset.file_path)
    columns = [
        {"name": str(column), "dtype": str(frame[column].dtype), "missing": int(frame[column].isna().sum()), "unique": int(frame[column].nunique(dropna=True))}
        for column in frame.columns
    ]
    numeric = frame.select_dtypes(include="number")
    numeric_summary = {
        str(column): {key: (None if pd.isna(value) else round(float(value), 4)) for key, value in values.items()}
        for column, values in numeric.describe().to_dict().items()
    }
    suggestions = ["Give me a dataset overview", "Find missing values"]
    if len(numeric.columns):
        first_numeric = str(numeric.columns[0])
        suggestions.extend([f"What is the average {first_numeric}?", f"Show the distribution of {first_numeric}"])
    category_columns = frame.select_dtypes(exclude="number").columns
    if len(category_columns):
        suggestions.append(f"What are the top values in {category_columns[0]}?")
    return {
        "columns": columns,
        "missing_values": int(frame.isna().sum().sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
        "numeric_summary": numeric_summary,
        "suggestions": suggestions[:5],
        "ml_profile": infer_ml_task(frame, dataset.file_type),
    }
