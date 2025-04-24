from fastapi import FastAPI, HTTPException
from app.api.router import api_router

from app.core.event_handlers import lifespan
from app.core.cors_middleware import add_cors_middleware
from app.settings import APISettings


def get_app() -> FastAPI:
    fast_app = FastAPI(title=APISettings().APP_NAME, version=APISettings().APP_VERSION, debug=APISettings().IS_DEBUG, 
                       lifespan=lifespan
                       )
    add_cors_middleware(fast_app)
    fast_app.include_router(api_router, prefix=APISettings().API_PREFIX)

    return fast_app

app = get_app()