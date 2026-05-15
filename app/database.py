import aiosqlite
import os
from datetime import datetime, UTC

DB_PATH = os.getenv("DB_PATH", "snip.db")

# Shared connection used when DB_PATH is :memory: (tests)
_shared_conn: aiosqlite.Connection | None = None


async def _connect() -> aiosqlite.Connection:
    global _shared_conn
    if DB_PATH == ":memory:":
        if _shared_conn is None:
            _shared_conn = await aiosqlite.connect(":memory:")
        return _shared_conn
    return await aiosqlite.connect(DB_PATH)


async def _maybe_close(conn: aiosqlite.Connection):
    if DB_PATH != ":memory:":
        await conn.close()


async def init_db():
    global _shared_conn
    if DB_PATH == ":memory:":
        if _shared_conn is None:
            _shared_conn = await aiosqlite.connect(":memory:")
        conn = _shared_conn
    else:
        conn = await aiosqlite.connect(DB_PATH)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            code TEXT PRIMARY KEY,
            original_url TEXT NOT NULL,
            created_at TEXT NOT NULL,
            clicks INTEGER DEFAULT 0
        )
    """)
    await conn.commit()

    if DB_PATH != ":memory:":
        await conn.close()


async def save_url(code: str, original_url: str):
    conn = await _connect()
    try:
        await conn.execute(
            "INSERT INTO urls (code, original_url, created_at, clicks) VALUES (?, ?, ?, 0)",
            (code, original_url, datetime.now(UTC).isoformat())
        )
        await conn.commit()
    finally:
        await _maybe_close(conn)


async def code_exists(code: str) -> bool:
    """Check if a code exists WITHOUT incrementing click count."""
    conn = await _connect()
    try:
        async with conn.execute(
            "SELECT 1 FROM urls WHERE code = ?", (code,)
        ) as cursor:
            return await cursor.fetchone() is not None
    finally:
        await _maybe_close(conn)


async def get_url(code: str) -> str | None:
    """Fetch original URL and increment click counter."""
    conn = await _connect()
    try:
        async with conn.execute(
            "SELECT original_url FROM urls WHERE code = ?", (code,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                await conn.execute(
                    "UPDATE urls SET clicks = clicks + 1 WHERE code = ?", (code,)
                )
                await conn.commit()
                return row[0]
    finally:
        await _maybe_close(conn)
    return None


async def get_stats(code: str) -> dict | None:
    conn = await _connect()
    try:
        async with conn.execute(
            "SELECT code, original_url, created_at, clicks FROM urls WHERE code = ?",
            (code,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "code": row[0],
                    "original_url": row[1],
                    "created_at": row[2],
                    "clicks": row[3],
                }
    finally:
        await _maybe_close(conn)
    return None