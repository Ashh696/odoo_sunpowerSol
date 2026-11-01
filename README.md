# SunPower Solutions — Solar Installation Management System (SIMS)

**SIMS (Solar Installation Management System)** is an enterprise ERP and operational execution platform engineered for **SunPower Solutions** to govern the complete end-to-end lifecycle of rooftop, commercial, and industrial solar installations in India.

The platform coordinates lead capture, engineering roof feasibility surveys, dynamic Bill of Materials (BOM) design, quotation engineering with statutory PM Surya Ghar subsidy calculations, order conversion, milestone-based project management, serialized inventory ledger tracking, procurement with Goods Receipt Notes (GRN), multi-stage on-site installation checklists, customer milestone tax invoicing, Accounts Payable matching, DISCOM net-metering compliance, and post-commissioning warranty/AMC ticketing.

---

## 1. Executive Summary & Key Capabilities

- **12-Stage Unified Operational Lifecycle**: Seamlessly transitions projects across twelve operational stages: Lead Intake $\rightarrow$ Technical Rooftop Survey $\rightarrow$ System BOM & Pricing $\rightarrow$ Multi-Tier Quotation $\rightarrow$ Sales Order $\rightarrow$ Project Handover & Milestone Tracking $\rightarrow$ Procurement (PO & GRN) $\rightarrow$ Serialized Dispatch $\rightarrow$ Multi-Stage Installation & Commissioning QA $\rightarrow$ Milestone Invoicing & Payment Allocation $\rightarrow$ Statutory Subsidy & DISCOM Net-Metering $\rightarrow$ Post-Commissioning Warranty & Service.
- **Strict Role-Based Access Control (RBAC)**: 9 canonical roles (`SUPER_ADMIN`, `DIRECTOR`, `SALES`, `TECHNICAL_MANAGER`, `WAREHOUSE_PROCUREMENT`, `FIELD_TECHNICIAN`, `SERVICE_WARRANTY`, `FINANCE_ACCOUNTS`, `CUSTOMER`) enforced across 77 fine-grained permissions.
- **Double-Entry Style Stock Movements & Serialized Assets**: Complete stock movements (`PO_RECEIPT`, `DISPATCH`, `RETURN`, `ADJUSTMENT`) with real-time weighted moving average unit costing and unit-level serial number state tracking (`IN_STOCK`, `DISPATCHED`, `INSTALLED`, `RETURNED`).
- **Comprehensive Financial Governance**: Real-time project profitability tracking (revenue vs. actual hardware, procurement, and labor expenses), milestone-based customer invoicing with over-billing prevention, supplier Accounts Payable (AP) invoices with 3-way matching, and payment allocation.
- **Statutory PM Surya Ghar Subsidy Engine**: Automated subsidy policy calculation compliant with MNRE / PM Surya Ghar Yojana residential capacity slabs, with mandatory audit reason logging for manual overrides.
- **Quality Assurance & Traceability**: On-site checklists for civil works, module arrays, inverter wiring, earthing pit resistance ($\Omega$), and grid-sync commissioning, with technician sign-offs and audit logs.

---

## 2. Technology Stack & Verified Versions

All versions have been directly verified against active workspace manifests and running environments:

| Tier | Technology / Library | Verified Version | Purpose / Description |
| :--- | :--- | :--- | :--- |
| **Backend Runtime** | Python | `3.12.0` | Asynchronous core backend runtime |
| **Backend Framework** | FastAPI | `0.115.0` | Asynchronous REST API framework with OpenAPI documentation |
| **ASGI Web Server** | Uvicorn | `0.30.6` | Asynchronous web server |
| **ORM / Data Access** | SQLAlchemy | `2.0.36` | Modern SQLAlchemy 2.0 ORM with declarative mapping |
| **Data Validation** | Pydantic / Pydantic-Settings | `2.9.2` / `2.10.1` | Data modeling, validation contracts, and environment settings |
| **Database Migrations**| Alembic | `1.14.0` | Relational schema versioning and migration engine |
| **Database Engine** | PostgreSQL | `18.x` (Service: `postgresql-x64-18`) | Primary relational database engine running locally on port 5432 |
| **DB Driver** | psycopg2-binary | `2.9.10` | C-optimized PostgreSQL database adapter |
| **Authentication** | python-jose / passlib / bcrypt| `3.5.0` / `1.7.4` / `4.3.0` | JWT token issuance/verification and salted bcrypt password hashing |
| **File Handling** | python-multipart | `0.0.22` | Multipart form-data parser for photos and documents |
| **Frontend Runtime** | Node.js / npm | `v22.19.0` / `10.9.3` | JavaScript execution runtime and package manager |
| **Frontend Framework**| React | `18.3.1` | Declarative UI component library |
| **Client Routing** | React Router DOM | `6.27.0` | Single-page application client-side routing |
| **Build Tool** | Vite | `5.4.10` | Development server with HMR and production bundler |
| **Styling** | Tailwind CSS / PostCSS | `3.4.14` / `8.4.47` | Utility-first responsive design framework |
| **Icons** | Lucide React | `0.454.0` | Modern SVG iconography |
| **HTTP Client** | Axios | `1.7.7` | Promise-based HTTP client for API consumption |
| **Data Visualization**| Chart.js / react-chartjs-2 | `4.4.6` / `5.2.0` | Analytical charts for executive, sales, and financial dashboards |
| **Test Suites** | Pytest / pytest-asyncio | `8.3.3` / `0.24.0` | Backend regression test suite (162 tests passing) |

---

## 3. Project Directory Structure

