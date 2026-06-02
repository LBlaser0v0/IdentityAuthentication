from fastapi import FastAPI

from auth_server.routes import router

app = FastAPI(title="Authorization Server")
app.include_router(router)
