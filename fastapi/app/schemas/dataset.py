from datetime import datetime

from pydantic import BaseModel


class DatasetSummary(BaseModel):
    id: str
    original_filename: str
    file_type: str
    file_size: int
    row_count: int
    column_count: int
    uploaded_at: datetime
    expires_at: datetime


class DatasetProfile(DatasetSummary):
    columns: list[dict]
    missing_values: int
    duplicate_rows: int
    numeric_summary: dict[str, dict]
    suggestions: list[str]