```
sunpowersol/
├── backend/
│   ├── alembic/                      # Alembic schema migration environment
│   │   ├── versions/                 # Database schema revision scripts
│   │   ├── env.py                    # Migration execution context
│   │   └── script.py.mako            # Migration file template
│   ├── app/                          # Core application package
│   │   ├── models/                   # SQLAlchemy 2.0 ORM models (75 tables)
│   │   │   ├── __init__.py           # Model aggregator exporting all models
│   │   │   ├── auth.py               # User, Role, Permission, Employee, Department, Skill
│   │   │   ├── crm.py                # Customer, Enquiry, Followup, Survey, Product, Quotation
│   │   │   ├── finance.py            # Invoice, Payment, Allocation, Expense, TechnicianPayment, ProjectCost
│   │   │   ├── installations.py      # Installation, Schedule, Checklist, Test, Photo, Consumption
│   │   │   ├── inventory.py          # Inventory, StockMovement, SerialNumber, Dispatch
│   │   │   ├── projects.py           # Project, Order, BOM, Supplier, PurchaseOrder, GoodsReceipt
│   │   │   ├── subsidy.py            # SubsidyApplication, Document, Payment, StatusHistory
│   │   │   ├── warranty.py           # WarrantyPolicy, WarrantyRecord, ServiceTicket, ServiceVisit
│   │   │   └── workflow.py           # Task, Escalation, Notification, AuditLog
│   │   ├── routers/                  # 24 modular FastAPI routers mounted under /api/v1
│   │   │   ├── analytics.py          # Executive, sales, inventory, finance KPIs, and CSV export
│   │   │   ├── auth.py               # Authentication, token generation, user profile
│   │   │   ├── bom.py                # BOM templates and project bill of materials
│   │   │   ├── certifications.py     # Staff certification records
│   │   │   ├── crm_dashboard.py      # Lead funnel, conversion, and pipeline analytics
│   │   │   ├── customers.py          # Customer accounts and site profiles
│   │   │   ├── departments.py        # Organizational department management
│   │   │   ├── dispatch.py           # Serial number allocation, stock, and dispatch challans
│   │   │   ├── employees.py          # Staff profile, department assignment, and RBAC
│   │   │   ├── enquiries.py          # Lead intake, electricity bills, and stage tracking
│   │   │   ├── finance.py            # Milestone tax invoices, payment allocation, over-billing guard
│   │   │   ├── followups.py          # Communication log and reminder schedule
│   │   │   ├── health.py             # Liveness and database connectivity probes
│   │   │   ├── installations.py      # Checklists, electrical tests, and commissioning
│   │   │   ├── orders.py             # Sales order conversion and advance verification
│   │   │   ├── procurement.py        # Suppliers, Purchase Orders, and Goods Receipt Notes (GRN)
│   │   │   ├── products.py           # Product catalog, technical specs, and unit pricing
│   │   │   ├── projects.py           # Project lifecycle, milestone stages, and task assignments
│   │   │   ├── quotations.py         # Multi-tier solar quote calculation, revisions, approvals
│   │   │   ├── skills.py             # Employee technical competencies
│   │   │   ├── subsidy.py            # MNRE / PM Surya Ghar subsidy tracking and DISCOM stages
│   │   │   ├── supplier_finance.py   # Supplier bills, 3-way matching, and AP accounts
│   │   │   ├── surveys.py            # Rooftop site feasibility, dimensions, and observations
│   │   │   └── warranty.py           # Warranty records, AMC contracts, and service tickets
│   │   ├── schemas/                  # Pydantic v2 validation contracts
│   │   ├── services/                 # Business logic, calculation engines, and seed services
│   │   │   ├── auth.py               # Token creation and role validation
│   │   │   ├── bootstrap.py          # Zero-state database provisioning
│   │   │   └── seed.py               # Canonical roles and 77 system permissions
│   │   ├── utils/                    # Helper utilities, constants, and canonical role enums
│   │   │   ├── permissions.py        # Permission dependency resolvers
│   │   │   ├── roles.py              # Canonical role definitions (SystemRole)
│   │   │   └── security.py           # Password hashing and token generation
│   │   ├── config.py                 # Pydantic BaseSettings configuration
│   │   ├── database.py               # SQLAlchemy engine, session maker, and Base class
│   │   ├── dependencies.py           # Authentication and authorization route guards
│   │   └── main.py                   # FastAPI initialization, CORS, static mounts, and routes
│   ├── tests/                        # 22 Pytest regression test suites (162 tests passing)
│   ├── uploads/                      # Local storage for survey photos, documents, and vouchers
│   ├── .env.example                  # Environment variable configuration template
│   ├── alembic.ini                   # Alembic migration configuration
│   ├── bootstrap_admin.py            # Initial administrative provisioning CLI utility
│   └── requirements.txt              # Backend Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/               # 52 modular UI components, modals, and tables
│   │   ├── pages/                    # 15 domain-specific route views
│   │   │   ├── AnalyticsDashboardPage.jsx
│   │   │   ├── BOMManagementPage.jsx
│   │   │   ├── CRMManagementPage.jsx
│   │   │   ├── DispatchManagementPage.jsx
│   │   │   ├── EmployeeManagementPage.jsx
│   │   │   ├── InstallationManagementPage.jsx
│   │   │   ├── InvoiceManagementPage.jsx
│   │   │   ├── OrderManagementPage.jsx
│   │   │   ├── ProcurementManagementPage.jsx
│   │   │   ├── ProductManagementPage.jsx
│   │   │   ├── ProjectManagementPage.jsx
│   │   │   ├── QuotationManagementPage.jsx
│   │   │   ├── ServiceWarrantyManagementPage.jsx
│   │   │   ├── SubsidyManagementPage.jsx
│   │   │   └── SurveyManagementPage.jsx
│   │   ├── services/                 # 17 Axios API integration clients
│   │   ├── App.jsx                   # React router, navigation bar, and system status view
│   │   ├── index.css                 # Tailwind CSS styles and print media rules
│   │   └── main.jsx                  # React DOM mount entrypoint
│   ├── package.json                  # Frontend dependencies and scripts
│   ├── postcss.config.js             # PostCSS plugins
│   ├── tailwind.config.js            # Tailwind typography and theme configuration
│   └── vite.config.js                # Vite server and local backend proxy configuration
└── README.md                         # Project documentation
```

