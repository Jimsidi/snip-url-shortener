from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, UTC
import string, random, os
from .database import init_db, save_url, get_url, get_stats, code_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Snip — URL Shortener", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class ShortenRequest(BaseModel):
    url: str
    custom_code: str | None = None


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str
    created_at: str


def generate_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html", "r") as f:
        return f.read()


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@app.post("/api/shorten", response_model=ShortenResponse)
async def shorten_url(request: Request, body: ShortenRequest):
    code = body.custom_code if body.custom_code else generate_code()

    if body.custom_code:
        if len(body.custom_code) < 3 or len(body.custom_code) > 20:
            raise HTTPException(status_code=400, detail="Custom code must be 3-20 characters.")
        existing = await code_exists(code)
        if existing:
            raise HTTPException(status_code=409, detail="That custom code is already taken.")

    base = str(request.base_url).rstrip("/")
    await save_url(code, body.url)

    return ShortenResponse(
        short_code=code,
        short_url=f"{base}/{code}",
        original_url=body.url,
        created_at=datetime.now(UTC).isoformat(),
    )


@app.get("/api/stats/{code}")
async def url_stats(code: str):
    data = await get_stats(code)
    if not data:
        raise HTTPException(status_code=404, detail="Short code not found.")
    return data


@app.get("/{code}")
async def redirect(code: str):
    url = await get_url(code)
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found.")
    return RedirectResponse(url=url, status_code=307)