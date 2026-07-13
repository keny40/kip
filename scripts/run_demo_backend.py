from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn
from fastapi import Request
from fastapi.responses import JSONResponse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app  # noqa: E402


@app.exception_handler(Exception)
async def safe_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    print("BACKEND_ERROR code=UNEXPECTED_SERVER_ERROR", flush=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        access_log=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
