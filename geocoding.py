import os
from typing import Optional, Tuple

import requests

KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    api_key = os.getenv("KAKAO_REST_API_KEY")
    if not api_key or not address:
        return None

    try:
        response = requests.get(
            KAKAO_GEOCODE_URL,
            params={"query": address},
            headers={"Authorization": f"KakaoAK {api_key}"},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return None

    documents = response.json().get("documents") or []
    if not documents:
        return None

    doc = documents[0]
    return float(doc["y"]), float(doc["x"])
