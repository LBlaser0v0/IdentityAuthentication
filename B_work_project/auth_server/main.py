from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from auth_server.routes import router

app = FastAPI(title="Authorization Server")
app.mount("/static", StaticFiles(directory="auth_server/static"), name="static")
app.include_router(router)
