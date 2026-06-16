from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from client_app.routes import router

app = FastAPI(title="Client App")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.mount("/static", StaticFiles(directory="client_app/static"), name="static")
app.include_router(router)
