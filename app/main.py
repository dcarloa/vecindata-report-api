from fastapi import FastAPI

app = FastAPI(title="VecinData Report API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
