from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.models import Dataset


def remove_expired_data(db: Session) -> int:
    expired = db.query(Dataset).filter(Dataset.expires_at <= datetime.utcnow()).all()
    for dataset in expired:
        Path(dataset.file_path).unlink(missing_ok=True)
        db.delete(dataset)
    db.commit()
    return len(expired)
