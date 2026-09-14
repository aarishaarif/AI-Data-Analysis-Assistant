from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dataset import DatasetProfile, DatasetSummary
from app.services.dataset_service import get_dataset, profile_dataset, save_upload

router = APIRouter(prefix="/datasets", tags=["datasets"])


def summary(dataset) -> dict:
    return {key: getattr(dataset, key) for key in ("id", "original_filename", "file_type", "file_size", "row_count", "column_count", "uploaded_at", "expires_at")}


@router.post("/upload", response_model=DatasetSummary, status_code=201)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return summary(await save_upload(file, db))


@router.get("/{dataset_id}", response_model=DatasetSummary)
def dataset(dataset_id: str, db: Session = Depends(get_db)):
    return summary(get_dataset(db, dataset_id))


@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
def profile(dataset_id: str, db: Session = Depends(get_db)):
    found = get_dataset(db, dataset_id)
    return summary(found) | profile_dataset(found)
