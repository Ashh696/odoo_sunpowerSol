from app.database import Base

# Module A: Authentication, roles and employee management (1-10)
from app.models.auth import (
    Role,
    Permission,
    User,
    RolePermission,
    Department,
    Employee,
    Skill,
    EmployeeSkill,
    FileAttachment,
    EmployeeCertification,
)

# Module B: CRM, enquiries, surveys and quotations (11-19)
from app.models.crm import (
    Customer,
    Enquiry,
    Followup,
    Survey,
    SurveyApproval,
    Quotation,
    Product,
    QuotationItem,
    QuotationRevision,
)

# Module C: Orders, projects, BOM and procurement (20-33)
from app.models.projects import (
    Order,
    Project,
    BomTemplate,
    BomItem,
    ProjectBomItem,
    ProjectNote,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    SupplierInvoice,
    SupplierPayment,
    SupplierPaymentAllocation,
)

# Module D: Inventory, serial numbers and dispatch (34-42)
from app.models.inventory import (
    Inventory,
    StockMovement,
    StockReservation,
    SerialNumber,
    SerialNumberHistory,
    Dispatch,
    DispatchItem,
    DispatchSerial,
    DeliveryConfirmation,
)

# Module E: Installation management (43-51)
from app.models.installations import (
    InstallationSchedule,
    InstallationScheduleTechnician,
    Installation,
    InstallationChecklist,
    InstallationPhoto,
    TechnicianWorklog,
    InstallationTest,
    MaterialConsumption,
    CustomerAcceptance,
)

# Module F: Finance and accounts (52-58)
from app.models.finance import (
    Payment,
    Invoice,
    InvoiceItem,
    PaymentAllocation,
    Expense,
    TechnicianPayment,
    ProjectCost,
)

# Module G: Warranty and service management (59-65)
from app.models.warranty import (
    WarrantyPolicy,
    WarrantyRecord,
    WarrantyEvent,
    ServiceTicket,
    ServiceVisit,
    Replacement,
    ServiceTicketConfirmation,
)

# Module H: Government subsidy management (66-69)
from app.models.subsidy import (
    SubsidyApplication,
    SubsidyDocument,
    SubsidyStatusHistory,
    SubsidyPayment,
)

# Module I: Workflow, tasks and system monitoring (70-75)
from app.models.workflow import (
    Task,
    TaskAssignment,
    TaskHistory,
    Escalation,
    Notification,
    AuditLog,
)

__all__ = [
    "Base",
    # Module A
    "Role",
    "Permission",
    "User",
    "RolePermission",
    "Department",
    "Employee",
    "Skill",
    "EmployeeSkill",
    "FileAttachment",
    "EmployeeCertification",
    # Module B
    "Customer",
    "Enquiry",
    "Followup",
    "Survey",
    "SurveyApproval",
    "Quotation",
    "Product",
    "QuotationItem",
    "QuotationRevision",
    # Module C
    "Order",
    "Project",
    "BomTemplate",
    "BomItem",
    "ProjectBomItem",
    "ProjectNote",
    "Supplier",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "GoodsReceipt",
    "GoodsReceiptItem",
    "SupplierInvoice",
    "SupplierPayment",
    "SupplierPaymentAllocation",
    # Module D
    "Inventory",
    "StockMovement",
    "StockReservation",
    "SerialNumber",
    "SerialNumberHistory",
    "Dispatch",
    "DispatchItem",
    "DispatchSerial",
    "DeliveryConfirmation",
    # Module E
    "InstallationSchedule",
    "InstallationScheduleTechnician",
    "Installation",
    "InstallationChecklist",
    "InstallationPhoto",
    "TechnicianWorklog",
    "InstallationTest",
    "MaterialConsumption",
    "CustomerAcceptance",
    # Module F
    "Payment",
    "Invoice",
    "InvoiceItem",
    "PaymentAllocation",
    "Expense",
    "TechnicianPayment",
    "ProjectCost",
    # Module G
    "WarrantyPolicy",
    "WarrantyRecord",
    "WarrantyEvent",
    "ServiceTicket",
    "ServiceVisit",
    "Replacement",
    "ServiceTicketConfirmation",
    # Module H
    "SubsidyApplication",
    "SubsidyDocument",
    "SubsidyStatusHistory",
    "SubsidyPayment",
    # Module I
    "Task",
    "TaskAssignment",
    "TaskHistory",
    "Escalation",
    "Notification",
    "AuditLog",
]