---

## 4. Implemented Business Modules & Workflows

### 1. CRM & Lead Management (`/crm`)
- **Customer Directory**: Centralized management of residential, commercial, and industrial consumers (GSTIN, consumer account numbers, sanctioned load, DISCOM utility, site coordinates).
- **Lead Pipeline**: Tracks enquiries through `NEW`, `CONTACTED`, `SURVEY_SCHEDULED`, `QUOTED`, `WON`, and `LOST`. Logs monthly electricity consumption, requested capacity (kW), and site address.
- **Follow-up Engine**: Schedule interaction dates, record meeting notes (Phone Call, WhatsApp, Email, In-Person Visit), and update next-contact deadlines.

### 2. Engineering Site Surveys (`/surveys`)
- **Feasibility Assessment**: Captures roof type (RCC Flat, Metal Sheet, Tiled), shadow-free area ($m^2$), tilt angle, azimuth, and structural integrity rating.
- **Electrical Evaluation**: Sanctioned load, service cable type, phase count (1-Phase / 3-Phase), distance to distribution transformer, and earthing pit soil conditions.
- **Observation Logs**: Add structured site observations, obstacle logs (chimneys, parapets, adjacent trees), and photo attachments with surveyor sign-offs.

### 3. Product Catalog & Hardware Inventory (`/products`)
- **Categorized Hardware**: Solar PV Modules (Mono PERC, TopCon, Bifacial), Grid-Tied Inverters, Hybrid Inverters, Energy Storage Batteries, BOS components, Mounting Structures, and Cabling.
- **Technical Specs**: Wattage, peak efficiency, input voltage ranges, warranty durations, and serialized tracking flags (`is_serialized`).
- **Pricing & Tax**: Base unit cost, suggested selling price, GST tax rates (5%, 12%, 18%), and reorder thresholds.

### 4. Bill of Materials (BOM) & Templates (`/bom`)
- **Standard BOM Templates**: Reusable templates for standard system capacities (e.g. 1 kW, 3 kW, 5 kW, 10 kW, 25 kW, 50 kW, 100 kW).
- **Project BOM Generation**: Instantiates template items into dedicated project BOMs with dynamic quantity multipliers for module counts, inverter capacities, wiring lengths, and mounting rails.
- **Cost Roll-Up**: Automated calculation of project hardware procurement costs and labor allowances.

### 5. Multi-Tier Quotation Engine (`/quotations`)
- **System Sizing & Pricing**: Automatically computes solar generation estimates, required panel counts, inverter ratings, gross cost, statutory PM Surya Ghar subsidy, net customer payable, and estimated payback period.
- **Revision Control**: Supports quote revisions (`QT-YYYY-XXXX-R1`, `QT-YYYY-XXXX-R2`) while preserving historical immutable records.
- **Approval Workflow**: Requires Director or Technical Manager approval before quotations are unlocked for customer release. Provides a dedicated printable view optimized for browser printing.

### 6. Sales Order Management (`/orders`)
- **Order Conversion**: Formally converts approved customer quotations into legally binding Sales Orders (`SO-YYYY-XXXX`).
- **Advance Payment Verification**: Tracks booking advance payments, payment transaction references, and customer sign-off dates.
- **Project Initiation Gateway**: Automatically creates the project record upon order confirmation.

### 7. Project Handover & Execution Tracking (`/projects`)
- **Seamless Handover**: Validates engineering BOM, commercial terms, and customer contacts before project initialization.
- **Milestone Management**: Governs 9 execution milestones:
  1. Engineering & Site Planning
  2. Procurement & Allocation
  3. Material Dispatch
  4. Civil & Structure Installation
  5. Panel & Inverter Mounting
  6. Electrical Wiring & Earthing
  7. Testing & Quality Commissioning
  8. DISCOM Net-Metering & Grid Sync
  9. Final Subsidy Release & Handover
- **Assignment & Scheduling**: Assign Project Engineers, set target completion dates, and log live stage transitions.

### 8. Procurement & Supplier Management (`/procurement`)
- **Vendor Directory**: Manage equipment manufacturers and distributors, GSTIN, payment terms, and vendor performance ratings.
- **Purchase Orders (PO)**: Generate structured POs linked directly to project requirements or general warehouse replenishment.
- **Goods Receipt Notes (GRN)**: Multi-step receiving inspection. Supports partial deliveries, inspects accepted vs. rejected quantities, records delivery challans, and executes automated stock ledger entries.
- **Weighted Moving Average Costing**: Automatically updates product unit costs using weighted moving average cost upon GRN approval.

### 9. Serialized Inventory Ledger & Dispatch (`/dispatch`)
- **Unit Serial Number Management**: Track high-value assets (PV panels, inverters, battery banks) by individual serial numbers.
- **State Machine**: Tracks lifecycle: `IN_STOCK` $\rightarrow$ `DISPATCHED` $\rightarrow$ `INSTALLED` $\rightarrow$ `RETURNED` / `REPLACED`.
- **Dispatch Challans**: Create itemized delivery challans (`DC-YYYY-XXXX`) linking specific serial numbers to targeted projects, capturing driver names, vehicle numbers, and dispatch dates.

