from fastapi import FastAPI
from src.auth.router import router as auth_router
import src.models

app = FastAPI()

app.include_router(auth_router)