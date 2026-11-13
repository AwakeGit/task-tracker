from fastapi import FastAPI

from .routers import analytics, auth, tasks

app = FastAPI(title="Task Tracker")

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}
