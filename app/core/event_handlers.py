from fastapi import FastAPI, HTTPException, status
from loguru import logger
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context for the FastAPI app to manage startup and shutdown tasks.
    """
    # Configure logging
    logger.add("logs.log", rotation="1 MB", level="INFO")

    yield  # Yield control back to the application

    logger.info("Shutting down FastAPI app...")