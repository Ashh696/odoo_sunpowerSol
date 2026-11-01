import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date, timedelta
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role
from app.models.crm import Customer, Product, Enquiry, Quotation
from app.models.projects import (
    Order,
    Project,
    ProjectBomItem,
)
from app.models.inventory import (
    Inventory,
    StockMovement,
    SerialNumber,
    SerialNumberHistory,
    StockReservation,
    Dispatch,
    DispatchItem,
    DispatchSerial,
    DeliveryConfirmation,
)
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_dispatch_test_env():
    tokens = {}
    user_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.DIRECTOR,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.SALES,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.SERVICE_WARRANTY,
            SystemRole.CUSTOMER,
        ]

        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"test_{slug.lower()}_disp@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Test {slug} Disp",
                    hashed_password=hash_password("Pass123!Safe"),
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            tokens[slug] = create_access_token({"sub": str(user.id), "role": slug})
            user_ids[slug] = user.id

    return {"tokens": tokens, "user_ids": user_ids}


@pytest.fixture(scope="module")
def dispatch_test_data(setup_dispatch_test_env):
    uid = uuid.uuid4().hex[:6]
    with SessionLocal() as db:
        warehouse_user_id = setup_dispatch_test_env["user_ids"][SystemRole.WAREHOUSE_PROCUREMENT]
        sales_user_id = setup_dispatch_test_env["user_ids"][SystemRole.SALES]

        # 1. Customer
        cust = Customer(
            customer_type="INDIVIDUAL",
            full_name=f"Dispatch Test Customer {uid}",
            phone=f"98765{uid[:5]}",
            email=f"disp_cust_{uid}@example.com",
            address="123 Solar Street, Green City",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            created_by=sales_user_id,
            is_active=True,
        )
        db.add(cust)
        db.flush()

        # 2. Products (one serialized, one non-serialized)
        p_serial = Product(
            product_code=f"INV-DISP-{uid}",
            name=f"Inverter 5kW {uid}",
            category="INVERTER",
            brand="SunPower",
            model_number=f"SP-5K-{uid}",
            wattage_or_capacity="5000W",
            unit_of_measure="NOS",
            base_price=Decimal("45000.00"),
            tax_rate_percent=Decimal("18.00"),
            min_stock_alert=Decimal("2.00"),
            is_serialized=True,
            is_active=True,
        )
        p_bulk = Product(
            product_code=f"CBL-DISP-{uid}",
            name=f"DC Cable 4sqmm {uid}",
            category="CABLE",
            brand="Polycab",
            model_number=f"DC-4SQ-{uid}",
            wattage_or_capacity="N/A",
            unit_of_measure="METER",
            base_price=Decimal("65.00"),
            tax_rate_percent=Decimal("18.00"),
            min_stock_alert=Decimal("50.00"),
            is_serialized=False,
            is_active=True,
        )
        db.add_all([p_serial, p_bulk])
        db.flush()

        # 3. Inventory for both products
        inv_serial = Inventory(
            product_id=p_serial.id,
            warehouse_location="Warehouse A - Bay 1",
            quantity_on_hand=Decimal("10.00"),
            reserved_quantity=Decimal("0.00"),
            quantity_available=Decimal("10.00"),
            average_unit_cost=Decimal("38000.00"),
            reorder_level=Decimal("2.00"),
        )
        inv_bulk = Inventory(
            product_id=p_bulk.id,
            warehouse_location="Warehouse A - Rack 3",
            quantity_on_hand=Decimal("500.00"),
            reserved_quantity=Decimal("0.00"),
            quantity_available=Decimal("500.00"),
            average_unit_cost=Decimal("45.00"),
            reorder_level=Decimal("50.00"),
        )
        db.add_all([inv_serial, inv_bulk])
        db.flush()

        # 4. Serial numbers for p_serial
        serials = []
        for i in range(1, 6):
            sn = SerialNumber(
                serial_number=f"SN-DISP-{uid}-{i:03d}",
                product_id=p_serial.id,
                inventory_id=inv_serial.id,
                status="IN_STOCK",
                warranty_months=60,
                received_date=date.today(),
            )
            db.add(sn)
            serials.append(sn)
        db.flush()

        # 5. Enquiry & Quotation for Order
        enq = Enquiry(
            enquiry_number=f"ENQ-DISP-{uid}",
            customer_id=cust.id,
            source="DIRECT",
            system_type="ON_GRID",
            proposed_capacity_kw=Decimal("5.00"),
            monthly_electricity_bill=Decimal("5000.00"),
            status="WON",
        )
        db.add(enq)
        db.flush()

        quo = Quotation(
            quotation_number=f"Q-DISP-{uid}",
            enquiry_id=enq.id,
            version=1,
            system_type="ON_GRID",
            capacity_kw=Decimal("5.00"),
            total_product_cost=Decimal("250000.00"),
            installation_cost=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            gross_amount=Decimal("250000.00"),
            subsidy_estimate=Decimal("0.00"),
            net_payable_amount=Decimal("250000.00"),
            valid_until=date.today() + timedelta(days=30),
            quotation_date=date.today(),
            status="ACCEPTED",
            created_by=sales_user_id,
        )
        db.add(quo)
        db.flush()

        # 6. Order
        order = Order(
            order_number=f"ORD-DISP-{uid}",
            customer_id=cust.id,
            quotation_id=quo.id,
            order_date=date.today(),
            total_amount=Decimal("250000.00"),
            advance_paid=Decimal("50000.00"),
            balance_amount=Decimal("200000.00"),
            status="CONFIRMED",
            created_by=sales_user_id,
        )
        db.add(order)
        db.flush()

        # 7. Project
        proj = Project(
            project_code=f"PRJ-DISP-{uid}",
            order_id=order.id,
            customer_id=cust.id,
            system_capacity_kw=Decimal("5.0"),
            system_type="ON_GRID",
            site_address="123 Solar Street, Green City",
            planned_start_date=date.today(),
            planned_completion_date=date.today() + timedelta(days=30),
            status="COMMITTED",
        )
        db.add(proj)
        db.flush()

        # 7. Project BOM items
        bom_serial = ProjectBomItem(
            project_id=proj.id,
            product_id=p_serial.id,
            item_category="INVERTER",
            planned_quantity=Decimal("2.00"),
            allocated_quantity=Decimal("2.00"),
            dispatched_quantity=Decimal("0.00"),
            installed_quantity=Decimal("0.00"),
            unit_cost_snapshot=Decimal("38000.00"),
        )
        bom_bulk = ProjectBomItem(
            project_id=proj.id,
            product_id=p_bulk.id,
            item_category="CABLE",
            planned_quantity=Decimal("100.00"),
            allocated_quantity=Decimal("100.00"),
            dispatched_quantity=Decimal("0.00"),
            installed_quantity=Decimal("0.00"),
            unit_cost_snapshot=Decimal("45.00"),
        )
        db.add_all([bom_serial, bom_bulk])
        db.commit()

        return {
            "customer_id": cust.id,
            "project_id": proj.id,
            "order_id": order.id,
            "p_serial_id": p_serial.id,
            "p_bulk_id": p_bulk.id,
            "serials": [s.id for s in serials],
            "serial_numbers": [s.serial_number for s in serials],
            "inv_serial_id": inv_serial.id,
            "inv_bulk_id": inv_bulk.id,
        }


