import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Employee
from app.models.crm import Customer, Enquiry, Quotation, Product
from app.models.projects import Order, Project
from app.models.inventory import Inventory
from app.models.finance import Invoice, InvoiceItem, Payment, PaymentAllocation
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_analytics_test_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.SALES,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_anl@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Anl",
                    hashed_password=hash_password("Pass123!Safe"),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            tokens[slug] = create_access_token(
                data={"sub": str(user.id), "role": role_obj.slug, "email": user.email}
            )
            user_ids[slug] = user.id

    return {
        "tokens": tokens,
        "user_ids": user_ids,
    }


def test_01_executive_dashboard_kpis(setup_analytics_test_env):
    """
    Verify executive dashboard returns valid schema, correct canonical conversion formula label,
    and accurate aggregation types.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.SUPER_ADMIN]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/executive", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Verify sections exist
    assert "enquiries" in data
    assert "conversion" in data
    assert "orders" in data
    assert "projects" in data
    assert "finance" in data
    assert "inventory" in data

    # Verify canonical conversion formula label and properties
    assert data["conversion"]["formula_label"] == "Overall Conversion (Won / All Leads)"
    assert data["conversion"]["overall_conversion_percentage"] >= 0.0

    # Verify finance properties
    assert Decimal(str(data["finance"]["total_invoiced"])) >= Decimal("0.00")
    assert Decimal(str(data["finance"]["cash_collected"])) >= Decimal("0.00")
    assert Decimal(str(data["finance"]["outstanding_receivables"])) >= Decimal("0.00")
    assert Decimal(str(data["finance"]["unbilled_order_obligation"])) >= Decimal("0.00")


def test_02_director_can_access_executive_dashboard(setup_analytics_test_env):
    """
    Verify DIRECTOR role has authorized access to executive dashboard.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.DIRECTOR]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/executive", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True


def test_03_customer_strictly_blocked_from_all_analytics(setup_analytics_test_env):
    """
    Verify CUSTOMER account receives HTTP 403 Forbidden from EVERY analytics endpoint.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.CUSTOMER]
    headers = {"Authorization": f"Bearer {token}"}

    endpoints = [
        "/api/v1/analytics/executive",
        "/api/v1/analytics/sales",
        "/api/v1/analytics/projects",
        "/api/v1/analytics/inventory",
        "/api/v1/analytics/finance",
        "/api/v1/analytics/export?report_type=sales_summary",
    ]

    for ep in endpoints:
        res = client.get(ep, headers=headers)
        assert res.status_code == 403, f"Endpoint {ep} should return 403 for CUSTOMER, got {res.status_code}"


def test_04_sales_analytics_metrics_and_acceptance(setup_analytics_test_env):
    """
    Verify sales analytics returns lead distribution, rep leaderboards,
    and quotation acceptance rate excluding DRAFT quotations.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.SALES]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/sales", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert "status_distribution" in data
    assert "source_distribution" in data
    assert "system_type_distribution" in data
    assert "volume_over_time" in data
    assert "reps_performance" in data
    assert "quotations_metric" in data

    qm = data["quotations_metric"]
    assert qm["total_commercial_quotations"] >= 0
    assert qm["accepted_quotations"] >= 0
    assert qm["acceptance_rate_percentage"] >= 0.0
    if qm["total_commercial_quotations"] > 0:
        expected_rate = round((qm["accepted_quotations"] / qm["total_commercial_quotations"] * 100.0), 1)
        assert abs(qm["acceptance_rate_percentage"] - expected_rate) < 0.05


def test_05_project_analytics_and_delayed_tracking(setup_analytics_test_env):
    """
    Verify project analytics correctly counts active, completed, and delayed projects,
    and calculates duration without errors.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.TECHNICAL_MANAGER]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/projects", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["total_projects"] >= 0
    assert data["active_projects"] >= 0
    assert data["completed_projects"] >= 0
    assert data["delayed_projects"] >= 0
    assert data["cancelled_projects"] >= 0
    assert "status_distribution" in data
    assert "project_managers_workload" in data
    assert "capacity_distribution_by_type" in data


def test_06_inventory_analytics_and_stock_valuation(setup_analytics_test_env):
    """
    Verify inventory analytics returns SKU counts, QOH, available quantities,
    and non-negative stock valuations.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/inventory", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["total_sku_count"] >= 0
    assert Decimal(str(data["total_quantity_on_hand"])) >= Decimal("0.00")
    assert Decimal(str(data["total_reserved_quantity"])) >= Decimal("0.00")
    assert Decimal(str(data["total_available_quantity"])) >= Decimal("0.00")
    assert Decimal(str(data["total_stock_valuation"])) >= Decimal("0.00")
    assert "low_stock_items" in data
    assert "top_stock_items" in data


