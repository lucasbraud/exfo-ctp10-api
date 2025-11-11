"""
EXFO CTP10 Vector Analyzer API
FastAPI application providing REST interface for CTP10 control via Pymeasure
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.manager import CTP10Manager
from app.routers import connection, detector, measurement, tls, rlaser, websocket

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup on startup/shutdown"""
    logger.info("Starting EXFO CTP10 API...")
    logger.info(f"CTP10 address: {settings.ctp10_address}")

    # Initialize manager and store in app state
    app.state.ctp10_manager = CTP10Manager(
        address=settings.ctp10_address,
        timeout_ms=settings.CTP10_TIMEOUT_MS
    )
    logger.info("CTP10 manager initialized")

    # Optionally auto-connect to CTP10 on startup
    if settings.AUTO_CONNECT:
        try:
            ctp = app.state.ctp10_manager.connect()
            logger.info(f"Auto-connect successful: {ctp.id}")

            # Set default wavelength on detector module
            try:
                detector = ctp.detector(module=settings.DEFAULT_MODULE, channel=settings.DEFAULT_CHANNEL)
                detector.wavelength_nm = settings.DEFAULT_WAVELENGTH_NM
                logger.info(f"Set default wavelength to {settings.DEFAULT_WAVELENGTH_NM} nm on module {settings.DEFAULT_MODULE}")
            except Exception as e:
                logger.warning(f"Failed to set default wavelength: {e}")

        except Exception as e:
            logger.warning(f"Auto-connect failed: {e}")
            logger.info("API is still running for manual connect")

    yield

    # Cleanup
    logger.info("Shutting down EXFO CTP10 API...")
    if app.state.ctp10_manager.is_connected:
        app.state.ctp10_manager.disconnect()
        logger.info("Disconnected from CTP10")


# Create FastAPI app
app = FastAPI(
    title="EXFO CTP10 Vector Analyzer API",
    description="REST API for EXFO CTP10 vector analyzer control via Pymeasure",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Root Endpoints ==========

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "EXFO CTP10 Vector Analyzer API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    manager = app.state.ctp10_manager
    return {
        "status": "healthy",
        "connected": manager.is_connected,
        "timestamp": datetime.now().isoformat()
    }


# ========== Include Routers ==========

app.include_router(connection.router)
app.include_router(detector.router)
app.include_router(measurement.router)
app.include_router(tls.router)
app.include_router(rlaser.router)
app.include_router(websocket.router)
