"""Pet news: GET /api/news is backed by real Google News RSS results only.

Deliberately not using an LLM to generate article text/URLs - a model asked
for "10 pet news articles" can hallucinate plausible-looking but nonexistent
articles/sources/links, which is unacceptable for something rendered as
real news. refresh_news() pulls real entries from Google News RSS (no API
key required) and upserts them; GET /api/news only ever serves what's
actually in that cache, so a refresh failure just means "no new articles
today," never a fabricated one.
"""
import hashlib
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import List
from xml.etree import ElementTree

import requests
from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import NewsArticle
from schemas import NewsArticleResponse

router = APIRouter(prefix="/api/news", tags=["news"])

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
SEARCH_QUERY = "반려동물 OR 반려견 OR 반려묘"
MAX_ARTICLES = 10


def _to_response(article: NewsArticle) -> NewsArticleResponse:
    # MySQL's DATETIME column drops tzinfo on round-trip; every value written
    # here is UTC (see refresh_news), so it's safe to reattach on the way out.
    published_at = article.published_at.replace(tzinfo=timezone.utc) if article.published_at else None
    return NewsArticleResponse(
        id=article.id,
        title=article.title,
        summary=article.summary,
        source=article.source,
        url=article.url,
        publishedAt=published_at,
    )


@router.get("", response_model=List[NewsArticleResponse])
def list_news(db: Session = Depends(get_db)):
    articles = (
        db.query(NewsArticle)
        .order_by(desc(NewsArticle.published_at), desc(NewsArticle.id))
        .limit(MAX_ARTICLES)
        .all()
    )
    return [_to_response(article) for article in articles]


def refresh_news(db: Session) -> int:
    response = requests.get(
        GOOGLE_NEWS_RSS_URL,
        params={"q": SEARCH_QUERY, "hl": "ko", "gl": "KR", "ceid": "KR:ko"},
        timeout=10,
    )
    response.raise_for_status()

    root = ElementTree.fromstring(response.content)
    items = root.findall("./channel/item")[:MAX_ARTICLES]

    inserted = 0
    for item in items:
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        if not link or not title:
            continue

        external_id = hashlib.sha256(link.encode("utf-8")).hexdigest()
        if db.query(NewsArticle).filter(NewsArticle.external_id == external_id).first():
            continue

        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else None

        published_at = None
        pub_date_text = item.findtext("pubDate")
        if pub_date_text:
            try:
                parsed = parsedate_to_datetime(pub_date_text)
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone(timezone.utc)
                published_at = parsed.replace(tzinfo=None)
            except (TypeError, ValueError):
                published_at = None

        db.add(
            NewsArticle(
                external_id=external_id,
                title=title,
                source=source,
                url=link,
                published_at=published_at,
            )
        )
        inserted += 1

    db.commit()
    return inserted


if __name__ == "__main__":
    session = SessionLocal()
    try:
        count = refresh_news(session)
        print(f"inserted {count} new articles")
    finally:
        session.close()
