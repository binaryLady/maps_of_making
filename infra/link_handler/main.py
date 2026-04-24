from fastapi import FastAPI, HTTPException

app = FastAPI(title="Maps of Making Link Handler")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/claim/{token}")
async def claim_link(token: str):
    raise HTTPException(status_code=422, detail="Not implemented yet")