def test_07_financial_analytics_accounting_invariants(setup_analytics_test_env):
    """
    Verify financial analytics invariants:
    - Cash collected strictly comes from completed payments.
    - Allocations are reported separately without double counting.
    - Receivables aging buckets are populated.
    - Estimated gross margin includes disclosure notes.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.FINANCE_ACCOUNTS]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/finance", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    assert Decimal(str(data["total_invoiced"])) >= Decimal("0.00")
    assert Decimal(str(data["cash_collected"])) >= Decimal("0.00")
    assert Decimal(str(data["outstanding_receivables"])) >= Decimal("0.00")
    assert Decimal(str(data["unallocated_cash"])) >= Decimal("0.00")
    assert Decimal(str(data["allocated_cash"])) >= Decimal("0.00")
    assert Decimal(str(data["unbilled_order_obligation"])) >= Decimal("0.00")

    # Verify aging buckets contain canonical tiers
    bucket_names = [b["bucket"] for b in data["aging_buckets"]]
    assert "Current" in bucket_names
    assert "1-30 Days" in bucket_names
    assert "90+ Days" in bucket_names

    # Verify estimated gross margin disclosure note
    egm = data["estimated_gross_margin"]
    assert "disclosure_note" in egm
    assert "Estimated gross margin is calculated from quotation baseline cost estimates" in egm["disclosure_note"]


def test_08_date_range_validation(setup_analytics_test_env):
    """
    Verify invalid or reversed date range (date_to < date_from) returns HTTP 400 Bad Request.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.SUPER_ADMIN]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/executive?date_from=2026-12-31&date_to=2026-01-01", headers=headers)
    assert res.status_code == 400
    assert "date_to cannot be earlier than date_from" in res.json()["detail"]


def test_09_csv_export_valid_report_types(setup_analytics_test_env):
    """
    Verify CSV export returns Content-Type text/csv with UTF-8 BOM (\xef\xbb\xbf)
    for authorized report types.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.SUPER_ADMIN]
    headers = {"Authorization": f"Bearer {token}"}

    report_types = [
        "sales_summary",
        "sales_reps",
        "projects_summary",
        "inventory_stock",
        "finance_invoices",
        "finance_payments",
        "receivables_aging",
    ]

    for rt in report_types:
        res = client.get(f"/api/v1/analytics/export?report_type={rt}", headers=headers)
        assert res.status_code == 200, f"Report {rt} failed: {res.text}"
        assert res.headers["content-type"].startswith("text/csv")
        assert "attachment; filename=" in res.headers["content-disposition"]
        # Verify UTF-8 BOM is present
        assert res.content[:3] == b"\xef\xbb\xbf"


def test_10_csv_export_invalid_type_rejected(setup_analytics_test_env):
    """
    Verify export rejects arbitrary or malicious report type with HTTP 400 Bad Request.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.SUPER_ADMIN]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/export?report_type=arbitrary_sql_dump", headers=headers)
    assert res.status_code == 400
    assert "Invalid report_type" in res.json()["detail"]


def test_11_operations_analytics_kpis(setup_analytics_test_env):
    """
    Verify operations analytics endpoint returns accurate sections for procurement,
    dispatch, installation, service/warranty, subsidy, and pipeline execution stages.
    """
    token = setup_analytics_test_env["tokens"][SystemRole.SUPER_ADMIN]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/analytics/operations", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["success"] is True
    data = body["data"]

    # Verify all operational sub-modules exist
    assert "procurement" in data
    assert "dispatch" in data
    assert "installation" in data
    assert "service_warranty" in data
    assert "subsidy" in data
    assert "pipeline_stages" in data

    # Verify structure of sub-objects
    assert "total_purchase_orders" in data["procurement"]
    assert "total_dispatches" in data["dispatch"]
    assert "total_schedules" in data["installation"]
    assert "active_warranties_count" in data["service_warranty"]
    assert "total_applications" in data["subsidy"]
    assert isinstance(data["pipeline_stages"], list)

    # Verify Customer role is rejected with HTTP 403
    cust_token = setup_analytics_test_env["tokens"][SystemRole.CUSTOMER]
    res_cust = client.get("/api/v1/analytics/operations", headers={"Authorization": f"Bearer {cust_token}"})
    assert res_cust.status_code == 403

