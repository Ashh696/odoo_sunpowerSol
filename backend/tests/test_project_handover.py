import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Employee
from app.models.crm import Customer, Enquiry, Quotation, QuotationItem, Product
from app.models.projects import Order, Project, ProjectBomItem, ProjectNote
from app.models.workflow import Task
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_project_test_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.SALES,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_prj@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Prj",
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

        # Secondary customer for isolation
        cust_role = db.execute(select(Role).where(Role.slug == SystemRole.CUSTOMER)).scalar_one()
        email_cust2 = "test_customer2_prj@sunpower.com"
        cust2_user = db.execute(select(User).where(User.email == email_cust2)).scalar_one_or_none()
        if not cust2_user:
            cust2_user = User(
                role_id=cust_role.id,
                email=email_cust2,
                full_name="Other Customer Prj",
                hashed_password=hash_password("Pass123!Safe"),
                is_active=True,
                is_verified=True,
            )
            db.add(cust2_user)
            db.commit()
            db.refresh(cust2_user)

        tokens["CUSTOMER_2"] = create_access_token(
            data={"sub": str(cust2_user.id), "role": cust_role.slug, "email": cust2_user.email}
        )
        user_ids["CUSTOMER_2"] = cust2_user.id

        cust1 = db.execute(select(Customer).where(Customer.user_id == user_ids[SystemRole.CUSTOMER])).scalar_one_or_none()
        if not cust1:
            cust1 = Customer(
                user_id=user_ids[SystemRole.CUSTOMER],
                full_name="Primary Project Customer",
                phone="9876543220",
                email="test_customer_prj@sunpower.com",
                address="500 Rooftop Way",
                city="Pune",
                state="Maharashtra",
                pincode="411002",
                created_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(cust1)
            db.commit()
            db.refresh(cust1)

        cust2 = db.execute(select(Customer).where(Customer.user_id == user_ids["CUSTOMER_2"])).scalar_one_or_none()
        if not cust2:
            cust2 = Customer(
                user_id=user_ids["CUSTOMER_2"],
                full_name="Secondary Project Customer",
                phone="9876543221",
                email="test_customer2_prj@sunpower.com",
                address="600 Solar Road",
                city="Pune",
                state="Maharashtra",
                pincode="411003",
                created_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(cust2)
            db.commit()
            db.refresh(cust2)

        # Ensure employee record for Technical Manager
        pm_emp = db.execute(select(Employee).where(Employee.user_id == user_ids[SystemRole.TECHNICAL_MANAGER])).scalar_one_or_none()
        pm_emp_id = pm_emp.id if pm_emp else None

    return tokens, user_ids, cust1.id, cust2.id, pm_emp_id


def _create_confirmed_order_with_items(customer_id, user_id):
    """Helper to create an accepted quotation and an order with advance payment."""
    with SessionLocal() as db:
        today = date.today()
        enq = Enquiry(
            enquiry_number=f"ENQ-{uuid.uuid4().hex[:6].upper()}",
            customer_id=customer_id,
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            monthly_electricity_bill=Decimal("6000.00"),
            status="WON",
        )
        db.add(enq)
        db.flush()

        prod1 = db.execute(select(Product).where(Product.category == "SOLAR_PANEL", Product.is_active == True)).scalars().first()
        prod2 = db.execute(select(Product).where(Product.category == "INVERTER", Product.is_active == True)).scalars().first()

        if not prod1:
            prod1 = Product(
                product_code=f"PANEL-{uuid.uuid4().hex[:6].upper()}",
                name="Monocrystalline 550W Module",
                category="SOLAR_PANEL",
                unit_of_measure="NOS",
                base_price=Decimal("12000.00"),
                is_active=True,
            )
            db.add(prod1)
            db.flush()

        if not prod2:
            prod2 = Product(
                product_code=f"INV-{uuid.uuid4().hex[:6].upper()}",
                name="5kW Hybrid Solar Inverter",
                category="INVERTER",
                unit_of_measure="NOS",
                base_price=Decimal("55000.00"),
                is_active=True,
            )
            db.add(prod2)
            db.flush()

        quo = Quotation(
            quotation_number=f"Q-PRJ-{uuid.uuid4().hex[:6].upper()}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            gross_amount=Decimal("175000.00"),
            net_payable_amount=Decimal("175000.00"),
            valid_until=today + timedelta(days=30),
            quotation_date=today,
            status="ACCEPTED",
            created_by=user_id,
        )
        db.add(quo)
        db.flush()

        item1 = QuotationItem(
            quotation_id=quo.id,
            product_id=prod1.id,
            item_description=prod1.name,
            quantity=Decimal("10.00"),
            unit_price=Decimal("12000.00"),
            total_amount=Decimal("120000.00"),
        )
        item2 = QuotationItem(
            quotation_id=quo.id,
            product_id=prod2.id,
            item_description=prod2.name,
            quantity=Decimal("1.00"),
            unit_price=Decimal("55000.00"),
            total_amount=Decimal("55000.00"),
        )
        db.add(item1)
        db.add(item2)
        db.flush()

        order = Order(
            order_number=f"ORD-PRJ-{uuid.uuid4().hex[:6].upper()}",
            quotation_id=quo.id,
            customer_id=customer_id,
            order_date=today,
            total_amount=Decimal("175000.00"),
            advance_paid=Decimal("50000.00"),  # Advance recorded
            balance_amount=Decimal("125000.00"),
            status="CONFIRMED",
            created_by=user_id,
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order.id, quo.id, prod1.id, prod2.id


# ==========================================
# 1. PROJECT HANDOVER TESTS
# ==========================================

def test_project_handover_success(setup_project_test_env):
    tokens, user_ids, cust1_id, _, pm_emp_id = setup_project_test_env
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}

    order_id, quo_id, p1_id, p2_id = _create_confirmed_order_with_items(cust1_id, user_ids[SystemRole.SUPER_ADMIN])

    handover_payload = {
        "project_manager_id": pm_emp_id,
        "site_address": "500 Rooftop Way, Solar Sector 4, Pune",
        "planned_start_date": str(date.today()),
        "planned_completion_date": str(date.today() + timedelta(days=21)),
        "initial_notes": "Rooftop structure requires southern elevation tilt bracket",
    }

    res = client.post(f"/api/v1/projects/orders/{order_id}/handover", json=handover_payload, headers=tm_headers)
    assert res.status_code == 201, res.text
    data = res.json()["data"]

    assert data["order_id"] == order_id
    assert data["customer_id"] == cust1_id
    assert data["status"] == "INITIATED"
    assert data["project_code"].startswith("PRJ-")
    assert float(data["system_capacity_kw"]) == 5.00
    assert data["system_type"] == "ON_GRID"

    # Base BOM items transferred
    assert len(data["bom_items"]) == 2
    bom_pids = [b["product_id"] for b in data["bom_items"]]
    assert p1_id in bom_pids
    assert p2_id in bom_pids

    # Tasks seeded
    assert len(data["tasks"]) == 2
    task_types = [t["task_type"] for t in data["tasks"]]
    assert "INSTALLATION" in task_types
    assert "PROCUREMENT" in task_types

    # Notes recorded
    assert len(data["notes"]) == 1
    assert "southern elevation tilt bracket" in data["notes"][0]["content"]

    # Verify order status transitioned to PROCESSING
    admin_headers = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    res_ord = client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
    assert res_ord.status_code == 200
    assert res_ord.json()["data"]["status"] == "PROCESSING"


def test_duplicate_project_handover_rejected(setup_project_test_env):
    tokens, user_ids, cust1_id, _, pm_emp_id = setup_project_test_env
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}

    order_id, _, _, _ = _create_confirmed_order_with_items(cust1_id, user_ids[SystemRole.SUPER_ADMIN])

    # First handover succeeds
    res1 = client.post(f"/api/v1/projects/orders/{order_id}/handover", json={}, headers=tm_headers)
    assert res1.status_code == 201

    # Second handover must return 409 Conflict
    res2 = client.post(f"/api/v1/projects/orders/{order_id}/handover", json={}, headers=tm_headers)
    assert res2.status_code == 409
    assert "At most one project per order is permitted" in res2.json()["detail"]


def test_project_handover_eligibility_checks(setup_project_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_project_test_env
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}

    # 1. Order in PENDING_ADVANCE with 0 advance paid
    with SessionLocal() as db:
        today = date.today()
        quo_id = _create_test_quo_standalone(db, cust1_id, user_ids[SystemRole.SUPER_ADMIN])
        zero_order = Order(
            order_number=f"ORD-ZERO-{uuid.uuid4().hex[:6].upper()}",
            quotation_id=quo_id,
            customer_id=cust1_id,
            order_date=today,
            total_amount=Decimal("150000.00"),
            advance_paid=Decimal("0.00"),
            balance_amount=Decimal("150000.00"),
            status="PENDING_ADVANCE",
            created_by=user_ids[SystemRole.SUPER_ADMIN],
        )
        db.add(zero_order)
        db.commit()
        zero_order_id = zero_order.id

    res_zero = client.post(f"/api/v1/projects/orders/{zero_order_id}/handover", json={}, headers=tm_headers)
    assert res_zero.status_code == 400
    assert "PENDING_ADVANCE" in res_zero.json()["detail"]

    # 2. CANCELLED order
    with SessionLocal() as db:
        ord_obj = db.execute(select(Order).where(Order.id == zero_order_id)).scalar_one()
        ord_obj.status = "CANCELLED"
        db.commit()

    res_canc = client.post(f"/api/v1/projects/orders/{zero_order_id}/handover", json={}, headers=tm_headers)
    assert res_canc.status_code == 409
    assert "CANCELLED" in res_canc.json()["detail"]


def _create_test_quo_standalone(db, customer_id, user_id):
    today = date.today()
    enq = Enquiry(
        enquiry_number=f"ENQ-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer_id,
        source="DIRECT",
        system_type="ON_GRID",
        proposed_capacity_kw=Decimal("3.00"),
        monthly_electricity_bill=Decimal("5000.00"),
        status="WON",
    )
    db.add(enq)
    db.flush()

    quo = Quotation(
        quotation_number=f"Q-ST-{uuid.uuid4().hex[:6].upper()}",
        enquiry_id=enq.id,
        version=1,
        system_type="ON_GRID",
        capacity_kw=Decimal("3.00"),
        gross_amount=Decimal("150000.00"),
        net_payable_amount=Decimal("150000.00"),
        valid_until=today + timedelta(days=30),
        quotation_date=today,
        status="ACCEPTED",
        created_by=user_id,
    )
    db.add(quo)
    db.commit()
    db.refresh(quo)
    return quo.id


def test_project_handover_unauthorized(setup_project_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_project_test_env
    order_id, _, _, _ = _create_confirmed_order_with_items(cust1_id, user_ids[SystemRole.SUPER_ADMIN])

    # SALES, CUSTOMER, FINANCE_ACCOUNTS do not have projects.create
    for role in [SystemRole.SALES, SystemRole.CUSTOMER, SystemRole.FINANCE_ACCOUNTS]:
        headers = {"Authorization": f"Bearer {tokens[role]}"}
        res = client.post(f"/api/v1/projects/orders/{order_id}/handover", json={}, headers=headers)
        assert res.status_code == 403, f"Expected 403 for role {role}, got {res.status_code}"


# ==========================================
# 2. HYBRID BOM & ADJUSTMENT TESTS
# ==========================================

def test_hybrid_bom_project_adjustment(setup_project_test_env):
    tokens, user_ids, cust1_id, _, pm_emp_id = setup_project_test_env
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}

    order_id, _, p1_id, _ = _create_confirmed_order_with_items(cust1_id, user_ids[SystemRole.SUPER_ADMIN])
    res_ho = client.post(f"/api/v1/projects/orders/{order_id}/handover", json={}, headers=tm_headers)
    assert res_ho.status_code == 201
    proj_id = res_ho.json()["data"]["id"]

    # 1. Retrieve project BOM via existing BOM router endpoint
    res_bom = client.get(f"/api/v1/projects/{proj_id}/bom", headers=tm_headers)
    assert res_bom.status_code == 200
    bom_items = res_bom.json()["data"]["items"]
    assert len(bom_items) >= 1

    item1 = [it for it in bom_items if it["product_id"] == p1_id][0]
    initial_qty = float(item1["planned_quantity"])

    # 2. Adjust planned quantity via existing BOM router endpoint
    res_adj = client.put(
        f"/api/v1/projects/{proj_id}/bom/items/{item1['id']}",
        json={"planned_quantity": initial_qty + 2.0},
        headers=tm_headers,
    )
    assert res_adj.status_code == 200
    assert float(res_adj.json()["data"]["planned_quantity"]) == initial_qty + 2.0


# ==========================================
# 3. CUSTOMER ISOLATION & INTERNAL NOTES
# ==========================================

def test_customer_project_isolation_and_internal_notes(setup_project_test_env):
    tokens, user_ids, cust1_id, cust2_id, _ = setup_project_test_env
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}
    cust1_headers = {"Authorization": f"Bearer {tokens[SystemRole.CUSTOMER]}"}
    cust2_headers = {"Authorization": f"Bearer {tokens['CUSTOMER_2']}"}

    order_id, _, _, _ = _create_confirmed_order_with_items(cust1_id, user_ids[SystemRole.SUPER_ADMIN])
    res_ho = client.post(f"/api/v1/projects/orders/{order_id}/handover", json={}, headers=tm_headers)
    assert res_ho.status_code == 201
    proj_id = res_ho.json()["data"]["id"]

    # Add 1 internal note and 1 public note
    res_n1 = client.post(
        f"/api/v1/projects/{proj_id}/notes",
        json={"note_type": "TECHNICAL", "content": "Internal inverter wiring specification", "is_internal": True},
        headers=tm_headers,
    )
    assert res_n1.status_code == 201

    res_n2 = client.post(
        f"/api/v1/projects/{proj_id}/notes",
        json={"note_type": "GENERAL", "content": "Scheduled installation arrival on Friday 10 AM", "is_internal": False},
        headers=tm_headers,
    )
    assert res_n2.status_code == 201

    # Staff/TM sees both notes
    res_tm = client.get(f"/api/v1/projects/{proj_id}", headers=tm_headers)
    assert res_tm.status_code == 200
    tm_notes = res_tm.json()["data"]["notes"]
    assert len(tm_notes) >= 2
    assert any(n["is_internal"] is True for n in tm_notes)

    # Customer 1 sees only the public note; internal note is hidden
    res_c1 = client.get(f"/api/v1/projects/{proj_id}", headers=cust1_headers)
    assert res_c1.status_code == 200
    c1_notes = res_c1.json()["data"]["notes"]
    assert len(c1_notes) == 1
    assert c1_notes[0]["is_internal"] is False
    assert "Friday 10 AM" in c1_notes[0]["content"]

    # Customer 2 attempting to view Customer 1's project gets 403 Forbidden
    res_c2 = client.get(f"/api/v1/projects/{proj_id}", headers=cust2_headers)
    assert res_c2.status_code == 403
    assert "own customer account" in res_c2.json()["detail"]


# ==========================================
# 4. PROJECT UPDATE TESTS
# ==========================================

def test_project_update(setup_project_test_env):
    tokens, user_ids, cust1_id, _, _ = setup_project_test_env
    tm_headers = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}

    order_id, _, _, _ = _create_confirmed_order_with_items(cust1_id, user_ids[SystemRole.SUPER_ADMIN])
    res_ho = client.post(f"/api/v1/projects/orders/{order_id}/handover", json={}, headers=tm_headers)
    proj_id = res_ho.json()["data"]["id"]

    # Update status to PROCUREMENT
    res_up = client.put(f"/api/v1/projects/{proj_id}", json={"status": "PROCUREMENT"}, headers=tm_headers)
    assert res_up.status_code == 200
    assert res_up.json()["data"]["status"] == "PROCUREMENT"

    # Unauthorized role (SALES) cannot update project
    sales_headers = {"Authorization": f"Bearer {tokens[SystemRole.SALES]}"}
    res_unauth = client.put(f"/api/v1/projects/{proj_id}", json={"status": "INSTALLATION"}, headers=sales_headers)
    assert res_unauth.status_code == 403
