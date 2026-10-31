from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.auth import Role, Permission, RolePermission, Department, Skill
from app.utils.roles import SystemRole, ROLE_METADATA
import logging

logger = logging.getLogger(__name__)

# Granular permissions grouped by business module
DEFINED_PERMISSIONS = [
    # Module: auth & administration
    ("users.read", "auth", "View system users and their profiles"),
    ("users.manage", "auth", "Create, update, activate or deactivate users"),
    ("roles.read", "auth", "View system roles and permissions"),
    ("roles.manage", "auth", "Manage roles and permission allocations"),
    ("employees.read", "auth", "View employee profiles and skills"),
    ("employees.manage", "auth", "Manage employee records, skills and certifications"),
    ("departments.read", "auth", "View company departments and rosters"),
    ("departments.manage", "auth", "Manage company departments and managers"),
    ("skills.read", "auth", "View technical skills and catalog"),
    ("skills.manage", "auth", "Manage technical skills and employee assignments"),
    ("certifications.read", "auth", "View employee certifications and expiry tracking"),
    ("certifications.manage", "auth", "Manage employee certifications and verification"),

    # Module: crm & sales
    ("customers.read", "crm", "View customer contact and electricity meter details"),
    ("customers.create", "crm", "Register new customers in the system"),
    ("customers.update", "crm", "Update existing customer details"),
    ("enquiries.read", "crm", "View customer enquiries and lead status"),
    ("enquiries.create", "crm", "Record new customer enquiries"),
    ("enquiries.update", "crm", "Update enquiry notes and sales stage"),
    ("followups.manage", "crm", "Schedule and record customer sales followups"),
    ("surveys.read", "crm", "View rooftop site survey reports and measurements"),
    ("surveys.create", "crm", "Submit rooftop site survey data and photos"),
    ("surveys.update", "crm", "Update survey observations"),
    ("surveys.approve", "crm", "Approve, reject or request corrections for site surveys"),
    ("quotations.read", "crm", "View solar project quotations"),
    ("quotations.create", "crm", "Generate quotation estimates and calculate subsidies"),
    ("quotations.update", "crm", "Revise quotation pricing and BOM items"),
    ("quotations.approve", "crm", "Finalize and approve quotations for customer dispatch"),

    # Module: projects & procurement
    ("orders.read", "projects", "View confirmed solar orders and payment terms"),
    ("orders.create", "projects", "Convert accepted quotations into customer orders"),
    ("orders.update", "projects", "Update order status and contract milestones"),
    ("projects.read", "projects", "View solar rooftop project milestones and status"),
    ("projects.create", "projects", "Initialize rooftop execution projects"),
    ("projects.update", "projects", "Manage project lifecycle, dates and notes"),
    ("bom.read", "projects", "View standard and project-specific BOM items"),
    ("bom.manage", "projects", "Configure and customize project Bill of Materials"),
    ("suppliers.manage", "procurement", "Manage equipment vendors and manufacturers"),
    ("procurement.read", "procurement", "View purchase orders and goods receipt notes"),
    ("procurement.manage", "procurement", "Issue POs and process inward goods receipts"),

    # Module: inventory & dispatch
    ("inventory.read", "inventory", "View warehouse stock levels and reorder alerts"),
    ("inventory.manage", "inventory", "Perform stock adjustments, reservations and ledger entries"),
    ("serials.read", "inventory", "Track component serial numbers and lifecycle status"),
    ("serials.manage", "inventory", "Scan, register, and update serialized panels and inverters"),
    ("dispatch.read", "inventory", "View transport dispatch notes and driver details"),
    ("dispatch.create", "inventory", "Prepare and authorize material dispatch gate passes"),
    ("dispatch.confirm", "inventory", "Confirm on-site material delivery and recipient receipt"),

    # Module: installation management
    ("schedules.read", "installations", "View installation calendars and team rosters"),
    ("schedules.manage", "installations", "Schedule installation teams and dates"),
    ("installations.read", "installations", "View physical rooftop installation records"),
    ("installations.manage", "installations", "Supervise installation progress and lead technician signoff"),
    ("checklists.submit", "installations", "Submit civil, electrical and safety checklists"),
    ("checklists.verify", "installations", "Verify quality and safety compliance"),
    ("tests.submit", "installations", "Record electrical test results (Voc, Isc, Earth, Grid sync)"),
    ("consumption.manage", "installations", "Record actual physical material consumption"),
    ("acceptances.manage", "installations", "Record and verify final customer handoff acceptance"),

    # Module: finance & accounts
    ("finance.read", "finance", "View financial summaries and cost accounting"),
    ("payments.read", "finance", "View customer payment receipts and allocations"),
    ("payments.record", "finance", "Record customer payments and milestone collections"),
    ("invoices.read", "finance", "View customer milestone and final tax invoices"),
    ("invoices.create", "finance", "Generate advance, dispatch, and commissioning invoices"),
    ("expenses.manage", "finance", "Submit, approve and reimburse site and travel expenses"),
    ("technician_payments.manage", "finance", "Process technician commission and labor disbursements"),
    ("costs.read", "finance", "Review consolidated project job costing and margins"),

    # Module: warranty & service
    ("warranty.read", "warranty", "View equipment warranty policies and certificates"),
    ("warranty.manage", "warranty", "Configure warranty policies and process activations"),
    ("tickets.read", "warranty", "View customer service and repair tickets"),
    ("tickets.create", "warranty", "Log customer maintenance and breakdown tickets"),
    ("tickets.manage", "warranty", "Assign, update and resolve service tickets"),
    ("visits.manage", "warranty", "Conduct field maintenance visits and diagnostics"),
    ("replacements.manage", "warranty", "Authorize and record warranty component replacements"),

    # Module: subsidies
    ("subsidies.read", "subsidy", "View government DBT subsidy applications"),
    ("subsidies.create", "subsidy", "Prepare and submit discom subsidy documentation"),
    ("subsidies.manage", "subsidy", "Track inspection milestones and record subsidy disbursements"),

    # Module: workflow & monitoring
    ("tasks.read", "workflow", "View assigned tasks and project deadlines"),
    ("tasks.manage", "workflow", "Create, assign and escalate operational tasks"),
    ("escalations.manage", "workflow", "Handle management escalations and SLA breaches"),
    ("audit.read", "workflow", "Inspect security audit logs and system change history"),
    ("reports.read", "workflow", "Access executive and analytical operational reports"),
]