### 10. Multi-Stage Installation & Commissioning (`/installations`)
- **Structured QA Checklists**:
  - **Civil & Structure**: Base grouting, anchor torque, tilt orientation, wind tolerance checks.
  - **Module & Array Mounting**: Clamp torque, array inter-spacing, string VOC/ISC measurements.
  - **Inverter & Wiring**: AC/DC distribution boxes, MC4 crimping quality, conduit protection.
  - **Earthing & Lightning Protection**: Earth pit resistance ($\Omega$), lightning arrester grounding.
  - **Testing & Commissioning**: Grid synchronization, anti-islanding test, inverter generation readout.
- **Technician Sign-off**: Record technician comments, punch-list items, and final commissioning approvals.

### 11. Customer Invoicing & Payment Allocation (`/invoices`)
- **Tax Invoices**: GST-compliant invoices (`INV-YYYY-XXXX`) generated against project milestones (Advance, Material Dispatch, Commissioning).
- **Over-Billing Prevention**: Automatic validation prevents cumulative billed amounts from exceeding total contract values.
- **Payment Allocation**: Record customer receipts (NEFT, RTGS, Cheque, UPI), log transaction IDs, and allocate payments against pending invoices with balance reconciliation.

### 12. Supplier Invoices & Accounts Payable (`/invoices` - Supplier AP Tab)
- **Supplier Bill Intake**: Match vendor invoices against approved Purchase Orders and Goods Receipt Notes (GRN).
- **Accounts Payable Ledger**: Track vendor liabilities, payment due dates, recorded payments, and pending balances.

### 13. Real-Time Project Profitability Engine (`/analytics` & `/projects`)
- **Real-Time Financial Auditing**: Computes recognized contract revenue vs. actual hardware costs (derived from GRN/dispatch values), direct procurement expenses, and subcontracted labor.
- **Gross Profit Margin Tracking**: Displays live Gross Margin (\%) and Net Profit per project to alert management to budget overruns.

### 14. Statutory Subsidy & DISCOM Net-Metering (`/subsidy`)
- **PM Surya Ghar Standard Slabs**:
  - Commercial / Industrial: ₹0 (Not eligible for central residential subsidy)
  - Residential up to 2 kW: ₹30,000 / kW (Max ₹60,000)
  - Residential 2 kW to 3 kW: ₹60,000 + ₹18,000 for the 3rd kW (Max ₹78,000)
  - Residential above 3 kW: Capped at ₹78,000
- **Audit Logging**: Manual overrides to the standard policy require an explicit `subsidy_override_reason` and log an audit action (`SUBSIDY_OVERRIDDEN`).
- **DISCOM Workflow**: Tracks Net-Metering application submission, DISCOM site inspection, bi-directional meter installation, and National Portal subsidy disbursement tracking.

### 15. Warranty Registration, AMC & Service Ticketing (`/warranty`)
- **Component Warranty Registration**: Register manufacturer warranties for modules (10/25-year performance), inverters (5/10-year), and workmanship.
- **Annual Maintenance Contracts (AMC)**: Manage comprehensive and non-comprehensive service contracts with scheduled quarterly inspection dates.
- **Service Helpdesk**: Customer complaint ticketing system tracking priority, technician dispatch, root cause resolution, and replacement serials.

### 16. Analytics & Executive Business Intelligence (`/analytics`)
- **Executive Overview**: Total revenue, booked capacity (kW), operational project counts, active pipeline value, and collection efficiency.
- **Sales Funnel Analytics**: Win/loss conversion ratios, monthly revenue trends, and enquiry sources.
- **Inventory & Operations**: Stock turnover, slow-moving items, open PO commitments, and technician installation velocity.
- **Data Export**: Export structured analytical datasets to CSV (`/api/v1/analytics/export`).

---

## 5. Canonical User Roles & Permissions Matrix

The system defines **9 canonical roles** (`backend/app/utils/roles.py`) governing access across **77 fine-grained permissions** (`backend/app/services/seed.py`):

| Canonical Role Code (`roles.slug`) | Display Role Name | Department | Core Responsibilities |
| :--- | :--- | :--- | :--- |
| `SUPER_ADMIN` | **Super Admin** | IT / Administration | Universal access across all modules. Manage users, employees, RBAC permissions, system configuration, database seeding, and global audit logs. |
| `DIRECTOR` | **Director** | Executive Board | Executive oversight. High-value quotation approvals, commercial discounts, project budgets, company profitability analytics, and executive reports. |
| `SALES` | **Sales Executive** | Sales & Marketing | Customer lead capture, enquiry management, customer follow-ups, survey requests, proposal and quotation generation. |
| `TECHNICAL_MANAGER` | **Technical / Installation Manager**| Operations & Engineering | Engineering feasibility, survey approvals, BOM management, technician scheduling, installation quality verification, and commissioning sign-offs. |
| `WAREHOUSE_PROCUREMENT` | **Warehouse & Procurement Manager**| Supply Chain & Logistics| Supplier directory, Purchase Orders, physical GRN inspection, serialized inventory control, and dispatch challan gate passes. |
| `FIELD_TECHNICIAN` | **Field Technician** | Field Operations | On-site roof measurements, obstacle mapping, structural and electrical installation execution, and checklist sign-off submissions. |
| `SERVICE_WARRANTY` | **Service & Warranty Executive**| After-Sales & Customer Care| Post-commissioning support, warranty certificate generation, AMC schedule tracking, ticket investigation, and on-site servicing. |
| `FINANCE_ACCOUNTS` | **Finance & Accounts Manager** | Finance & Accounts | Customer milestone tax invoicing, payment receipt allocation, supplier bill reconciliation (AP), GST compliance, and profitability auditing. |
| `CUSTOMER` | **Customer** | External Stakeholder | Portal access to view project progress, milestone completion, signed quotation copies, tax invoices, and to raise post-installation service tickets. |

### Permission Groups (77 Total Permissions)

