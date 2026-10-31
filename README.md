# SunPower Solutions — Solar Installation Management System (SIMS)

A complete full-stack enterprise management system designed for **SunPower Solutions** to handle end-to-end solar project workflows: enquiries, site surveys, quotations, BOM generation, orders, procurement, inventory with serial number tracking, technician dispatch, physical installation, payment milestones, invoicing, warranties, service tickets, and executive dashboards.

The company handles **~40 solar installations per month with 15 field technicians**, installing **1 kW to 5 kW rooftop systems (On-Grid & Off-Grid)**.

---

## 1. System Architecture

```text
solar-management-system/
    backend/
        app/
            main.py              # FastAPI application entrypoint & middleware
            database.py          # SQLAlchemy 2.x session & declarative base
            config.py            # Pydantic BaseSettings environment loader
            models/              # SQLAlchemy 2.x models & enum definitions
            schemas/             # Pydantic validation schemas & API responses
            routers/             # API route controllers (health, auth, etc.)
            services/            # Business logic layer
            dependencies/        # Auth, role check & DB injection dependencies
            utils/               # Helper utilities & security algorithms
        alembic/                 # Alembic migration environment & versions
        uploads/                 # Local file storage for documents & photos
        alembic.ini              # Alembic migration configuration
        requirements.txt         # Backend Python dependencies
        .env.example             # Backend environment template
    frontend/
        src/
            components/          # Reusable UI components
            pages/               # Page-level route views
            dashboards/          # Role-specific dashboard views
            layouts/             # App shell and navigation wrappers
            services/            # Axios API client & endpoints
            hooks/               # Custom React hooks
            assets/              # Static media & icons
            App.jsx              # Main router & health diagnostic interface
            main.jsx             # React DOM entry point
            index.css            # Tailwind CSS directives
        index.html               # Vite HTML entry point
        vite.config.js           # Vite build & reverse-proxy configuration
        tailwind.config.js       # Tailwind CSS theme extension
        postcss.config.js        # PostCSS configuration
        package.json             # Frontend NPM dependencies & scripts
        .env.example             # Frontend environment template
    database/
        schema.sql               # PostgreSQL initial DDL schema definition
    README.md                    # Project documentation & instructions
```

---

## 2. Technology Stack

### Frontend
- **React 18** (Modern functional components)
- **Vite** (Next-generation frontend tooling)
- **JavaScript (ES Modules)**
- **Tailwind CSS** (Utility-first styling with Solar theme)
- **React Router v6** (Client-side routing)
- **Axios** (Configured HTTP client with interceptors)
- **Chart.js & react-chartjs-2** (Interactive analytics charts)
- **Lucide React** (Clean icons)

### Backend
- **Python 3.12+**
- **FastAPI** (High-performance async web framework)
- **SQLAlchemy 2.x** (Object Relational Mapper)
- **Alembic** (Database schema versioning & migrations)
- **Pydantic v2 & pydantic-settings** (Data validation and settings)
- **JWT Authentication** (`python-jose` / `pyjwt`)
- **Password Hashing** (`passlib[bcrypt]`)
- **Local File Storage** (Uploaded photos & documents stored locally, metadata in PostgreSQL)

### Database
- **PostgreSQL 14+**

---

## 3. The 9 User Roles

The system strictly enforces permissions on the backend using dependency-injected role-based access control (RBAC):

1. **Super Admin**: Full administrative control across the entire system.
2. **Director**: Executive KPIs, high-level business analytics, and revenue reports.
3. **Sales Executive**: Leads, enquiries, customer interactions, and quotation generation.
4. **Technical / Installation Manager**: Site survey reviews, technical feasibility, project planning, and work orders.
5. **Warehouse & Procurement Manager**: Inventory stock, purchase orders, BOM allocation, and component serial tracking.
6. **Field Technician**: Mobile-friendly survey uploads, installation checklists, commissioning photos, and job sign-offs.
7. **Service & Warranty Executive**: Maintenance tickets, warranty claims, and periodic service scheduling.
8. **Finance & Accounts Manager**: Invoices, milestone payment tracking, customer receipts, and subsidy claims.
9. **Customer**: Project progress tracking, document download, milestone payments, and feedback.

---

## 4. Installation & Setup Guide

### Prerequisites
- Python 3.10+ installed
- Node.js 18+ and npm installed
- PostgreSQL 14+ installed and running

---

### Step 1: Backend Setup

1. Open a terminal and navigate to the backend directory:
   ```powershell
   cd solar-management-system/backend
   ```

2. (Optional but recommended) Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` if your PostgreSQL username, password, or port differs:
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sunpower_sims
   ```

5. Initialize the PostgreSQL Database:
   Create the database in PostgreSQL:
   ```powershell
   psql -U postgres -c "CREATE DATABASE sunpower_sims;"
   ```
   Apply initial schema via PostgreSQL:
   ```powershell
   psql -U postgres -d sunpower_sims -f ../database/schema.sql
   ```
   Or generate/run Alembic migrations:
   ```powershell
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

---

### Step 2: Frontend Setup

1. Open a terminal and navigate to the frontend directory:
   ```powershell
   cd solar-management-system/frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```

---

## 5. Starting the Application

### Start Backend Server
Inside `solar-management-system/backend`:
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Interactive API Docs (Swagger): `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### Start Frontend Server
Inside `solar-management-system/frontend`:
```powershell
npm run dev
```
- Frontend Application: `http://localhost:5173`

---

## 6. Verification & Health Check

1. Open `http://localhost:5173` in your browser.
2. The UI will automatically ping the backend `/health` endpoint and verify client-server connectivity.
3. Once PostgreSQL is running and credentials in `.env` are verified, the database status will reflect `Connected`.
