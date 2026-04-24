import logging
import re

from fastapi import FastAPI, HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maps of Making Link Handler")

_TOKEN_RE = re.compile(r'^[A-Za-z0-9_\-]{8,255}$')


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/claim/{token}")
async def claim_link(token: str):
    if not _TOKEN_RE.match(token):
        logger.warning("claim attempt rejected — invalid token format: %.40s", token)
        raise HTTPException(status_code=400, detail="Invalid token format")
    logger.info("claim attempt: %s", token)
    raise HTTPException(status_code=422, detail="Not implemented yet")
