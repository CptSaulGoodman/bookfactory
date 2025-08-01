# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.routers import views, ai

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(views.router)
app.include_router(ai.router)