1. **Authentication & Administration (12)**: `users.read`, `users.manage`, `roles.read`, `roles.manage`, `employees.read`, `employees.manage`, `departments.read`, `departments.manage`, `skills.read`, `skills.manage`, `certifications.read`, `certifications.manage`.
2. **CRM & Sales (15)**: `customers.read`, `customers.create`, `customers.update`, `enquiries.read`, `enquiries.create`, `enquiries.update`, `followups.manage`, `surveys.read`, `surveys.create`, `surveys.update`, `surveys.approve`, `quotations.read`, `quotations.create`, `quotations.update`, `quotations.approve`.
3. **Projects & Procurement (8)**: `orders.read`, `orders.create`, `orders.update`, `projects.read`, `projects.create`, `projects.update`, `bom.read`, `bom.manage`, `suppliers.manage`, `procurement.read`, `procurement.manage`.
4. **Inventory & Dispatch (7)**: `inventory.read`, `inventory.manage`, `serials.read`, `serials.manage`, `dispatch.read`, `dispatch.create`, `dispatch.confirm`.
5. **Installation Management (9)**: `schedules.read`, `schedules.manage`, `installations.read`, `installations.manage`, `checklists.submit`, `checklists.verify`, `tests.submit`, `consumption.manage`, `acceptances.manage`.
6. **Finance & Accounts (8)**: `finance.read`, `payments.read`, `payments.record`, `invoices.read`, `invoices.create`, `expenses.manage`, `technician_payments.manage`, `costs.read`.
7. **Warranty & Service (7)**: `warranty.read`, `warranty.manage`, `tickets.read`, `tickets.create`, `tickets.manage`, `visits.manage`, `replacements.manage`.
8. **Subsidies (3)**: `subsidies.read`, `subsidies.create`, `subsidies.manage`.
9. **Workflow & Monitoring (5)**: `tasks.read`, `tasks.manage`, `escalations.manage`, `audit.read`, `reports.read`.

---

## 6. End-to-End 12-Stage Solar Lifecycle Workflow

```
[1. Lead Intake] ──> [2. Technical Survey] ──> [3. System BOM] ──> [4. Quotation Engine]
       │                        │                       │                      │
       v                        v                       v                      v
Enquiry logged in       Rooftop area, tilt,    Template assemblies     Cost calculation,
CRM with sanctioned     azimuth, & single-     instantiated for        MNRE subsidy slab,
load & electricity      line diagram logged    project kW rating       & Director sign-off
bills                   by technician                                  
                                                                               │
[8. Installation QA] <── [7. Serial Dispatch] <── [6. Procurement] <── [5. Sales Order]
       │                        │                       │                      │
       v                        v                       v                      v
Civil, panel, inverter, Challans generated with  Suppliers, POs, &     Approved quote converted;
earthing, & commissioning individual serial IDs  GRN verification      booking advance logged;
checklists signed off   for asset tracking      with moving avg cost   project initialized
       │
       v
[9. Invoicing & Finance] ──> [10. Net-Metering] ──> [11. Subsidy Claim] ──> [12. AMC & Warranty]
       │                             │                       │                       │
       v                             v                       v                       v
Milestone tax invoices       DISCOM application,    National Portal claim   Warranty cards issued,
generated; over-billing      meter testing, & grid  tracking & direct-to-   AMC maintenance logs, &
prevented; payments allocated sync approval         customer disbursement   service tickets resolved
```

---

## 7. Backend Architecture & API Organization

The backend is built with **FastAPI 0.115.0** and **SQLAlchemy 2.0.36**. The API exposes **193 routes** across **24 modular routers** registered in `backend/app/main.py`:

```
Base Prefix: /api/v1
```

| Router Module | Mount Prefix / Endpoint Groups | Key Responsibilities |
| :--- | :--- | :--- |
| `health_router` | `/api/v1/health` & `/health` | Health checks, database connectivity, and timestamp probes |
| `auth_router` | `/api/v1/auth` | Login (`/auth/login`), profile (`/auth/me`), change password |
| `department_router` | `/api/v1/departments` | Company organizational departments and rosters |
| `skill_router` | `/api/v1/skills` | Technical skill directory for field staff qualification |
| `certification_router`| `/api/v1/certifications`| Staff safety and electrical certifications |
| `employee_router` | `/api/v1/employees` | Staff profiles, department linkage, role assignments |
| `customer_router` | `/api/v1/customers` | Customer accounts, utility meter IDs, and sites |
| `enquiry_router` | `/api/v1/enquiries` | Lead capture, monthly power consumption, and status |
| `followup_router` | `/api/v1/followups` | Lead touchpoints, call notes, and reminder scheduling |
| `crm_router` | `/api/v1/crm` | Sales pipeline summary and lead conversion analytics |
| `survey_router` | `/api/v1/surveys` | Rooftop feasibility, physical dimensions, observations |
| `product_router` | `/api/v1/products` | Solar modules, inverters, batteries, BOS hardware |
| `bom_router` | `/api/v1/bom` | Reusable BOM engineering templates and project bills |
| `quotation_router` | `/api/v1/quotations` | Multi-tier solar quote calculation, revisions, approvals |
| `order_router` | `/api/v1/orders` | Confirmed sales orders, advance tracking, and handover |
| `project_router` | `/api/v1/projects` | 9-stage milestone progression, task assignments, notes |
| `procurement_router` | `/api/v1/suppliers`<br>`/api/v1/purchase-orders`<br>`/api/v1/goods-receipts` | Supplier records, Purchase Orders, and physical GRN receipts with moving average cost |
| `dispatch_router` | `/api/v1/dispatch`<br>`/api/v1/dispatches`<br>`/api/v1/inventory` | Serial number allocation, warehouse stock, and dispatch challans |
| `installation_router`| `/api/v1/installations`<br>`/api/v1/installation-schedules` | Checklists (civil, panel, inverter), electrical tests, worklogs |
| `finance_router` | `/api/v1/invoices`<br>`/api/v1/payments` | Customer milestone tax invoices, payment allocation, over-billing guards |
| `supplier_finance_router`| `/api/v1/supplier-invoices`<br>`/api/v1/supplier-payments` | Supplier bills, 3-way matching against PO/GRN, AP ledger |
| `subsidy_router` | `/api/v1/subsidy` | PM Surya Ghar subsidy tracking and DISCOM stages |
| `warranty_router` | `/api/v1/warranty`<br>`/api/v1/service-tickets`<br>`/api/v1/service-visits` | Warranty records, AMC agreements, service tickets |
| `analytics_router` | `/api/v1/analytics` | Executive KPIs, profitability metrics, and CSV reporting export |