def test_project_material_readiness(setup_dispatch_test_env, dispatch_test_data):
    token = setup_dispatch_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    project_id = dispatch_test_data["project_id"]

    res = client.get(
        f"/api/v1/projects/{project_id}/material-readiness",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["project_id"] == project_id
    assert data["all_ready_for_dispatch"] is True
    assert len(data["items"]) == 2

    serial_item = next(i for i in data["items"] if i["product_id"] == dispatch_test_data["p_serial_id"])
    assert float(serial_item["planned_quantity"]) == 2.0
    assert float(serial_item["remaining_to_dispatch"]) == 2.0
    assert float(serial_item["warehouse_on_hand"]) == 10.0
    assert serial_item["is_serialized"] is True
    assert serial_item["is_ready_for_dispatch"] is True


def test_stock_reservation_lifecycle(setup_dispatch_test_env, dispatch_test_data):
    token = setup_dispatch_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    project_id = dispatch_test_data["project_id"]
    p_bulk_id = dispatch_test_data["p_bulk_id"]

    # 1. Create reservation of 50m cable
    res = client.post(
        "/api/v1/dispatches/reservations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "product_id": p_bulk_id,
            "reserved_quantity": 50.0,
        },
    )
    assert res.status_code == 201, res.text
    reservation_id = res.json()["data"]["id"]

    # Verify inventory updated
    with SessionLocal() as db:
        inv = db.execute(select(Inventory).where(Inventory.product_id == p_bulk_id)).scalar_one()
        assert inv.reserved_quantity == Decimal("50.00")
        assert inv.quantity_available == Decimal("450.00")

    # 2. Release reservation
    res_rel = client.delete(
        f"/api/v1/dispatches/reservations/{reservation_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_rel.status_code == 200, res_rel.text

    # Verify inventory restored
    with SessionLocal() as db:
        inv = db.execute(select(Inventory).where(Inventory.product_id == p_bulk_id)).scalar_one()
        assert inv.reserved_quantity == Decimal("0.00")
        assert inv.quantity_available == Decimal("500.00")


def test_serial_validation_errors(setup_dispatch_test_env, dispatch_test_data):
    token = setup_dispatch_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    project_id = dispatch_test_data["project_id"]
    p_serial_id = dispatch_test_data["p_serial_id"]

    # Attempt to dispatch serialized product without serial numbers
    res = client.post(
        "/api/v1/dispatches",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "items": [
                {
                    "product_id": p_serial_id,
                    "dispatched_quantity": 2.0,
                    "serial_number_ids": [],
                }
            ],
        },
    )
    assert res.status_code == 400
    assert "Serialized component" in res.json()["detail"] or "scanned serial numbers" in res.json()["detail"]