# Role to permission mapping based on business responsibilities
ROLE_PERMISSION_MATRIX: Dict[str, List[str]] = {
    # 1. SUPER_ADMIN: Universal access
    SystemRole.SUPER_ADMIN: [p[0] for p in DEFINED_PERMISSIONS],

    # 2. DIRECTOR: Executive oversight, approvals, financial/operational reporting
    SystemRole.DIRECTOR: [
        "users.read", "employees.read", "departments.read", "skills.read", "certifications.read",
        "customers.read", "enquiries.read", "surveys.read",
        "quotations.read", "quotations.approve", "orders.read", "projects.read", "bom.read",
        "procurement.read", "inventory.read", "serials.read", "dispatch.read",
        "installations.read", "finance.read", "payments.read", "invoices.read",
        "expenses.manage", "costs.read", "warranty.read", "tickets.read",
        "subsidies.read", "tasks.read", "escalations.manage", "audit.read", "reports.read",
    ],

    # 3. SALES: Leads, enquiries, surveys, proposals, quotations
    SystemRole.SALES: [
        "customers.read", "customers.create", "customers.update",
        "enquiries.read", "enquiries.create", "enquiries.update",
        "followups.manage", "surveys.read",
        "quotations.read", "quotations.create", "quotations.update",
        "orders.read", "projects.read", "tasks.read", "reports.read",
    ],

    # 4. TECHNICAL_MANAGER: Feasibility, survey approvals, BOM, work orders, commissioning
    SystemRole.TECHNICAL_MANAGER: [
        "employees.read", "departments.read", "skills.read", "skills.manage", "certifications.read", "certifications.manage",
        "customers.read", "enquiries.read", "surveys.read", "surveys.approve",
        "quotations.read", "quotations.approve", "orders.read", "projects.read", "projects.create", "projects.update",
        "bom.read", "bom.manage", "procurement.read", "inventory.read", "serials.read",
        "schedules.read", "schedules.manage", "installations.read", "installations.manage",
        "checklists.verify", "consumption.manage", "acceptances.manage", "warranty.read",
        "tasks.read", "tasks.manage", "escalations.manage",
    ],

    # 5. WAREHOUSE_PROCUREMENT: Stock, serials, dispatches, POs, vendors
    SystemRole.WAREHOUSE_PROCUREMENT: [
        "products.read" if False else "bom.read",
        "suppliers.manage", "procurement.read", "procurement.manage",
        "inventory.read", "inventory.manage",
        "serials.read", "serials.manage",
        "dispatch.read", "dispatch.create", "dispatch.confirm",
        "projects.read", "tasks.read",
    ],

    # 6. FIELD_TECHNICIAN: Mobile survey, installation, checklists, tests
    SystemRole.FIELD_TECHNICIAN: [
        "customers.read", "surveys.read", "surveys.create", "surveys.update",
        "projects.read", "schedules.read", "installations.read",
        "checklists.submit", "tests.submit", "consumption.manage",
        "serials.read", "tasks.read",
    ],

    # 7. SERVICE_WARRANTY: Maintenance tickets, visits, replacements, claims
    SystemRole.SERVICE_WARRANTY: [
        "customers.read", "projects.read", "serials.read",
        "warranty.read", "warranty.manage",
        "tickets.read", "tickets.create", "tickets.manage",
        "visits.manage", "replacements.manage", "tasks.read",
    ],

    # 8. FINANCE_ACCOUNTS: Invoices, receipts, expenses, subsidy disbursements
    SystemRole.FINANCE_ACCOUNTS: [
        "customers.read", "orders.read", "projects.read",
        "finance.read", "payments.read", "payments.record",
        "invoices.read", "invoices.create",
        "expenses.manage", "technician_payments.manage", "costs.read",
        "subsidies.read", "subsidies.manage", "reports.read",
    ],

    # 9. CUSTOMER: Restricted strictly to own project, documents and feedback
    SystemRole.CUSTOMER: [
        "customers.read", "quotations.read", "orders.read", "projects.read",
        "installations.read", "invoices.read", "payments.read",
        "warranty.read", "tickets.create", "tickets.read", "acceptances.manage",
    ],
}


