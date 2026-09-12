from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import router as auth_router
from chat import router as chat_router
from clinic import router as clinic_router
from database import Base, SessionLocal, engine
from insurance import router as insurance_router
from pets import router as pets_router
from schedules import router as schedules_router
from seed import seed_mock_clinics, seed_mock_insurance, seed_test_user

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
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_test_user(db)
        seed_mock_clinics(db)
        seed_mock_insurance(db)
    finally:
        db.close()


app.include_router(auth_router)
app.include_router(pets_router)
app.include_router(clinic_router)
app.include_router(insurance_router)
app.include_router(chat_router)
app.include_router(schedules_router)


@app.get("/health")
def health():
    return {"status": "ok"}