def test_over_dispatch_validation_errors(setup_dispatch_test_env, dispatch_test_data):
    token = setup_dispatch_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    project_id = dispatch_test_data["project_id"]
    p_bulk_id = dispatch_test_data["p_bulk_id"]

    # Attempt to dispatch more than planned in BOM (planned is 100, stock is 500)
    res = client.post(
        "/api/v1/dispatches",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "items": [
                {
                    "product_id": p_bulk_id,
                    "dispatched_quantity": 150.0,
                    "serial_number_ids": [],
                }
            ],
        },
    )
    assert res.status_code == 400
    assert "exceeds remaining BOM quantity" in res.json()["detail"]


def test_atomic_dispatch_deduction_and_history(setup_dispatch_test_env, dispatch_test_data):
    token = setup_dispatch_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    project_id = dispatch_test_data["project_id"]
    p_serial_id = dispatch_test_data["p_serial_id"]
    p_bulk_id = dispatch_test_data["p_bulk_id"]
    serials = dispatch_test_data["serials"][:2]

    # Execute valid dispatch: 2 inverters with 2 serial numbers, 80m cables
    res = client.post(
        "/api/v1/dispatches",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
            "vehicle_number": "KA-01-MJ-1234",
            "driver_name": "Ramesh Kumar",
            "driver_phone": "9876543210",
            "remarks": "Priority dispatch for solar installation",
            "items": [
                {
                    "product_id": p_serial_id,
                    "dispatched_quantity": 2.0,
                    "serial_number_ids": serials,
                },
                {
                    "product_id": p_bulk_id,
                    "dispatched_quantity": 80.0,
                    "serial_number_ids": [],
                },
            ],
        },
    )
    assert res.status_code == 201, res.text
    disp_data = res.json()["data"]
    dispatch_id = disp_data["id"]
    assert disp_data["dispatch_status"] == "DISPATCHED"

    # Verify Database state atomically
    with SessionLocal() as db:
        # 1. Project BOM items updated
        bom_s = db.execute(
            select(ProjectBomItem).where(
                ProjectBomItem.project_id == project_id,
                ProjectBomItem.product_id == p_serial_id,
            )
        ).scalar_one()
        assert bom_s.dispatched_quantity == Decimal("2.00")

        bom_b = db.execute(
            select(ProjectBomItem).where(
                ProjectBomItem.project_id == project_id,
                ProjectBomItem.product_id == p_bulk_id,
            )
        ).scalar_one()
        assert bom_b.dispatched_quantity == Decimal("80.00")

        # 2. Inventory decremented
        inv_s = db.execute(select(Inventory).where(Inventory.product_id == p_serial_id)).scalar_one()
        assert inv_s.quantity_on_hand == Decimal("8.00")
        assert inv_s.quantity_available == Decimal("8.00")

        inv_b = db.execute(select(Inventory).where(Inventory.product_id == p_bulk_id)).scalar_one()
        assert inv_b.quantity_on_hand == Decimal("420.00")
        assert inv_b.quantity_available == Decimal("420.00")

        # 3. Stock movements recorded (negative)
        movements = db.execute(
            select(StockMovement).where(
                StockMovement.reference_type == "DISPATCH",
                StockMovement.reference_id == dispatch_id,
            )
        ).scalars().all()
        assert len(movements) == 2
        for m in movements:
            assert m.movement_type == "DISPATCH"
            assert m.quantity < 0

        # 4. Serial numbers status updated to DISPATCHED
        for sid in serials:
            sn = db.execute(select(SerialNumber).where(SerialNumber.id == sid)).scalar_one()
            assert sn.status == "DISPATCHED"
            # History log exists
            hist = db.execute(
                select(SerialNumberHistory).where(
                    SerialNumberHistory.serial_number_id == sid,
                    SerialNumberHistory.new_status == "DISPATCHED",
                )
            ).scalars().all()
            assert len(hist) >= 1

        # 5. Project status updated to DISPATCHED
        proj = db.execute(select(Project).where(Project.id == project_id)).scalar_one()
        assert proj.status == "DISPATCHED"


