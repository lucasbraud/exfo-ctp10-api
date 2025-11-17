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
from app.factory import create_ctp10_manager
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

    # Create manager (real or mock based on MOCK_MODE setting)
    app.state.ctp10_manager = create_ctp10_manager()

    # Auto-connect only if NOT in mock mode (mock is already "connected")
    if settings.AUTO_CONNECT and not settings.MOCK_MODE:
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
    if app.state.ctp10_manager.is_connected and not settings.MOCK_MODE:
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
