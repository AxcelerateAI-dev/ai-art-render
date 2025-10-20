from fastapi import FastAPI
from loguru import logger
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context for the FastAPI app to manage startup and shutdown tasks.
    """
    logger.add("logs.log", rotation="10 MB", level="INFO")
    
    yield

    logger.info("Shutting down FastAPI app...")
