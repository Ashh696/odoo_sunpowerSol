from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.departments import router as department_router
from app.routers.skills import router as skill_router
from app.routers.certifications import router as certification_router
from app.routers.employees import router as employee_router

__all__ = [
    "health_router",
    "auth_router",
    "department_router",
    "skill_router",
    "certification_router",
    "employee_router",
]