def test_delivery_confirmation_and_idempotency(setup_dispatch_test_env, dispatch_test_data):
    token = setup_dispatch_test_env["tokens"][SystemRole.WAREHOUSE_PROCUREMENT]
    project_id = dispatch_test_data["project_id"]

    # Retrieve dispatches for this project or create one if none exists
    res_list = client.get(
        f"/api/v1/dispatches?project_id={project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_list.status_code == 200
    dispatches = res_list.json()["data"]["items"]
    if len(dispatches) == 0:
        # Create a dispatch
        res_create = client.post(
            "/api/v1/dispatches",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": project_id,
                "items": [
                    {
                        "product_id": dispatch_test_data["p_bulk_id"],
                        "dispatched_quantity": 10.0,
                        "serial_number_ids": [],
                    }
                ],
            },
        )
        assert res_create.status_code == 201
        dispatch_id = res_create.json()["data"]["id"]
    else:
        dispatch_id = dispatches[0]["id"]

    # Check inventory was NOT decremented again during delivery confirmation
    with SessionLocal() as db:
        inv_before = db.execute(
            select(Inventory).where(Inventory.product_id == dispatch_test_data["p_serial_id"])
        ).scalar_one()
        qty_before = inv_before.quantity_on_hand

    # Confirm delivery
    res_conf = client.post(
        f"/api/v1/dispatches/{dispatch_id}/delivery-confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "confirmation_type": "CUSTOMER_SIGN",
            "recipient_name": "Suresh Patil",
            "recipient_phone": "9876500001",
            "delivery_notes": "All items verified and received in good condition on site.",
        },
    )
    assert res_conf.status_code == 200, res_conf.text
    assert res_conf.json()["data"]["dispatch_status"] == "DELIVERED"
    assert res_conf.json()["data"]["is_confirmed"] is True

    # Verify inventory was unchanged by delivery confirmation
    with SessionLocal() as db:
        inv_after = db.execute(
            select(Inventory).where(Inventory.product_id == dispatch_test_data["p_serial_id"])
        ).scalar_one()
        assert inv_after.quantity_on_hand == qty_before

    # Attempt to confirm delivery again (should reject as already confirmed)
    res_conf2 = client.post(
        f"/api/v1/dispatches/{dispatch_id}/delivery-confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "confirmation_type": "CUSTOMER_SIGN",
            "recipient_name": "Suresh Patil",
            "recipient_phone": "9876500001",
        },
    )
    assert res_conf2.status_code == 400
    assert "already" in res_conf2.json()["detail"].lower() and "confirmed" in res_conf2.json()["detail"].lower()


def test_rbac_dispatch_restrictions(setup_dispatch_test_env, dispatch_test_data):
    sales_token = setup_dispatch_test_env["tokens"][SystemRole.SALES]
    customer_token = setup_dispatch_test_env["tokens"][SystemRole.CUSTOMER]
    project_id = dispatch_test_data["project_id"]

    # Sales cannot create dispatch
    res = client.post(
        "/api/v1/dispatches",
        headers={"Authorization": f"Bearer {sales_token}"},
        json={"project_id": project_id, "items": []},
    )
    assert res.status_code == 403

    # Customer cannot access dispatch list
    res_c = client.get(
        "/api/v1/dispatches",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert res_c.status_code == 403
