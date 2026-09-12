"""One-off data import: pulls real Seoul vet/hotel/grooming places from the
Kakao keyword search API and upserts them into the clinics table.

Not run automatically on app startup (unlike seed.py) - this hits a real
external API and is meant to be run manually/periodically:

    python import_clinics.py [pages_per_query]
"""
import os
import sys
import time

import requests
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Clinic, ClinicCategory

SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
]

CATEGORY_KEYWORDS = {
    ClinicCategory.VET: "동물병원",
    ClinicCategory.HOTEL: "애견호텔",
    ClinicCategory.GROOMING: "애견미용실",
}

KAKAO_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


def search_places(query: str, api_key: str, page: int) -> dict:
    response = requests.get(
        KAKAO_KEYWORD_URL,
        params={"query": query, "page": page, "size": 15},
        headers={"Authorization": f"KakaoAK {api_key}"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def import_clinics(pages_per_query: int = 1) -> None:
    api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key:
        raise SystemExit("KAKAO_REST_API_KEY 환경변수가 필요합니다.")

    db: Session = SessionLocal()
    inserted = updated = 0
    try:
        for district in SEOUL_DISTRICTS:
            for category, keyword in CATEGORY_KEYWORDS.items():
                query = f"서울 {district} {keyword}"
                for page in range(1, pages_per_query + 1):
                    data = search_places(query, api_key, page)
                    documents = data.get("documents", [])
                    for doc in documents:
                        external_id = doc["id"]
                        address = doc.get("road_address_name") or doc.get("address_name")
                        existing = db.query(Clinic).filter(Clinic.external_id == external_id).first()
                        if existing:
                            existing.name = doc["place_name"]
                            existing.category = category
                            existing.district = district
                            existing.address = address
                            existing.phone = doc.get("phone") or ""
                            existing.latitude = float(doc["y"])
                            existing.longitude = float(doc["x"])
                            updated += 1
                        else:
                            db.add(
                                Clinic(
                                    external_id=external_id,
                                    name=doc["place_name"],
                                    category=category,
                                    district=district,
                                    address=address,
                                    phone=doc.get("phone") or "",
                                    latitude=float(doc["y"]),
                                    longitude=float(doc["x"]),
                                )
                            )
                            inserted += 1
                    db.commit()
                    print(f"{query} page {page}: {len(documents)} results")
                    if data.get("meta", {}).get("is_end", True):
                        break
                    time.sleep(0.2)
        print(f"done: inserted={inserted}, updated={updated}")
    finally:
        db.close()


if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    import_clinics(pages_per_query=pages)
