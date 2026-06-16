from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from resource_server.routes import router

app = FastAPI(title="Resource Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(router)
