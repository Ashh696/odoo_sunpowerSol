from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine
from app.config import settings
from app.schemas import APIResponse, HealthResponse, DatabaseHealth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=APIResponse[HealthResponse])
def get_health():
    """
    Health check endpoint returning application status and database connectivity.
    """
    db_connected = False
    db_detail = "Connected"
    dialect = engine.name

    try:
        # Ping the database directly
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}")
        db_detail = f"Database ping failed: {str(e)}"

    health_data = HealthResponse(
        app_name=settings.APP_NAME,
        status="ok" if db_connected else "degraded",
        environment=settings.APP_ENV,
        database=DatabaseHealth(
            connected=db_connected,
            dialect=dialect,
            detail=db_detail,
        ),
    )

    return APIResponse(
        success=True,
        message="Service health status",
        data=health_data,
    )
