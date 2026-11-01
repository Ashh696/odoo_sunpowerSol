"""
SUNPOWER SOLUTIONS — SIMS MASTER END-TO-END FLOW TEST SUITE
============================================================
Validates the complete, continuous business lifecycle across all 14 project phases:
1. Customer Creation & Enquiry Registration (CRM)
2. Technical Feasibility Site Survey & Engineering Assessment
3. Quotation Formulation, Cost Estimation, Multi-Stage Approval & Customer Acceptance
4. Order Conversion, Advance Receipt & Automatic Project Handover
5. Supplier Procurement PO, PO Issuance & Goods Receipt Note (GRN) Inwarding
6. Stock Reservation, Serial Number Tracking & Material Dispatch Delivery
7. Installation Scheduling, Technician Worklog, Quality Checklist & Commissioning Testing
8. Milestone Tax Invoicing, Customer Cash Collections & Payment Allocation
9. Supplier Accounts Payable Invoicing, Disbursements & Realized Project Profitability
10. Warranty Policy Auto-Registration, Service Ticket, On-Site Visit & Component Replacement
11. PM Surya Ghar Subsidy Application, Document Compliance, Approval & DBT Disbursement
12. Operational Workflow Analytics & Executive BI Dashboard Reconciliation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
import uuid

from app.main import app
from app.database import SessionLocal
from app.models.auth import User, Role, Employee, Department, FileAttachment
from app.models.crm import Customer, Product, Enquiry, Survey, Quotation, QuotationItem
from app.models.projects import (
    Order,
    Project,
    ProjectBomItem,
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
    SupplierInvoice,
    SupplierPayment,
    SupplierPaymentAllocation,
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
from app.models.installations import (
    InstallationSchedule,
    InstallationScheduleTechnician,
    Installation,
    TechnicianWorklog,
    InstallationChecklist,
    InstallationTest,
)
from app.models.finance import (
    Invoice,
    InvoiceItem,
    Payment,
    PaymentAllocation,
)
from app.models.warranty import (
    WarrantyPolicy,
    WarrantyRecord,
    WarrantyEvent,
    ServiceTicket,
    ServiceVisit,
    Replacement,
    ServiceTicketConfirmation,
)
from app.models.subsidy import (
    SubsidyApplication,
    SubsidyDocument,
    SubsidyStatusHistory,
    SubsidyPayment,
)
from app.utils.roles import SystemRole
from app.utils.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_master_e2e_env():
    """
    Initializes a clean, fully populated test environment covering all 9 canonical roles,
    active employee profiles, active departments, default warranty policy, and catalog products.
    """
    tokens = {}
    user_ids = {}
    emp_ids = {}

    with SessionLocal() as db:
        role_slugs = [
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.SALES,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.SERVICE_WARRANTY,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.CUSTOMER,
        ]

        # 1. Ensure Roles & Users
        for slug in role_slugs:
            role_obj = db.execute(select(Role).where(Role.slug == slug)).scalar_one()
            email = f"master_e2e_{slug.lower()}@sunpower.com"
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    role_id=role_obj.id,
                    email=email,
                    full_name=f"Master {slug.replace('_', ' ').title()}",
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

        # 2. Ensure Department
        dept = db.execute(select(Department).where(Department.code == "OPS-E2E")).scalar_one_or_none()
        if not dept:
            dept = Department(name="Master Operations", code="OPS-E2E", is_active=True)
            db.add(dept)
            db.commit()
            db.refresh(dept)

        # 3. Ensure Employees for operational roles
        operational_roles = [
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.SALES,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.SERVICE_WARRANTY,
        ]
        for op_role in operational_roles:
            u_id = user_ids[op_role]
            emp = db.execute(select(Employee).where(Employee.user_id == u_id)).scalar_one_or_none()
            if not emp:
                emp = Employee(
                    user_id=u_id,
                    department_id=dept.id,
                    employee_code=f"EMP-E2E-{op_role[:3]}",
                    designation=f"Master {op_role}",
                    joining_date=date.today() - timedelta(days=365),
                    employment_type="FULL_TIME",
                    is_active=True,
                )
                db.add(emp)
                db.commit()
                db.refresh(emp)
            emp_ids[op_role] = emp.id

        # 4. Ensure Catalog Products (Inverter, Panel, Cable)
        p_inv = db.execute(select(Product).where(Product.product_code == "PRD-E2E-INV5K")).scalar_one_or_none()
        if not p_inv:
            p_inv = Product(
                product_code="PRD-E2E-INV5K",
                name="SunPower Hybrid Inverter 5kW E2E",
                category="INVERTER",
                brand="SunPower",
                model_number="SP-INV-5K",
                unit_of_measure="NOS",
                base_price=Decimal("45000.00"),
                tax_rate_percent=Decimal("18.00"),
                is_serialized=True,
                is_active=True,
            )
            db.add(p_inv)

        p_pnl = db.execute(select(Product).where(Product.product_code == "PRD-E2E-PNL550")).scalar_one_or_none()
        if not p_pnl:
            p_pnl = Product(
                product_code="PRD-E2E-PNL550",
                name="SunPower Mono PERC Panel 550W E2E",
                category="SOLAR_PANEL",
                brand="SunPower",
                model_number="SP-550W",
                unit_of_measure="NOS",
                base_price=Decimal("14000.00"),
                tax_rate_percent=Decimal("12.00"),
                is_serialized=True,
                is_active=True,
            )
            db.add(p_pnl)

        p_cbl = db.execute(select(Product).where(Product.product_code == "PRD-E2E-CBL4SQ")).scalar_one_or_none()
        if not p_cbl:
            p_cbl = Product(
                product_code="PRD-E2E-CBL4SQ",
                name="Solar DC Cable 4sqmm E2E",
                category="CABLE",
                brand="Polycab",
                model_number="DC-4SQ",
                unit_of_measure="METER",
                base_price=Decimal("60.00"),
                tax_rate_percent=Decimal("18.00"),
                is_serialized=False,
                is_active=True,
            )
            db.add(p_cbl)

        db.commit()
        db.refresh(p_inv)
        db.refresh(p_pnl)
        db.refresh(p_cbl)

        # 5. Ensure Warranty Policy
        pol = db.execute(select(WarrantyPolicy).where(WarrantyPolicy.policy_code == "POL-E2E-60M")).scalar_one_or_none()
        if not pol:
            pol = WarrantyPolicy(
                policy_code="POL-E2E-60M",
                name="Standard 5-Year Comprehensive Warranty",
                warranty_period_months=60,
                activation_trigger="COMMISSIONING",
                terms_and_conditions="Comprehensive on-site parts and labor guarantee.",
                is_active=True,
            )
            db.add(pol)
            db.commit()
            db.refresh(pol)

        # 6. Ensure FileAttachment for tests
        att = db.execute(select(FileAttachment).where(FileAttachment.file_name == "e2e_document.pdf")).scalar_one_or_none()
        if not att:
            att = FileAttachment(
                entity_type="SUBSIDY",
                entity_id=1,
                file_name="e2e_document.pdf",
                file_path="/uploads/e2e_document.pdf",
                file_size_bytes=10240,
                mime_type="application/pdf",
                uploaded_by=user_ids[SystemRole.SUPER_ADMIN],
            )
            db.add(att)
            db.commit()
            db.refresh(att)

    return {
        "tokens": tokens,
        "user_ids": user_ids,
        "emp_ids": emp_ids,
        "dept_id": dept.id,
        "products": {
            "inverter": p_inv.id,
            "panel": p_pnl.id,
            "cable": p_cbl.id,
        },
        "policy_id": pol.id,
        "attachment_id": att.id,
    }


def test_complete_master_lifecycle_flow(setup_master_e2e_env):
    """
    Executes the unbroken, end-to-end solar operational lifecycle across 12 sequential stages.
    """
    env = setup_master_e2e_env
    tokens = env["tokens"]
    user_ids = env["user_ids"]
    emp_ids = env["emp_ids"]
    products = env["products"]
    uid = uuid.uuid4().hex[:6].upper()

    headers_admin = {"Authorization": f"Bearer {tokens[SystemRole.SUPER_ADMIN]}"}
    headers_sales = {"Authorization": f"Bearer {tokens[SystemRole.SALES]}"}
    headers_tech = {"Authorization": f"Bearer {tokens[SystemRole.TECHNICAL_MANAGER]}"}
    headers_warehouse = {"Authorization": f"Bearer {tokens[SystemRole.WAREHOUSE_PROCUREMENT]}"}
    headers_field = {"Authorization": f"Bearer {tokens[SystemRole.FIELD_TECHNICIAN]}"}
    headers_finance = {"Authorization": f"Bearer {tokens[SystemRole.FINANCE_ACCOUNTS]}"}
    headers_service = {"Authorization": f"Bearer {tokens[SystemRole.SERVICE_WARRANTY]}"}

    # =========================================================================
    # STAGE 1: CUSTOMER REGISTRATION, ENQUIRY & TECHNICAL SURVEY
    # =========================================================================
    # A. Register Customer
    cust_res = client.post(
        "/api/v1/customers",
        headers=headers_sales,
        json={
            "customer_type": "RESIDENTIAL",
            "full_name": f"Master Flow Customer {uid}",
            "phone": f"98765{uid[:5]}",
            "email": f"cust_{uid}@masterflow.com",
            "address": "42 Solar Boulevard, Cyber City",
            "city": "Pune",
            "state": "Maharashtra",
            "pincode": "411001",
            "sanctioned_load_kw": 5.0,
            "electricity_consumer_number": f"MSEB-{uid}",
        },
    )
    assert cust_res.status_code == 201, cust_res.text
    customer_id = cust_res.json()["data"]["id"]

    # B. Create Enquiry (5.0 kW On-Grid)
    enq_res = client.post(
        "/api/v1/enquiries",
        headers=headers_sales,
        json={
            "customer_id": customer_id,
            "source": "WEBSITE",
            "system_type": "ON_GRID",
            "proposed_capacity_kw": 5.0,
            "monthly_electricity_bill": 6500.0,
            "roof_type": "CONCRETE_FLAT",
            "notes": "Rooftop solar installation for residential bungalow.",
        },
    )
    assert enq_res.status_code == 201, enq_res.text
    enquiry_id = enq_res.json()["data"]["id"]

    # C. Schedule Site Survey
    survey_sched_res = client.post(
        "/api/v1/surveys",
        headers=headers_sales,
        json={
            "enquiry_id": enquiry_id,
            "surveyor_id": emp_ids[SystemRole.TECHNICAL_MANAGER],
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "remarks": "Site survey scheduled for residential rooftop assessment.",
        },
    )
    assert survey_sched_res.status_code == 201, survey_sched_res.text
    survey_id = survey_sched_res.json()["data"]["id"]

    # D. Conduct Survey & Update Findings
    survey_update_res = client.put(
        f"/api/v1/surveys/{survey_id}",
        headers=headers_tech,
        json={
            "conducted_at": datetime.now(timezone.utc).isoformat(),
            "roof_area_sqft": 650.0,
            "shadow_free_area_sqft": 550.0,
            "roof_orientation": "SOUTH",
            "roof_tilt_degrees": 15.0,
            "roof_structure_type": "ELEVATED",
            "existing_phase": "THREE_PHASE",
            "sanctioned_load_kw": 5.0,
            "gps_latitude": 18.5204,
            "gps_longitude": 73.8567,
            "technical_feasibility": "FEASIBLE",
            "remarks": "Optimal southern orientation, robust concrete slab.",
        },
    )
    assert survey_update_res.status_code == 200, survey_update_res.text

    # E. Surveyor submits survey for review
    survey_sub_res = client.put(f"/api/v1/surveys/{survey_id}/submit", headers=headers_tech)
    assert survey_sub_res.status_code == 200, survey_sub_res.text

    # F. Technical Manager reviews & approves Survey
    appr_res = client.post(
        f"/api/v1/surveys/{survey_id}/review",
        headers=headers_tech,
        json={
            "action": "APPROVED",
            "comments": "Site fully feasible for 5 kW solar installation.",
        },
    )
    assert appr_res.status_code == 200, appr_res.text

    # =========================================================================
    # STAGE 2: QUOTATION ENGINE — CREATE, SUBMIT, APPROVE, SEND & ACCEPT
    # =========================================================================
    quote_res = client.post(
        "/api/v1/quotations",
        headers=headers_sales,
        json={
            "enquiry_id": enquiry_id,
            "survey_id": survey_id,
            "system_type": "ON_GRID",
            "capacity_kw": 5.0,
            "installation_cost": 25000.0,
            "subsidy_estimate": 78000.0,
            "valid_until": str(date.today() + timedelta(days=30)),
            "items": [
                {
                    "product_id": products["inverter"],
                    "item_description": "SunPower Hybrid Inverter 5kW",
                    "quantity": 1,
                    "unit_price": 45000.0,
                    "discount_amount": 0.0,
                    "tax_rate_percent": 18.0,
                },
                {
                    "product_id": products["panel"],
                    "item_description": "SunPower Mono PERC Panel 550W",
                    "quantity": 9,
                    "unit_price": 14000.0,
                    "discount_amount": 0.0,
                    "tax_rate_percent": 12.0,
                },
                {
                    "product_id": products["cable"],
                    "item_description": "Solar DC Cable 4sqmm",
                    "quantity": 100,
                    "unit_price": 60.0,
                    "discount_amount": 0.0,
                    "tax_rate_percent": 18.0,
                },
            ],
        },
    )
    assert quote_res.status_code == 201, quote_res.text
    quotation_id = quote_res.json()["data"]["id"]

    # Submit quotation for review
    sub_res = client.post(f"/api/v1/quotations/{quotation_id}/submit", headers=headers_sales)
    assert sub_res.status_code == 200, sub_res.text

    # Super Admin approves quotation
    appr_q_res = client.post(f"/api/v1/quotations/{quotation_id}/approve", headers=headers_admin, json={"comments": "Approved pricing."})
    assert appr_q_res.status_code == 200, appr_q_res.text

    # Sales rep sends quotation to customer
    send_q_res = client.post(f"/api/v1/quotations/{quotation_id}/send", headers=headers_sales)
    assert send_q_res.status_code == 200, send_q_res.text

    # Accept quotation (authorized by Super Admin on customer's behalf)
    accept_res = client.post(
        f"/api/v1/quotations/{quotation_id}/accept",
        headers=headers_admin,
        json={"acceptance_notes": "Customer accepted via signed proposal form."},
    )
    assert accept_res.status_code == 200, accept_res.text

    # =========================================================================
    # STAGE 3: ORDER CONVERSION & AUTOMATIC PROJECT HANDOVER (PHASE 6)
    # =========================================================================
    order_res = client.post(
        "/api/v1/orders",
        headers=headers_admin,
        json={"quotation_id": quotation_id, "notes": "Confirmed solar order from accepted proposal."},
    )
    assert order_res.status_code == 201, order_res.text
    order_data = order_res.json()["data"]
    order_id = order_data["id"]
    assert order_data["status"] == "PENDING_ADVANCE"

    # Record Customer Advance Payment against order (transitions order to CONFIRMED)
    adv_res = client.post(
        f"/api/v1/orders/{order_id}/payments",
        headers=headers_finance,
        json={
            "amount": 50000.0,
            "payment_method": "NEFT",
            "transaction_reference": f"TXN-ADV-{uid}",
            "payment_date": str(date.today()),
            "notes": "Advance booking deposit 50,000 INR",
        },
    )
    assert adv_res.status_code in [200, 201], adv_res.text
    assert adv_res.json()["data"]["status"] == "CONFIRMED"

    # Handover Order to Project
    handover_res = client.post(
        f"/api/v1/projects/orders/{order_id}/handover",
        headers=headers_tech,
        json={
            "project_manager_id": emp_ids[SystemRole.TECHNICAL_MANAGER],
            "site_address": "42 Solar Boulevard, Cyber City, Pune",
            "planned_start_date": str(date.today()),
            "planned_completion_date": str(date.today() + timedelta(days=21)),
            "initial_notes": "Rooftop structure requires southern elevation tilt bracket",
        },
    )
    assert handover_res.status_code == 201, handover_res.text
    project_id = handover_res.json()["data"]["id"]

    # Verify Project BOM items exist
    with SessionLocal() as db:
        bom_items = db.execute(select(ProjectBomItem).where(ProjectBomItem.project_id == project_id)).scalars().all()
        assert len(bom_items) >= 2

    # =========================================================================
    # STAGE 4: PROCUREMENT PO & GOODS RECEIPT INWARD (PHASE 7 & 5.10)
    # =========================================================================
    # A. Get or Create Supplier
    with SessionLocal() as db:
        supp = db.execute(select(Supplier).where(Supplier.supplier_code == "SUP-E2E-MASTER")).scalar_one_or_none()
        if not supp:
            # Check by GST or pick first active
            supp = db.execute(select(Supplier).where(Supplier.gst_number == "27AAPCM1234F1Z5")).scalar_one_or_none()
        if not supp:
            try:
                supp = Supplier(
                    supplier_code="SUP-E2E-MASTER",
                    company_name="SunPower Master OEM Supplier",
                    gst_number="27AAPCM1234F1Z5",
                    pan_number="AAPCM1234F",
                    contact_person="Ramesh Patel",
                    email="oem_master@supplier.com",
                    phone="9823456789",
                    address="Industrial Phase 2, Chakan",
                    city="Pune",
                    state="Maharashtra",
                    is_active=True,
                )
                db.add(supp)
                db.commit()
                db.refresh(supp)
            except Exception:
                db.rollback()
                supp = db.execute(select(Supplier).where(Supplier.is_active == True)).scalars().first()
        supplier_id = supp.id

    # B. Create Purchase Order
    po_res = client.post(
        "/api/v1/purchase-orders",
        headers=headers_warehouse,
        json={
            "supplier_id": supplier_id,
            "expected_delivery_date": str(date.today() + timedelta(days=7)),
            "notes": "Procurement for master E2E project stock.",
            "items": [
                {
                    "product_id": products["inverter"],
                    "ordered_quantity": 2,
                    "unit_price": 40000.0,
                    "tax_rate_percent": 18.0,
                },
                {
                    "product_id": products["cable"],
                    "ordered_quantity": 200,
                    "unit_price": 50.0,
                    "tax_rate_percent": 18.0,
                },
            ],
        },
    )
    assert po_res.status_code == 201, po_res.text
    po_data = po_res.json()["data"]
    po_id = po_data["id"]
    po_item_inverter_id = po_data["items"][0]["id"]
    po_item_cable_id = po_data["items"][1]["id"]

    # C. Issue Purchase Order
    issue_po_res = client.post(
        f"/api/v1/purchase-orders/{po_id}/issue",
        headers=headers_warehouse,
    )
    assert issue_po_res.status_code == 200, issue_po_res.text

    # D. Inward Goods Receipt (GRN) with Serial Numbers
    inv_serial_1 = f"SN-INV-A-{uid}"
    inv_serial_2 = f"SN-INV-B-{uid}"
    grn_res = client.post(
        "/api/v1/goods-receipts",
        headers=headers_warehouse,
        json={
            "purchase_order_id": po_id,
            "received_date": str(date.today()),
            "challan_number": f"DC-{uid}",
            "challan_date": str(date.today()),
            "inspection_remarks": "Flawless inward inspection.",
            "items": [
                {
                    "po_item_id": po_item_inverter_id,
                    "product_id": products["inverter"],
                    "received_quantity": 2,
                    "accepted_quantity": 2,
                    "rejected_quantity": 0,
                    "serial_numbers": [inv_serial_1, inv_serial_2],
                },
                {
                    "po_item_id": po_item_cable_id,
                    "product_id": products["cable"],
                    "received_quantity": 200,
                    "accepted_quantity": 200,
                    "rejected_quantity": 0,
                    "serial_numbers": [],
                },
            ],
        },
    )
    assert grn_res.status_code == 201, grn_res.text

    # =========================================================================
    # STAGE 5: MATERIAL DISPATCH & SERIAL NUMBER TRACKING (PHASE 8)
    # =========================================================================
    with SessionLocal() as db:
        sn_record = db.execute(select(SerialNumber).where(SerialNumber.serial_number == inv_serial_1)).scalar_one()
        sn_id_1 = sn_record.id
        sn_record_2 = db.execute(select(SerialNumber).where(SerialNumber.serial_number == inv_serial_2)).scalar_one()
        sn_id_2 = sn_record_2.id

    # Create Dispatch
    disp_res = client.post(
        "/api/v1/dispatch",
        headers=headers_warehouse,
        json={
            "project_id": project_id,
            "order_id": order_id,
            "dispatched_date": str(date.today()),
            "vehicle_number": "MH-12-SP-8822",
            "driver_name": "Suresh Shinde",
            "driver_phone": "9811223344",
            "tracking_number": f"TRK-{uid}",
            "remarks": "Complete material dispatch for site installation.",
            "items": [
                {
                    "product_id": products["inverter"],
                    "dispatched_quantity": 1,
                    "serial_number_ids": [sn_id_1],
                },
                {
                    "product_id": products["cable"],
                    "dispatched_quantity": 100,
                    "serial_number_ids": [],
                },
            ],
        },
    )
    assert disp_res.status_code == 201, disp_res.text
    dispatch_id = disp_res.json()["data"]["id"]

    # Ship Dispatch
    ship_res = client.patch(
        f"/api/v1/dispatch/{dispatch_id}/status",
        headers=headers_warehouse,
        json={"dispatch_status": "DISPATCHED"},
    )
    assert ship_res.status_code == 200, ship_res.text

    # Deliver Dispatch
    deliver_res = client.post(
        f"/api/v1/dispatch/{dispatch_id}/confirm",
        headers=headers_warehouse,
        json={
            "confirmation_type": "CUSTOMER_SIGN",
            "recipient_name": f"Master Flow Customer {uid}",
            "recipient_phone": f"98765{uid[:5]}",
            "delivery_notes": "Delivered in perfect boxed condition.",
        },
    )
    assert deliver_res.status_code == 200, deliver_res.text

    # =========================================================================
    # STAGE 6: INSTALLATION SCHEDULING, WORKLOG, TESTING & COMPLETION (PHASE 9)
    # =========================================================================
    # A. Schedule Installation
    sched_res = client.post(
        "/api/v1/installations/schedules",
        headers=headers_tech,
        json={
            "project_id": project_id,
            "scheduled_start_date": str(date.today()),
            "scheduled_end_date": str(date.today() + timedelta(days=2)),
            "lead_technician_id": emp_ids[SystemRole.FIELD_TECHNICIAN],
            "technician_ids": [emp_ids[SystemRole.FIELD_TECHNICIAN]],
            "notes": "Residential solar commissioning schedule.",
        },
    )
    assert sched_res.status_code == 201, sched_res.text
    schedule_id = sched_res.json()["data"]["id"]

    # B. Record Installation Execution
    inst_res = client.post(
        "/api/v1/installations",
        headers=headers_field,
        json={
            "project_id": project_id,
            "schedule_id": schedule_id,
            "lead_technician_id": emp_ids[SystemRole.FIELD_TECHNICIAN],
            "system_capacity_kw": 5.0,
            "inverter_make_model": "SunPower Hybrid Inverter 5kW",
            "total_panels_installed": 9,
            "structure_type": "GALVANIZED_IRON_ELEVATED",
            "installation_date": str(date.today()),
            "technician_notes": "Roof structure mounted, modules clamped and wired.",
        },
    )
    assert inst_res.status_code == 201, inst_res.text
    installation_id = inst_res.json()["data"]["id"]

    # C. Submit Technician Worklog
    worklog_res = client.post(
        f"/api/v1/installations/{installation_id}/worklogs",
        headers=headers_field,
        json={
            "employee_id": emp_ids[SystemRole.FIELD_TECHNICIAN],
            "work_date": str(date.today()),
            "hours_worked": 8.0,
            "work_description": "Mounted structure, ran DC conduit, interconnected panels.",
        },
    )
    assert worklog_res.status_code == 201, worklog_res.text

    # D. Submit Quality Checklist
    chk_res = client.post(
        f"/api/v1/installations/{installation_id}/checklists",
        headers=headers_field,
        json={
            "checklist_item": "Earthing pit resistance and array isolation test",
            "category": "ELECTRICAL",
            "is_checked": True,
            "remarks": "Measured earthing at 1.8 Ohms, well within IEEE standards.",
        },
    )
    assert chk_res.status_code == 201, chk_res.text

    # E. Submit Electrical Commissioning Test (Voc, Isc, Earthing)
    test_res = client.post(
        f"/api/v1/installations/{installation_id}/tests",
        headers=headers_field,
        json={
            "test_name": "VOC_TEST",
            "standard_value": "450V",
            "measured_value": "442V",
            "unit_of_measure": "Volts",
            "is_passed": True,
            "tested_by": emp_ids[SystemRole.FIELD_TECHNICIAN],
            "test_date": str(date.today()),
            "remarks": "String Voc confirmed balanced across both MPPTs.",
        },
    )
    assert test_res.status_code == 201, test_res.text

    # F. Complete Installation
    comp_res = client.patch(
        f"/api/v1/installations/{installation_id}/status",
        headers=headers_tech,
        json={"status": "COMPLETED"},
    )
    assert comp_res.status_code == 200, comp_res.text

    # =========================================================================
    # STAGE 7: MILESTONE INVOICING & CASH COLLECTIONS (PHASE 5.8 & 10)
    # =========================================================================
    # Generate Final Tax Invoice
    # A. Issue Final Invoice against Order & Project
    order_chk = client.get(f"/api/v1/orders/{order_id}", headers=headers_sales).json()["data"]
    order_balance = Decimal(str(order_chk["balance_amount"]))

    inv_res = client.post(
        "/api/v1/invoices",
        headers=headers_finance,
        json={
            "order_id": order_id,
            "project_id": project_id,
            "invoice_type": "FINAL",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=15)),
            "notes": "Final settlement invoice on completed solar installation.",
            "items": [
                {
                    "product_id": products["inverter"],
                    "item_description": "SunPower Hybrid Inverter 5kW E2E - Final Balance",
                    "quantity": 1,
                    "unit_price": float(order_balance),
                    "tax_rate_percent": 0.0,
                }
            ],
        },
    )
    assert inv_res.status_code == 201, inv_res.text
    invoice_data = inv_res.json()["data"]
    invoice_id = invoice_data["id"]
    invoice_total = Decimal(str(invoice_data["total_amount"]))

    # Record Direct Customer Payment against this invoice
    pay_res = client.post(
        f"/api/v1/invoices/{invoice_id}/payments",
        headers=headers_finance,
        json={
            "amount": float(invoice_total),
            "payment_method": "NEFT",
            "transaction_reference": f"TXN-INV-{uid}",
            "payment_date": str(date.today()),
            "notes": "Full balance payment via NEFT.",
        },
    )
    assert pay_res.status_code in [200, 201], pay_res.text

    # Verify Invoice is now fully PAID
    inv_verify = client.get(f"/api/v1/invoices/{invoice_id}", headers=headers_finance)
    assert inv_verify.status_code == 200
    assert inv_verify.json()["data"]["payment_status"] == "PAID"
    assert Decimal(str(inv_verify.json()["data"]["balance_amount"])) == Decimal("0.00")

    # =========================================================================
    # STAGE 8: SUPPLIER ACCOUNTS PAYABLE & PROFITABILITY (PHASE 10)
    # =========================================================================
    # A. Record Supplier Bill / Invoice
    supp_inv_res = client.post(
        "/api/v1/supplier-invoices",
        headers=headers_finance,
        json={
            "purchase_order_id": po_id,
            "supplier_id": supplier_id,
            "invoice_number": f"SUP-INV-{uid}",
            "invoice_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=30)),
            "subtotal": 85000.0,
            "tax_amount": 15300.0,
            "total_amount": 100300.0,
            "notes": "Supplier bill for inverters and DC cabling.",
        },
    )
    assert supp_inv_res.status_code == 201, supp_inv_res.text
    supp_invoice_id = supp_inv_res.json()["data"]["id"]

    # B. Record Supplier Disbursement Payment
    supp_pay_res = client.post(
        "/api/v1/supplier-payments",
        headers=headers_finance,
        json={
            "supplier_id": supplier_id,
            "amount": 100300.0,
            "payment_mode": "RTGS",
            "reference_number": f"RTGS-SUP-{uid}",
            "payment_date": str(date.today()),
            "notes": "Settlement of supplier invoice via corporate banking.",
        },
    )
    assert supp_pay_res.status_code == 201, supp_pay_res.text
    supp_payment_id = supp_pay_res.json()["data"]["id"]

    # C. Allocate Payment to Supplier Invoice
    supp_alloc_res = client.post(
        f"/api/v1/supplier-invoices/{supp_invoice_id}/allocations",
        headers=headers_finance,
        json={
            "supplier_payment_id": supp_payment_id,
            "allocated_amount": 100300.0,
        },
    )
    assert supp_alloc_res.status_code == 201, supp_alloc_res.text

    # D. Verify Realized Project Profitability
    profit_res = client.get(f"/api/v1/projects/{project_id}/profitability", headers=headers_finance)
    assert profit_res.status_code == 200, profit_res.text
    profit_data = profit_res.json()["data"]
    assert "contract_amount" in profit_data
    assert "gross_profit" in profit_data
    assert "gross_margin_percentage" in profit_data

    # =========================================================================
    # STAGE 9: WARRANTY REGISTRATION, SERVICE TICKET & REPLACEMENT (PHASE 11)
    # =========================================================================
    # A. Register Warranty for Project Serialized Equipment
    warr_res = client.post(
        f"/api/v1/projects/{project_id}/warranty-register",
        headers=headers_service,
        json={"activation_date": str(date.today())},
    )
    assert warr_res.status_code == 201, warr_res.text
    warranty_records = warr_res.json()["data"]
    warranty_record_id = warranty_records[0]["id"] if warranty_records else None

    # B. Raise Service Ticket (Inverter Underperformance)
    ticket_res = client.post(
        "/api/v1/service-tickets",
        headers=headers_service,
        json={
            "project_id": project_id,
            "customer_id": customer_id,
            "serial_number_id": sn_id_1,
            "warranty_record_id": warranty_record_id,
            "issue_category": "INVERTER_FAULT",
            "priority": "HIGH",
            "description": "Inverter displays error code E-04 (Grid Overvoltage).",
        },
    )
    assert ticket_res.status_code == 201, ticket_res.text
    ticket_id = ticket_res.json()["data"]["id"]

    # C. Schedule Service Visit
    visit_res = client.post(
        f"/api/v1/service-tickets/{ticket_id}/visits",
        headers=headers_service,
        json={
            "technician_id": emp_ids[SystemRole.FIELD_TECHNICIAN],
            "scheduled_date": str(date.today()),
        },
    )
    assert visit_res.status_code == 201, visit_res.text
    visit_id = visit_res.json()["data"]["id"]

    # Complete Service Visit
    comp_visit_res = client.patch(
        f"/api/v1/service-visits/{visit_id}/complete",
        headers=headers_service,
        json={
            "actual_start": datetime.now(timezone.utc).isoformat(),
            "actual_end": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            "findings": "Internal control board damaged due to lightning surge.",
            "action_taken": "Replaced faulty inverter under manufacturer warranty.",
        },
    )
    assert comp_visit_res.status_code == 200, comp_visit_res.text

    # D. Execute Warranty Replacement with In-Stock Serial #2
    repl_res = client.post(
        f"/api/v1/service-tickets/{ticket_id}/replacements",
        headers=headers_service,
        json={
            "original_serial_id": sn_id_1,
            "replacement_serial_id": sn_id_2,
            "replacement_reason": "Control board burned, swapped with warranty reserve unit.",
            "replacement_date": str(date.today()),
            "replaced_by": emp_ids[SystemRole.FIELD_TECHNICIAN],
        },
    )
    assert repl_res.status_code == 201, repl_res.text

    # E. Customer Confirmation & 5-Star Feedback
    confirm_res = client.post(
        f"/api/v1/service-tickets/{ticket_id}/confirm",
        headers=headers_service,
        json={
            "customer_id": customer_id,
            "resolution_confirmed": True,
            "customer_rating": 5,
            "customer_feedback": "Fast resolution and courteous technical team!",
            "confirmation_channel": "PORTAL",
        },
    )
    assert confirm_res.status_code == 201, confirm_res.text

    # =========================================================================
    # STAGE 10: PM SURYA GHAR SUBSIDY & DBT DISBURSEMENT (PHASE 12)
    # =========================================================================
    # A. Submit Subsidy Application (5 kW => Capped at 78,000 INR)
    sub_res = client.post(
        "/api/v1/subsidy/applications",
        headers=headers_tech,
        json={
            "project_id": project_id,
            "customer_id": customer_id,
            "discom_name": "Maharashtra State Electricity Distribution Co. (MSEDCL)",
            "sanctioned_capacity_kw": 5.0,
            "portal_registration_number": f"PMSG-{uid}-5KW",
            "application_date": str(date.today()),
        },
    )
    assert sub_res.status_code == 201, sub_res.text
    subsidy_data = sub_res.json()["data"]
    subsidy_id = subsidy_data["id"]
    assert Decimal(str(subsidy_data["eligible_subsidy_amount"])) == Decimal("78000.00")

    # B. Attach Verified Compliance Document
    doc_res = client.post(
        f"/api/v1/subsidy/applications/{subsidy_id}/documents",
        headers=headers_tech,
        json={
            "document_type": "JOINT_INSPECTION_REPORT",
            "file_name": "Joint_Inspection_Report.pdf",
            "remarks": "DISCOM official joint inspection report signed.",
        },
    )
    assert doc_res.status_code == 201, doc_res.text

    # C. Transition through DISCOM Stages to APPROVED
    for next_st in ["SUBMITTED_TO_DISCOM", "INSPECTION_COMPLETED", "APPROVED"]:
        st_res = client.patch(
            f"/api/v1/subsidy/applications/{subsidy_id}/status",
            headers=headers_tech,
            json={"status": next_st, "comments": f"Progression to {next_st} verified."},
        )
        assert st_res.status_code == 200, st_res.text

    # D. Record Government DBT Subsidy Disbursement
    disb_res = client.post(
        f"/api/v1/subsidy/applications/{subsidy_id}/disbursements",
        headers=headers_tech,
        json={
            "project_id": project_id,
            "disbursed_amount": 78000.0,
            "disbursement_date": str(date.today()),
            "bank_reference_number": f"DBT-MSEDCL-{uid}",
            "payment_reference": f"SUBPAY-{uid}",
        },
    )
    assert disb_res.status_code == 201, disb_res.text

    # =========================================================================
    # STAGE 11: OPERATIONAL WORKFLOW ANALYTICS & EXECUTIVE RECONCILIATION (PHASE 13)
    # =========================================================================
    ops_res = client.get("/api/v1/analytics/operations", headers=headers_admin)
    assert ops_res.status_code == 200, ops_res.text
    ops_data = ops_res.json()["data"]

    # Verify all subsystems reported live data
    assert ops_data["procurement"]["total_purchase_orders"] >= 1
    assert ops_data["dispatch"]["total_dispatches"] >= 1
    assert ops_data["installation"]["completed_installations"] >= 1
    assert ops_data["service_warranty"]["technician_visits_completed"] >= 1
    assert ops_data["service_warranty"]["components_replaced_count"] >= 1
    assert ops_data["subsidy"]["disbursed_applications"] >= 1
    assert Decimal(str(ops_data["subsidy"]["total_subsidy_disbursed"])) >= Decimal("78000.00")

    # Verify Executive KPI Dashboard runs smoothly
    exec_res = client.get("/api/v1/analytics/executive", headers=headers_admin)
    assert exec_res.status_code == 200, exec_res.text
    exec_data = exec_res.json()["data"]
    assert "enquiries" in exec_data
    assert "orders" in exec_data
    assert "projects" in exec_data
    assert "finance" in exec_data
