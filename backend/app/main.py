from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import (
    health_router,
    auth_router,
    department_router,
    skill_router,
    certification_router,
    employee_router,
    customer_router,
    enquiry_router,
    followup_router,
    crm_router,
    survey_router,
    product_router,
    bom_router,
    quotation_router,
    order_router,
    project_router,
    finance_router,
    analytics_router,
    procurement_router,
    dispatch_router,
    installation_router,
    supplier_finance_router,
    warranty_router,
    subsidy_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    # Shutdown actions


app = FastAPI(
    title=settings.APP_NAME,
    description="Solar Installation Management System (SIMS) for SunPower Solutions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local uploads directory for file serving
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(health_router)  # Also expose /health at root for quick checks
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(department_router, prefix=settings.API_V1_STR)
app.include_router(skill_router, prefix=settings.API_V1_STR)
app.include_router(certification_router, prefix=settings.API_V1_STR)
app.include_router(employee_router, prefix=settings.API_V1_STR)
app.include_router(customer_router, prefix=settings.API_V1_STR)
app.include_router(enquiry_router, prefix=settings.API_V1_STR)
app.include_router(followup_router, prefix=settings.API_V1_STR)
app.include_router(crm_router, prefix=settings.API_V1_STR)
app.include_router(survey_router, prefix=settings.API_V1_STR)
app.include_router(product_router, prefix=settings.API_V1_STR)
app.include_router(bom_router, prefix=settings.API_V1_STR)
app.include_router(quotation_router, prefix=settings.API_V1_STR)
app.include_router(order_router, prefix=settings.API_V1_STR)
app.include_router(project_router, prefix=settings.API_V1_STR)
app.include_router(finance_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(procurement_router, prefix=settings.API_V1_STR)
app.include_router(dispatch_router, prefix=settings.API_V1_STR)
app.include_router(installation_router, prefix=settings.API_V1_STR)
app.include_router(supplier_finance_router, prefix=settings.API_V1_STR)
app.include_router(warranty_router, prefix=settings.API_V1_STR)
app.include_router(subsidy_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred.",
        },
    )