### Authoritative SQLAlchemy Database Models (75 Tables)

The database schema comprises **75 tables** grouped across 10 modular SQLAlchemy model files (`backend/app/models/`):

- **`auth.py`**: `User`, `Role`, `RolePermission`, `Permission`, `Employee`, `Department`, `Skill`, `EmployeeSkill`, `EmployeeCertification`, `FileAttachment`
- **`crm.py`**: `Customer`, `Enquiry`, `Followup`, `Survey`, `SurveyApproval`, `Product`, `Quotation`, `QuotationItem`, `QuotationRevision`
- **`projects.py`**: `Project`, `ProjectBomItem`, `ProjectNote`, `Order`, `BomTemplate`, `BomItem`, `Supplier`, `PurchaseOrder`, `PurchaseOrderItem`, `GoodsReceipt`, `GoodsReceiptItem`, `SupplierInvoice`, `SupplierPayment`, `SupplierPaymentAllocation`
- **`inventory.py`**: `Inventory`, `StockMovement`, `StockReservation`, `SerialNumber`, `SerialNumberHistory`, `Dispatch`, `DispatchItem`, `DispatchSerial`, `DeliveryConfirmation`
- **`installations.py`**: `Installation`, `InstallationSchedule`, `InstallationScheduleTechnician`, `InstallationChecklist`, `InstallationTest`, `InstallationPhoto`, `MaterialConsumption`, `CustomerAcceptance`, `TechnicianWorklog`
- **`finance.py`**: `Invoice`, `InvoiceItem`, `Payment`, `PaymentAllocation`, `Expense`, `TechnicianPayment`, `ProjectCost`
- **`subsidy.py`**: `SubsidyApplication`, `SubsidyDocument`, `SubsidyPayment`, `SubsidyStatusHistory`
- **`warranty.py`**: `WarrantyPolicy`, `WarrantyRecord`, `WarrantyEvent`, `ServiceTicket`, `ServiceTicketConfirmation`, `ServiceVisit`, `Replacement`
- **`workflow.py`**: `Task`, `TaskAssignment`, `TaskHistory`, `Escalation`, `Notification`, `AuditLog`

---

## 8. Frontend Architecture & Views

The frontend is a single-page application built with **React 18** and **Vite**, featuring **15 domain-specific page views**, **17 route endpoints**, **52 modular components**, and **17 Axios API services**.

### Route Catalog

| Path | View Component | Core Functionality |
| :--- | :--- | :--- |
| `/` | `SystemStatusPage` | Real-time backend API liveness, database connectivity status, and system metrics |
| `/crm` | `CRMManagementPage` | Lead pipeline board, customer accounts, and scheduled follow-up tracking |
| `/surveys` | `SurveyManagementPage` | Site feasibility assessments, roof dimension entry, electrical specs |
| `/products` | `ProductManagementPage` | Hardware catalog (panels, inverters, batteries, BOS), pricing tiers |
| `/bom` | `BOMManagementPage` | Reusable BOM engineering templates and project-specific BOM breakdowns |
| `/quotations` | `QuotationManagementPage`| Solar pricing calculation, quotation revisions, approval modal, print view |
| `/orders` | `OrderManagementPage` | Sales order conversion, advance verification, and project handover |
| `/projects` | `ProjectManagementPage` | 9-stage milestone progression, task assignments, and profitability overview |
| `/procurement`| `ProcurementManagementPage`| Supplier directory, PO creation, physical GRN inspection, and inventory ledger |
| `/dispatch` | `DispatchManagementPage` | Serial number status tracking, dispatch challan generation, transport tracking|
| `/installations`| `InstallationManagementPage`| Civil, structure, module, inverter, and commissioning checklists |
| `/warranty` | `ServiceWarrantyManagementPage`| Warranty registration certificates, AMC contracts, and service ticket logging |
| `/subsidy` | `SubsidyManagementPage` | MNRE / PM Surya Ghar scheme processing, DISCOM net-metering stages |
| `/invoices` | `InvoiceManagementPage` | Milestone tax invoicing, payment recording, and supplier AP bills |
| `/analytics` | `AnalyticsDashboardPage` | Executive BI dashboard, financial charts, gross margin %, CSV report export |
| `/employees` | `EmployeeManagementPage` | Staff administration, department assignment, skills, and certifications |
| `/architecture`| `ArchitecturePage` | System architecture overview, canonical roles, and permission reference |

---

## 9. Database Configuration & Local Setup

SIMS uses **PostgreSQL 18** running locally on default port `5432`.

- **Database Engine**: PostgreSQL 18 (Local Windows Service: `postgresql-x64-18`)
- **Default Database Name**: `sunpower_sims`
- **Default Port**: `5432`
- **Default Host**: `localhost` / `127.0.0.1`

### Step 1: Ensure PostgreSQL Service is Running (Windows)

```powershell
# Check PostgreSQL service status
Get-Service -Name "postgresql*"

# If stopped, start the service
Start-Service -Name "postgresql-x64-18"
```

### Step 2: Create the Database (If not already created)

