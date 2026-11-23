from fastapi import FastAPI

app = FastAPI(
    title="Bible Study AI",
    description="An offline-first AI-powered Bible study companion",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}