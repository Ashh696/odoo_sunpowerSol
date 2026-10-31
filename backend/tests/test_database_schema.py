import pytest
import psycopg2
from app.config import settings

AGREED_75_TABLES = [
    # A. Authentication, roles and employee management (10)
    "roles",
    "permissions",
    "users",
    "role_permissions",
    "departments",
    "employees",
    "skills",
    "employee_skills",
    "file_attachments",
    "employee_certifications",
    # B. CRM, enquiries, surveys and quotations (9)
    "customers",
    "enquiries",
    "followups",
    "surveys",
    "survey_approvals",
    "quotations",
    "products",
    "quotation_items",
    "quotation_revisions",
    # C. Orders, projects, BOM and procurement (14)
    "orders",
    "projects",
    "bom_templates",
    "bom_items",
    "project_bom_items",
    "project_notes",
    "suppliers",
    "purchase_orders",
    "purchase_order_items",
    "goods_receipts",
    "goods_receipt_items",
    "supplier_invoices",
    "supplier_payments",
    "supplier_payment_allocations",
    # D. Inventory, serial numbers and dispatch (9)
    "inventory",
    "stock_movements",
    "stock_reservations",
    "serial_numbers",
    "serial_number_history",
    "dispatches",
    "dispatch_items",
    "dispatch_serials",
    "delivery_confirmations",
    # E. Installation management (9)
    "installation_schedules",
    "installation_schedule_technicians",
    "installations",
    "installation_checklists",
    "installation_photos",
    "technician_worklogs",
    "installation_tests",
    "material_consumption",
    "customer_acceptances",
    # F. Finance and accounts (7)
    "payments",
    "invoices",
    "invoice_items",
    "payment_allocations",
    "expenses",
    "technician_payments",
    "project_costs",
    # G. Warranty and service management (7)
    "warranty_policies",
    "warranty_records",
    "warranty_events",
    "service_tickets",
    "service_visits",
    "replacements",
    "service_ticket_confirmations",
    # H. Government subsidy management (4)
    "subsidy_applications",
    "subsidy_documents",
    "subsidy_status_history",
    "subsidy_payments",
    # I. Workflow, tasks and system monitoring (6)
    "tasks",
    "task_assignments",
    "task_history",
    "escalations",
    "notifications",
    "audit_logs",
]


def test_database_has_all_75_tables():
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name != 'alembic_version'
        ORDER BY table_name;
        """
    )
    db_tables = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    missing = set(AGREED_75_TABLES) - set(db_tables)
    extra = set(db_tables) - set(AGREED_75_TABLES)

    assert len(db_tables) == 75, f"Expected 75 tables, got {len(db_tables)}. Missing: {missing}, Extra: {extra}"
    assert missing == set(), f"Missing tables: {missing}"
    assert extra == set(), f"Extra tables: {extra}"


def test_database_foreign_keys_and_constraints():
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
    )
    cur = conn.cursor()

    # Foreign Keys count
    cur.execute(
        """
        SELECT count(*)
        FROM information_schema.table_constraints
        WHERE table_schema = 'public' AND constraint_type = 'FOREIGN KEY';
        """
    )
    fk_count = cur.fetchone()[0]
    assert fk_count > 50, f"Expected > 50 foreign keys, got {fk_count}"

    # Check Constraints count
    cur.execute(
        """
        SELECT count(*)
        FROM information_schema.table_constraints
        WHERE table_schema = 'public' AND constraint_type = 'CHECK';
        """
    )
    check_count = cur.fetchone()[0]
    assert check_count > 30, f"Expected > 30 check constraints, got {check_count}"

    # Indexes count
    cur.execute(
        """
        SELECT count(*)
        FROM pg_indexes
        WHERE schemaname = 'public';
        """
    )
    idx_count = cur.fetchone()[0]
    assert idx_count > 100, f"Expected > 100 indexes, got {idx_count}"

    print(f"\n[STATS] Foreign Keys: {fk_count}, Checks: {check_count}, Indexes: {idx_count}")

    cur.close()
    conn.close()
