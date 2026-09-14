from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Dataset

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def read_dataframe(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    try:
        frame = pd.read_csv(source) if source.suffix.lower() == ".csv" else pd.read_excel(source)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file could not be read as a dataset.") from exc
    if frame.empty or not len(frame.columns):
        raise HTTPException(status_code=400, detail="The dataset must contain at least one row and one column.")
    return frame


async def save_upload(upload: UploadFile, db: Session) -> Dataset:
    original_name = Path(upload.filename or "dataset").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only CSV, XLSX, and XLS files are supported.")

    contents = await upload.read()
    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(contents) > settings.max_upload_size:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="The uploaded file is too large.")

    settings.dataset_storage_path.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = settings.dataset_storage_path / stored_name
    stored_path.write_bytes(contents)
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
        file_size=len(contents),
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
    }
