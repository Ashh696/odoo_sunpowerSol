class SystemRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    DIRECTOR = "DIRECTOR"
    SALES = "SALES"
    TECHNICAL_MANAGER = "TECHNICAL_MANAGER"
    WAREHOUSE_PROCUREMENT = "WAREHOUSE_PROCUREMENT"
    FIELD_TECHNICIAN = "FIELD_TECHNICIAN"
    SERVICE_WARRANTY = "SERVICE_WARRANTY"
    FINANCE_ACCOUNTS = "FINANCE_ACCOUNTS"
    CUSTOMER = "CUSTOMER"

    ALL_ROLES = [
        SUPER_ADMIN,
        DIRECTOR,
        SALES,
        TECHNICAL_MANAGER,
        WAREHOUSE_PROCUREMENT,
        FIELD_TECHNICIAN,
        SERVICE_WARRANTY,
        FINANCE_ACCOUNTS,
        CUSTOMER,
    ]


ROLE_METADATA = {
    SystemRole.SUPER_ADMIN: {
        "name": "Super Admin",
        "description": "Full administrative control across the entire solar management system.",
    },
    SystemRole.DIRECTOR: {
        "name": "Director",
        "description": "Executive dashboard, high-level business analytics, approvals, and revenue reporting.",
    },
    SystemRole.SALES: {
        "name": "Sales Executive",
        "description": "Customer leads, enquiries, site survey coordination, and proposal/quotation generation.",
    },
    SystemRole.TECHNICAL_MANAGER: {
        "name": "Technical / Installation Manager",
        "description": "Engineering feasibility, survey approvals, BOM management, project planning, and work orders.",
    },
    SystemRole.WAREHOUSE_PROCUREMENT: {
        "name": "Warehouse & Procurement Manager",
        "description": "Inventory stock, supplier purchase orders, serial number allocation, and dispatch gate passes.",
    },
    SystemRole.FIELD_TECHNICIAN: {
        "name": "Field Technician",
        "description": "Site surveys, physical rooftop installation, electrical testing, and commission checklists.",
    },
    SystemRole.SERVICE_WARRANTY: {
        "name": "Service & Warranty Executive",
        "description": "Post-installation warranty records, service maintenance tickets, and component replacements.",
    },
    SystemRole.FINANCE_ACCOUNTS: {
        "name": "Finance & Accounts Manager",
        "description": "Milestone customer invoicing, payment receipts, expense approvals, and subsidy disbursements.",
    },
    SystemRole.CUSTOMER: {
        "name": "Customer",
        "description": "Self-service portal for tracking rooftop project status, quotations, invoices, and warranties.",
    },
}