```powershell
# Connect via psql and create database
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE sunpower_sims;"
```

---

## 10. Local Installation & Prerequisites

### Prerequisites

- **Python**: Version `3.12.0` installed and available in system PATH.
- **Node.js**: Version `v18+` (verified on `v22.19.0`) and `npm` (verified on `10.9.3`).
- **PostgreSQL**: Version `16+` (verified on `18.x`).
- **Git**: Installed for version control.

### Backend Setup

1. Open PowerShell and navigate to the `backend` directory:
   ```powershell
   cd c:\Users\AsherG\sunpowersol\backend
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure environment settings:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env to verify database connection credentials
   ```

### Frontend Setup

1. Open a new PowerShell terminal and navigate to the `frontend` directory:
   ```powershell
   cd c:\Users\AsherG\sunpowersol\frontend
   ```

2. Install Node.js dependencies:
   ```powershell
   npm install
   ```

---

## 11. Running the Application Locally — Two-Terminal Startup

### Terminal 1: Start the Backend API Server

In your first PowerShell terminal (with virtual environment activated):

```powershell
cd c:\Users\AsherG\sunpowersol\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*Console output will confirm:*
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### Terminal 2: Start the Frontend Development Server

In your second PowerShell terminal:

```powershell
cd c:\Users\AsherG\sunpowersol\frontend
npm run dev
```

*Console output will confirm:*
```
  VITE v5.4.10  ready in 420 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: use --host to expose
```

---

## 12. Local Application URLs & Endpoints

| Service / Interface | Local URL | Description |
| :--- | :--- | :--- |
| **Frontend Web Application** | [http://127.0.0.1:5173/](http://127.0.0.1:5173/) | Main SIMS React single-page application |
| **Backend API Root** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Welcome message and API version endpoint |
| **Interactive Swagger UI Docs**| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Interactive OpenAPI documentation and test console |
| **ReDoc API Documentation** | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) | Alternative comprehensive API reference |
| **Backend Health Check** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Real-time database and service liveness check |

---

## 13. Environment Configuration & Placeholders

Configure your backend settings in `backend/.env`.

> [!CAUTION]
> Never commit actual passwords, database credentials, or secret keys to version control. Use the placeholders below as a reference.

```ini
# Environment Configuration
APP_NAME="SunPower SIMS"
APP_ENV=development
DEBUG=True
API_V1_STR=/api/v1
SECRET_KEY=<generate_a_secure_random_64_character_hex_key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=<your_database_username>
DB_PASSWORD=<your_database_password>
DB_NAME=sunpower_sims

# Constructed Database URL
DATABASE_URL=postgresql://<your_database_username>:<your_database_password>@localhost:5432/sunpower_sims

# Local Storage Directory
UPLOAD_DIR=./uploads