def seed_reference_data(db: Session) -> Dict[str, int]:
    """
    Idempotently seed the 9 canonical system roles, granular permissions,
    and role-permission mappings.
    Returns counts of inserted items.
    """
    roles_created = 0
    perms_created = 0
    mappings_created = 0

    # 1. Seed the 9 System Roles
    role_map: Dict[str, Role] = {}
    for canonical_slug in SystemRole.ALL_ROLES:
        meta = ROLE_METADATA[canonical_slug]
        existing = db.execute(
            select(Role).where(Role.slug == canonical_slug)
        ).scalar_one_or_none()

        if not existing:
            role = Role(
                name=meta["name"],
                slug=canonical_slug,
                description=meta["description"],
                is_system_role=True,
            )
            db.add(role)
            db.flush()
            role_map[canonical_slug] = role
            roles_created += 1
            logger.info(f"Seeded role: {canonical_slug} ({meta['name']})")
        else:
            role_map[canonical_slug] = existing

    # 2. Seed Granular Permissions
    perm_map: Dict[str, Permission] = {}
    for code, module, desc in DEFINED_PERMISSIONS:
        existing_perm = db.execute(
            select(Permission).where(Permission.code == code)
        ).scalar_one_or_none()

        if not existing_perm:
            perm = Permission(
                name=code.replace(".", " ").title(),
                code=code,
                module=module,
                description=desc,
            )
            db.add(perm)
            db.flush()
            perm_map[code] = perm
            perms_created += 1
        else:
            perm_map[code] = existing_perm

    # 3. Seed Role-Permission Mappings
    for role_slug, perm_codes in ROLE_PERMISSION_MATRIX.items():
        role = role_map[role_slug]
        for p_code in perm_codes:
            if p_code not in perm_map:
                continue
            perm = perm_map[p_code]

            existing_mapping = db.execute(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id,
                )
            ).scalar_one_or_none()

            if not existing_mapping:
                mapping = RolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                )
                db.add(mapping)
                mappings_created += 1

    # 4. Seed Reference Skills (Solar & Technical)
    STANDARD_SKILLS = [
        ("Solar Panel Installation", "MOUNTING", "Mounting and structural alignment of photovoltaic solar modules on rooftops"),
        ("Electrical Wiring", "ELECTRICAL", "AC and DC cable routing, conduit laying, and junction box termination"),
        ("Inverter Installation", "ELECTRICAL", "String and micro-inverter mounting, grid connection, and anti-islanding setup"),
        ("Battery Installation", "STORAGE", "Lithium-ion/lead-acid solar battery bank rack setup, BMS calibration, and wiring"),
        ("Electrical Testing", "TESTING", "Open circuit voltage (Voc), short circuit current (Isc), insulation resistance, and earthing earth-resistance testing"),
        ("Site Survey", "SURVEY", "Roof structural assessment, azimuth and tilt measurement, shadow profiling, and 3D modeling"),
        ("System Commissioning", "COMMISSIONING", "Final end-to-end grid synchronization, discom net-metering tests, and customer handoff"),
        ("Troubleshooting", "MAINTENANCE", "Fault diagnostics, thermal imaging hotspot detection, and degraded panel troubleshooting"),
        ("Customer Service", "SERVICE", "Customer orientation, mobile app monitoring tutorial, and warranty onboarding"),
        ("Safety Compliance", "SAFETY", "Fall protection harness usage, working at heights safety, PPE compliance, and OSHA standards"),
    ]
    skills_created = 0
    for s_name, s_cat, s_desc in STANDARD_SKILLS:
        existing_skill = db.execute(select(Skill).where(Skill.name == s_name)).scalar_one_or_none()
        if not existing_skill:
            skill = Skill(name=s_name, category=s_cat, description=s_desc, is_active=True)
            db.add(skill)
            skills_created += 1

    # 5. Seed Core Departments
    CORE_DEPARTMENTS = [
        ("Engineering & Technical Operations", "TECH"),
        ("Field Installation & Commissioning", "FIELD"),
        ("Sales & Customer Relations", "SALES"),
        ("Warehouse & Procurement", "PROC"),
        ("Finance & Accounts", "FIN"),
        ("Service & Warranty Support", "SERV"),
    ]
    depts_created = 0
    for d_name, d_code in CORE_DEPARTMENTS:
        existing_dept = db.execute(select(Department).where(Department.code == d_code)).scalar_one_or_none()
        if not existing_dept:
            dept = Department(name=d_name, code=d_code, is_active=True)
            db.add(dept)
            depts_created += 1

    db.commit()
    logger.info(
        f"Seeding completed: {roles_created} roles created, "
        f"{perms_created} permissions created, {mappings_created} mappings created, "
        f"{skills_created} skills created, {depts_created} departments created."
    )

    return {
        "roles_created": roles_created,
        "permissions_created": perms_created,
        "mappings_created": mappings_created,
        "skills_created": skills_created,
        "departments_created": depts_created,
        "total_canonical_roles": len(SystemRole.ALL_ROLES),
        "total_permissions": len(DEFINED_PERMISSIONS),
    }

