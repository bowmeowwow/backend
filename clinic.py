from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Clinic, ClinicCategory
from schemas import ClinicResponse

router = APIRouter(prefix="/api/clinics", tags=["clinics"])


@router.get("", response_model=List[ClinicResponse])
def list_clinics(
    district: Optional[str] = Query(None),
    category: Optional[ClinicCategory] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Clinic)
    if district:
        query = query.filter(Clinic.district == district)
    if category:
        query = query.filter(Clinic.category == category)
    return query.all()
