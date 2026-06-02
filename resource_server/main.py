from fastapi import FastAPI

from resource_server.routes import router

app = FastAPI(title="Resource Server")
app.include_router(router)
