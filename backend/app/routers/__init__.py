from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.departments import router as department_router
from app.routers.skills import router as skill_router
from app.routers.certifications import router as certification_router
from app.routers.employees import router as employee_router
from app.routers.customers import router as customer_router
from app.routers.enquiries import router as enquiry_router
from app.routers.followups import router as followup_router
from app.routers.crm_dashboard import router as crm_router
from app.routers.surveys import router as survey_router
from app.routers.products import router as product_router
from app.routers.bom import router as bom_router
from app.routers.quotations import router as quotation_router
from app.routers.orders import router as order_router
from app.routers.projects import router as project_router
from app.routers.finance import router as finance_router
from app.routers.analytics import router as analytics_router
from app.routers.procurement import router as procurement_router
from app.routers.dispatch import router as dispatch_router
from app.routers.installations import router as installation_router
from app.routers.supplier_finance import router as supplier_finance_router
from app.routers.warranty import router as warranty_router
from app.routers.subsidy import router as subsidy_router

__all__ = [
    "health_router",
    "auth_router",
    "department_router",
    "skill_router",
    "certification_router",
    "employee_router",
    "customer_router",
    "enquiry_router",
    "followup_router",
    "crm_router",
    "survey_router",
    "product_router",
    "bom_router",
    "quotation_router",
    "order_router",
    "project_router",
    "finance_router",
    "analytics_router",
    "procurement_router",
    "dispatch_router",
    "installation_router",
    "supplier_finance_router",
    "warranty_router",
    "subsidy_router",
]
