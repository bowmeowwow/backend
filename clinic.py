from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Clinic, ClinicPrice
from schemas import ClinicPriceResponse, ClinicResponse

router = APIRouter(prefix="/api/clinics", tags=["clinics"])


@router.get("", response_model=List[ClinicResponse])
def list_clinics(district: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Clinic)
    if district:
        query = query.filter(Clinic.district == district)
    return query.all()


@router.get("/{clinic_id}/prices", response_model=List[ClinicPriceResponse])
def get_clinic_prices(clinic_id: int, db: Session = Depends(get_db)):
    if db.query(Clinic).filter(Clinic.id == clinic_id).first() is None:
        raise HTTPException(status_code=404, detail="병원을 찾을 수 없습니다.")
    return db.query(ClinicPrice).filter(ClinicPrice.clinic_id == clinic_id).all()