# CORS Allowed Origins (Comma separated)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Optional Company Quotation Profile
COMPANY_LEGAL_NAME="SunPower Solutions Private Limited"
COMPANY_GSTIN="07AAAAA0000A1Z5"
COMPANY_ADDRESS="Plot 42, Solar Tech Park, Industrial Area, New Delhi"
COMPANY_PHONE="+91-11-4000-0000"
COMPANY_EMAIL="contact@sunpowersol.com"
COMPANY_BANK_NAME="State Bank of India"
COMPANY_BANK_ACCOUNT_NAME="SunPower Solutions Pvt Ltd"
COMPANY_BANK_ACCOUNT_NO="000000000000"
COMPANY_BANK_IFSC="SBIN0001234"
COMPANY_BANK_BRANCH="Industrial Finance Branch"
```

---

## 14. Authentication & Bootstrap Administration

### The `bootstrap_admin.py` Script

The project provides an administrative provisioning utility located at `backend/bootstrap_admin.py`.

```powershell
python bootstrap_admin.py [--email EMAIL] [--password PASSWORD] [--name NAME] [--phone PHONE] [--seed-only]
```

#### Code Inspection Findings & Operational Guidance:
1. **Initial Zero-State Provisioning Utility**: This script seeds the 9 canonical roles and 77 fine-grained system permissions, creating an initial Super Admin account when initializing an empty database from scratch.
2. **Idempotent by Design**: The underlying `bootstrap_super_admin` service checks whether roles, permissions, or the target admin email already exist. If an admin account exists, the script safely reports existing status without modifying or duplicating records.
3. **NOT Required for Daily Startup**: Once your local database is provisioned and has an administrative account, you **DO NOT** execute this script when starting the application. Normal startup is simply starting the services (`uvicorn` + `npm run dev`), which will serve all endpoints using existing database records.

### Logging into the Application

- Log in via the top-right `AuthBar` in the web application using your configured administrator credentials.
- The system returns an HTTP-only compatible JWT bearer token valid for 480 minutes (8 hours).
- The application automatically decodes user roles and displays accessible modules and role badges in the navigation bar.

---

## 15. File Uploads & Local Document Storage

- **Upload Directory**: Documents, site survey roof photographs, DISCOM sanction letters, warranty cards, and receipt vouchers are stored locally on the server in `backend/uploads/`.
- **Static Mounting**: The directory is mounted at `/uploads` via FastAPI's `StaticFiles` middleware in `backend/app/main.py`.
- **Database Metadata**: File metadata (original filename, stored disk filename, MIME type, file size in bytes, and uploading user ID) is persisted in the PostgreSQL `file_attachments` table.
- **Frontend Access**: The Vite development server automatically proxies any URL requests matching `/uploads/*` to `http://127.0.0.1:8000/uploads/*`, ensuring seamless thumbnail rendering and document downloads.

---

## 16. Verification & Automated Test Suite Execution

The SIMS application includes a regression test suite validating all business modules, permission guards, costing calculations, and state workflows across **22 test files**.

### Running Backend Tests

In the `backend` directory (with virtual environment active):

```powershell
cd c:\Users\AsherG\sunpowersol\backend
python -m pytest
```

#### Verified Test Suite Results:
- **Total Tests**: `162 passed`
- **Execution Time**: `~33.36 seconds`
- **Test File Coverage (22 Files)**:
  1. `test_analytics_module.py`: Executive KPIs, sales, operations, inventory valuation, CSV export
  2. `test_auth_api.py`: Login, token refresh, password change, RBAC isolation
  3. `test_bom_module.py`: Template CRUD, item configuration, project BOM generation
  4. `test_crm_module.py`: Lead stages, concurrency, follow-ups, capacity validation
  5. `test_database_schema.py`: Verifies existence of all 75 database tables and foreign keys
  6. `test_dispatch_module.py`: Material readiness, stock reservation, serial assignment, challans
  7. `test_employee_module.py`: Departments, employee CRUD, skills, certifications expiry
  8. `test_finance_module.py`: Milestone invoicing, over-billing prevention, payment allocation
  9. `test_health.py`: Health probes and database ping
  10. `test_installation_module.py`: Checklists, electrical test results, commissioning sign-off
  11. `test_master_end_to_end_flow.py`: Automated 12-stage end-to-end lifecycle verification
  12. `test_order_engine.py`: Sales order conversion, advance payments, order statuses
  13. `test_procurement_module.py`: Suppliers, Purchase Orders, GRN physical inspection, moving average cost
  14. `test_product_module.py`: Catalog management, specifications, pricing validation
  15. `test_project_handover.py`: Order-to-project handover, milestone generation, tasks
  16. `test_quotation_engine.py`: Solar sizing, pricing calculations, approvals, revisions, print view
  17. `test_security.py`: Password hashing, JWT token generation, expiration, signature verification
  18. `test_seed.py`: Canonical 9 roles and 77 permissions idempotency validation
  19. `test_subsidy_module.py`: MNRE / PM Surya Ghar slab calculation, DISCOM steps
  20. `test_supplier_finance.py`: Supplier AP invoices, 3-way matching, payments, profitability
  21. `test_survey_module.py`: Site feasibility, roof dimensions, observations, approvals
  22. `test_warranty_module.py`: Warranty registration, AMC agreements, service tickets, replacements

### Building the Frontend

In the `frontend` directory:

```powershell
cd c:\Users\AsherG\sunpowersol\frontend
npm run build
```

#### Verified Frontend Build Results:
- **Vite Production Bundler**: `vite v5.4.10 building for production...`
- **Build Status**: `✓ built in ~4.69s`
- **Output Artifacts**: Zero build warnings; production bundle emitted in `frontend/dist/`.

---

## 17. Known Limitations & Implementation Notes

1. **Print-to-PDF vs. Server-Side PDF Compilation**:
   - Customer quotations and milestone invoices provide dedicated printable views (`QuotationPrintModal.jsx`, `InvoicePrintModal.jsx`) engineered with `@media print` CSS stylesheets for clean browser-native print and "Save as PDF" functionality.
   - Server-side headless PDF binary compilation (via tools like WeasyPrint or ReportLab) is not configured; the system relies on browser printing and the `file_attachments` schema to attach signed external PDFs.
2. **Tabular Data Export**:
   - Analytical reporting data exports are supported in standard **CSV format** via `/api/v1/analytics/export`. Streaming Excel (`.xlsx`) binary export is not implemented.
3. **Local Deployment Scope**:
   - The application is designed and configured specifically for local execution on a Windows workstation. Cloud infrastructure deployment manifests (Docker containers, Kubernetes charts, AWS S3 buckets) are not part of the current workspace configuration.
4. **DISCOM National Portal Integration**:
   - National Portal and state DISCOM portal interactions (such as PM Surya Ghar application filing) are structured as internal milestone tracking workflows requiring manual input of application reference numbers, inspection dates, and approval numbers. Direct automated robotic scraping or government API integrations are not implemented due to external government portal access boundaries.

---

## 18. Troubleshooting & Common Issues

### 1. Database Connection Failure (`psycopg2.OperationalError`)
- **Symptom**: Backend startup fails with `psycopg2.OperationalError: could not connect to server: Connection refused`.
- **Cause**: The local PostgreSQL service is stopped or port 5432 is blocked.
- **Resolution**:
  ```powershell
  Get-Service -Name "postgresql*"
  Start-Service -Name "postgresql-x64-18"
  ```
  Verify that `DB_PASSWORD` and `DB_USER` in `backend/.env` match your local PostgreSQL server credentials.

### 2. Frontend API Calls Return `404 Not Found` or `ECONNREFUSED`
- **Symptom**: Browser shows network errors when fetching `/api/v1/...`.
- **Cause**: The FastAPI backend server is not running on `127.0.0.1:8000`, or Vite's reverse proxy cannot reach it.
- **Resolution**:
  - Verify that the backend is running by navigating to [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).
  - Ensure `frontend/vite.config.js` has the proxy target set to `http://127.0.0.1:8000`.

### 3. Missing Roles or "Invalid Credentials" on Fresh Database
- **Symptom**: Unable to log in immediately after creating an empty database.
- **Cause**: The database tables exist, but canonical roles, permissions, and the initial administrator account have not been seeded.
- **Resolution**:
  Run the provisioning script once:
  ```powershell
  cd c:\Users\AsherG\sunpowersol\backend
  python bootstrap_admin.py --email admin@sunpowersol.com --password AdminPassword123! --name "System Administrator"
  ```

### 4. Port Conflicts (Port 8000 or 5173 Already in Use)
- **Symptom**: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`.
- **Cause**: A previous uvicorn or node process is still running in the background.
- **Resolution**:
  Find and terminate the process holding the port:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```
