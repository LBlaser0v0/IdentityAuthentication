from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from client_app.routes import router

app = FastAPI(title="Client App")
app.mount("/static", StaticFiles(directory="client_app/static"), name="static")
app.include_router(router)
