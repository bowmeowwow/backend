from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import router as auth_router
from chat import router as chat_router
from clinic import router as clinic_router
from database import SessionLocal
from insurance import router as insurance_router
from models import NewsArticle
from news import refresh_news
from news import router as news_router
from pets import router as pets_router
from schedules import router as schedules_router
from seed import seed_mock_clinics, seed_mock_insurance, seed_test_user

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


def _refresh_news_job() -> None:
    db = SessionLocal()
    try:
        refresh_news(db)
    finally:
        db.close()

app = FastAPI(title="Bow-Meow-Wow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    field = ".".join(str(loc) for loc in first_error["loc"] if loc != "body")
    return JSONResponse(status_code=422, content={"message": f"{field}: {first_error['msg']}"})


@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        seed_test_user(db)
        seed_mock_clinics(db)
        seed_mock_insurance(db)
        if db.query(NewsArticle).first() is None:
            try:
                refresh_news(db)
            except Exception:
                pass  # best-effort; the daily cron job will retry
    finally:
        db.close()

    if not scheduler.running:
        scheduler.add_job(_refresh_news_job, CronTrigger(hour=0, minute=0), id="refresh_news", replace_existing=True)
        scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)


app.include_router(auth_router)
app.include_router(pets_router)
app.include_router(clinic_router)
app.include_router(insurance_router)
app.include_router(chat_router)
app.include_router(schedules_router)
app.include_router(news_router)


@app.get("/health")
def health():
    return {"status": "ok"}
