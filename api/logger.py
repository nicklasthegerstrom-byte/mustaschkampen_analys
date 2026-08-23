import os
import asyncio
from datetime import datetime, timezone


# Sätt DATABASE_URL i Render environment variables:
# postgresql://user:password@host/dbname
DATABASE_URL = os.environ.get("DATABASE_URL")

_pool = None


async def get_pool():
    global _pool
    if _pool is None and DATABASE_URL:
        try:
            import asyncpg
            _pool = await asyncpg.create_pool(DATABASE_URL)
            await _ensure_table(_pool)
        except Exception as e:
            print(f"[LOGGER] Kunde inte ansluta till databasen: {e}", flush=True)
    return _pool


async def _ensure_table(pool):
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS mustasch_log (
            id          SERIAL PRIMARY KEY,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            event       TEXT NOT NULL,
            score       FLOAT,
            error_msg   TEXT
        )
    """)


async def log_analysis(score: float):
    await _write("analysis", score=score)


async def log_error(event: str, error_msg: str):
    await _write(event, error_msg=error_msg)


async def _write(event: str, score: float = None, error_msg: str = None):
    pool = await get_pool()
    if pool is None:
        return
    try:
        await pool.execute(
            "INSERT INTO mustasch_log (event, score, error_msg) VALUES ($1, $2, $3)",
            event, score, error_msg
        )
    except Exception as e:
        print(f"[LOGGER] Kunde inte skriva till databasen: {e}", flush=True)
