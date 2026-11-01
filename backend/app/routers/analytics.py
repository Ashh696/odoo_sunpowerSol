from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_, and_, case, distinct
from decimal import Decimal
from datetime import date, datetime, timezone, timedelta
import io
import csv
import logging

from app.database import get_db
from app.models.auth import User, Role, Employee
from app.models.crm import Customer, Enquiry, Followup, Survey, Quotation, Product
from app.models.projects import Order, Project, ProjectBomItem, Supplier, PurchaseOrder, GoodsReceipt
from app.models.inventory import Inventory, Dispatch, DispatchItem, SerialNumber
from app.models.installations import InstallationSchedule, Installation, TechnicianWorklog, InstallationTest
from app.models.finance import Invoice, Payment, PaymentAllocation
from app.models.warranty import WarrantyRecord, ServiceTicket, ServiceVisit, Replacement
from app.models.subsidy import SubsidyApplication, SubsidyPayment
from app.dependencies.auth import get_current_user, get_user_permissions
from app.utils.roles import SystemRole
from app.schemas import APIResponse
from app.schemas.analytics import (
    ExecutiveDashboardResponse,
    ExecutiveEnquiryKPIs,
    ExecutiveConversionKPIs,
    ExecutiveOrderKPIs,
    ExecutiveProjectKPIs,
    ExecutiveFinanceKPIs,
    ExecutiveInventoryKPIs,
    SalesAnalyticsResponse,
    SalesRepPerformance,
    QuotationConversionMetrics,
    SalesVolumeByPeriod,
    ProjectAnalyticsResponse,
    ProjectManagerWorkload,
    InstallationScheduleWorkload,
    InventoryAnalyticsResponse,
    InventoryProductItem,
    FinanceAnalyticsResponse,
    AgingReceivablesBucket,
    MilestoneInvoiceBreakdown,
    MonthlyCashFlow,
    EstimatedGrossMarginMetric,
    OperationalAnalyticsResponse,
    ProcurementOperationsKPIs,
    DispatchOperationsKPIs,
    InstallationOperationsKPIs,
    ServiceWarrantyOperationsKPIs,
    SubsidyOperationsKPIs,
    ProjectStageExecution,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Reports & Analytics"])


# ==========================================
# AUTH & AUTHORIZATION HELPERS
# ==========================================

def _assert_internal_staff(user: User):
    """
    Enforces strict customer isolation.
    Customers receive HTTP 403 from every company-wide /analytics endpoint.
    """
    if getattr(user, "user_type", None) == "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer accounts cannot access internal company-wide analytics.",
        )
    if user.role and user.role.slug == SystemRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer role is restricted from accessing business analytics dashboards.",
        )


def _check_analytics_access(user: User, allowed_roles: List[str], required_perms: List[str]):
    """
    Checks if user is SUPER_ADMIN, holds one of allowed_roles, or possesses any of required_perms.
    """
    _assert_internal_staff(user)
    if user.role and user.role.slug == SystemRole.SUPER_ADMIN:
        return

    user_role_slug = user.role.slug if user.role else ""
    if user_role_slug in allowed_roles:
        return

    user_perms = get_user_permissions(user)
    if any(p in user_perms for p in required_perms):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient privileges to view this analytics report.",
    )


def _parse_date_range(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Validates date ranges and returns UTC half-open intervals for DateTime comparisons.
    timestamp >= start_dt and timestamp < end_dt
    """
    if date_from and date_to and date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to cannot be earlier than date_from.",
        )
    start_dt = None
    end_dt = None
    if date_from:
        start_dt = datetime(date_from.year, date_from.month, date_from.day, 0, 0, 0, tzinfo=timezone.utc)
    if date_to:
        next_day = date_to + timedelta(days=1)
        end_dt = datetime(next_day.year, next_day.month, next_day.day, 0, 0, 0, tzinfo=timezone.utc)
    return start_dt, end_dt


# ==========================================
# 1. EXECUTIVE DASHBOARD ENDPOINT
# ==========================================

@router.get("/executive", response_model=APIResponse[ExecutiveDashboardResponse])
def get_executive_dashboard(
    date_from: Optional[date] = Query(None, description="Filter from date (applies to creation dates)"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executive Multi-Module Dashboard.
    Accessible to SUPER_ADMIN, DIRECTOR, or users with 'reports.read'.
    Aggregates high-level KPIs across Enquiries, Orders, Projects, Invoicing, and Inventory.
    """
    _check_analytics_access(
        user=current_user,
        allowed_roles=[SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR],
        required_perms=["reports.read"],
    )
    start_dt, end_dt = _parse_date_range(date_from, date_to)

    # -----------------------------
    # A. Enquiries & Conversion
    # -----------------------------
    enq_stmt = select(Enquiry.status, func.count(Enquiry.id))
    if start_dt:
        enq_stmt = enq_stmt.where(Enquiry.created_at >= start_dt)
    if end_dt:
        enq_stmt = enq_stmt.where(Enquiry.created_at < end_dt)
    enq_stmt = enq_stmt.group_by(Enquiry.status)
    enq_rows = db.execute(enq_stmt).all()

    enq_counts = {r[0]: r[1] for r in enq_rows}
    canonical_statuses = ["NEW", "CONTACTED", "SURVEY_REQUESTED", "QUOTED", "WON", "LOST", "CANCELLED"]
    status_distribution = {s: enq_counts.get(s, 0) for s in canonical_statuses}

    total_enquiries = sum(status_distribution.values())
    won_count = status_distribution.get("WON", 0)
    lost_count = status_distribution.get("LOST", 0)
    cancelled_count = status_distribution.get("CANCELLED", 0)

    # Strict conversion formula: Won / All Leads (including Lost and Cancelled)
    conversion_pct = round((won_count / total_enquiries * 100.0), 1) if total_enquiries > 0 else 0.0

    # -----------------------------
    # B. Orders
    # -----------------------------
    order_stmt = select(
        func.count(Order.id),
        func.coalesce(func.sum(Order.total_amount), Decimal("0.00")),
        func.coalesce(func.sum(Order.advance_paid), Decimal("0.00")),
        func.coalesce(func.sum(Order.balance_amount), Decimal("0.00")),
    ).where(Order.status != "CANCELLED")

    if date_from:
        order_stmt = order_stmt.where(Order.order_date >= date_from)
    if date_to:
        order_stmt = order_stmt.where(Order.order_date <= date_to)

    order_metrics = db.execute(order_stmt).one()
    total_orders = order_metrics[0] or 0
    contract_val = Decimal(str(order_metrics[1] or 0))
    advance_col = Decimal(str(order_metrics[2] or 0))
    balance_due = Decimal(str(order_metrics[3] or 0))

    # -----------------------------
    # C. Projects
    # -----------------------------
    today_date = date.today()
    proj_rows = db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    ).all()
    proj_status_map = {r[0]: r[1] for r in proj_rows}

    active_statuses = ["INITIATED", "PROCUREMENT", "DISPATCHED", "INSTALLATION", "ON_HOLD"]
    active_count = sum(proj_status_map.get(s, 0) for s in active_statuses)
    completed_statuses = ["COMMISSIONED", "HANDED_OVER"]
    completed_count = sum(proj_status_map.get(s, 0) for s in completed_statuses)

    delayed_stmt = select(func.count(Project.id)).where(
        Project.status.notin_(["COMMISSIONED", "HANDED_OVER", "CANCELLED"]),
        Project.planned_completion_date < today_date,
    )
    delayed_count = db.execute(delayed_stmt).scalar() or 0

    comm_cap_stmt = select(
        func.coalesce(func.sum(Project.system_capacity_kw), Decimal("0.00"))
    ).where(Project.status.in_(["COMMISSIONED", "HANDED_OVER"]))
    commissioned_kw = Decimal(str(db.execute(comm_cap_stmt).scalar() or "0.00"))

    # -----------------------------
    # D. Finance
    # -----------------------------
    inv_stmt = select(func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")))
    if date_from:
        inv_stmt = inv_stmt.where(Invoice.invoice_date >= date_from)
    if date_to:
        inv_stmt = inv_stmt.where(Invoice.invoice_date <= date_to)
    total_inv = Decimal(str(db.execute(inv_stmt).scalar() or "0.00"))

    pay_stmt = select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(Payment.status == "COMPLETED")
    if date_from:
        pay_stmt = pay_stmt.where(Payment.payment_date >= date_from)
    if date_to:
        pay_stmt = pay_stmt.where(Payment.payment_date <= date_to)
    cash_col = Decimal(str(db.execute(pay_stmt).scalar() or "0.00"))

    # Outstanding: invoices with balance > 0
    rec_stmt = select(func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00"))).where(Invoice.balance_amount > 0)
    out_rec = Decimal(str(db.execute(rec_stmt).scalar() or "0.00"))

    # Overdue: balance > 0 and due_date < today
    overdue_stmt = select(
        func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00")),
        func.count(Invoice.id),
    ).where(
        Invoice.balance_amount > 0,
        Invoice.due_date < today_date,
    )
    overdue_res = db.execute(overdue_stmt).one()
    overdue_amount = Decimal(str(overdue_res[0] or "0.00"))
    overdue_count = overdue_res[1] or 0

    # Unbilled order obligation: sum across active orders of max(0, order.total - sum(invoices on order))
    inv_subq = (
        select(Invoice.order_id, func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")).label("inv_sum"))
        .group_by(Invoice.order_id)
        .subquery()
    )
    unbilled_stmt = (
        select(
            func.coalesce(
                func.sum(
                    func.greatest(
                        Decimal("0.00"),
                        Order.total_amount - func.coalesce(inv_subq.c.inv_sum, Decimal("0.00")),
                    )
                ),
                Decimal("0.00"),
            )
        )
        .outerjoin(inv_subq, Order.id == inv_subq.c.order_id)
        .where(Order.status != "CANCELLED")
    )
    unbilled_obligation = Decimal(str(db.execute(unbilled_stmt).scalar() or "0.00"))

    # -----------------------------
    # E. Inventory
    # -----------------------------
    inv_metric = db.execute(
        select(
            func.count(Inventory.id),
            func.coalesce(func.sum(Inventory.quantity_on_hand), Decimal("0.00")),
            func.count(case((Inventory.quantity_on_hand <= Inventory.reorder_level, 1))),
        )
    ).one()
    total_sku = inv_metric[0] or 0
    total_qoh = Decimal(str(inv_metric[1] or "0.00"))
    low_stock_cnt = inv_metric[2] or 0

    return APIResponse(
        success=True,
        message="Executive dashboard metrics aggregated successfully.",
        data=ExecutiveDashboardResponse(
            as_of_date=today_date,
            enquiries=ExecutiveEnquiryKPIs(
                total_enquiries=total_enquiries,
                won_enquiries=won_count,
                lost_enquiries=lost_count,
                cancelled_enquiries=cancelled_count,
                status_distribution=status_distribution,
            ),
            conversion=ExecutiveConversionKPIs(
                overall_conversion_percentage=conversion_pct,
                formula_label="Overall Conversion (Won / All Leads)",
                total_leads_denominator=total_enquiries,
                won_leads_numerator=won_count,
            ),
            orders=ExecutiveOrderKPIs(
                total_orders=total_orders,
                contract_value=contract_val,
                advance_collected=advance_col,
                balance_due=balance_due,
            ),
            projects=ExecutiveProjectKPIs(
                active_projects=active_count,
                completed_projects=completed_count,
                delayed_projects=delayed_count,
                commissioned_capacity_kw=commissioned_kw,
            ),
            finance=ExecutiveFinanceKPIs(
                total_invoiced=total_inv,
                cash_collected=cash_col,
                outstanding_receivables=out_rec,
                overdue_receivables=overdue_amount,
                overdue_invoices_count=overdue_count,
                unbilled_order_obligation=unbilled_obligation,
            ),
            inventory=ExecutiveInventoryKPIs(
                total_products_tracked=total_sku,
                low_stock_products_count=low_stock_cnt,
                total_quantity_on_hand=total_qoh,
            ),
        ),
    )


# ==========================================
# 2. SALES & CRM ANALYTICS ENDPOINT
# ==========================================

@router.get("/sales", response_model=APIResponse[SalesAnalyticsResponse])
def get_sales_analytics(
    date_from: Optional[date] = Query(None, description="Filter enquiries created from date"),
    date_to: Optional[date] = Query(None, description="Filter enquiries created to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sales Pipeline & Performance Analytics.
    Accessible to SUPER_ADMIN, DIRECTOR, SALES, or users with 'reports.read' or 'enquiries.read'.
    Computes lead funnel, rep performance leaderboard, and quotation acceptance rates.
    """
    _check_analytics_access(
        user=current_user,
        allowed_roles=[SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.SALES],
        required_perms=["reports.read", "enquiries.read"],
    )
    start_dt, end_dt = _parse_date_range(date_from, date_to)

    base_filter = []
    if start_dt:
        base_filter.append(Enquiry.created_at >= start_dt)
    if end_dt:
        base_filter.append(Enquiry.created_at < end_dt)

    # 1. Total & Status distribution
    status_rows = db.execute(
        select(Enquiry.status, func.count(Enquiry.id))
        .where(*base_filter)
        .group_by(Enquiry.status)
    ).all()
    status_map = {r[0]: r[1] for r in status_rows}
    canonical_statuses = ["NEW", "CONTACTED", "SURVEY_REQUESTED", "QUOTED", "WON", "LOST", "CANCELLED"]
    status_dist = {s: status_map.get(s, 0) for s in canonical_statuses}
    total_enquiries = sum(status_dist.values())

    # 2. Source distribution
    source_rows = db.execute(
        select(Enquiry.source, func.count(Enquiry.id))
        .where(*base_filter)
        .group_by(Enquiry.source)
    ).all()
    source_dist = {r[0]: r[1] for r in source_rows}

    # 3. System type distribution
    sys_rows = db.execute(
        select(Enquiry.system_type, func.count(Enquiry.id))
        .where(*base_filter)
        .group_by(Enquiry.system_type)
    ).all()
    sys_dist = {r[0]: r[1] for r in sys_rows}

    # 4. Volume over time (grouped by YYYY-MM)
    time_stmt = (
        select(
            func.to_char(Enquiry.created_at, "YYYY-MM").label("period"),
            func.count(Enquiry.id).label("total_cnt"),
            func.count(case((Enquiry.status == "WON", 1))).label("won_cnt"),
        )
        .where(*base_filter)
        .group_by(func.to_char(Enquiry.created_at, "YYYY-MM"))
        .order_by(func.to_char(Enquiry.created_at, "YYYY-MM").asc())
    )
    time_rows = db.execute(time_stmt).all()
    volume_over_time = [
        SalesVolumeByPeriod(period=r[0] or "N/A", count=r[1], won_count=r[2])
        for r in time_rows
    ]

    # 5. Salesperson performance leaderboard
    # Aggregate assigned, won leads, and won order values traceably
    rep_stmt = (
        select(
            Employee.id,
            User.full_name,
            User.email,
            func.count(distinct(Enquiry.id)).label("assigned_leads"),
            func.count(distinct(case((Enquiry.status == "WON", Enquiry.id)))).label("won_leads"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            and_(Enquiry.status == "WON", Order.status != "CANCELLED"),
                            Order.total_amount,
                        ),
                        else_=Decimal("0.00"),
                    )
                ),
                Decimal("0.00"),
            ).label("won_val"),
        )
        .select_from(Employee)
        .join(User, Employee.user_id == User.id)
        .outerjoin(Enquiry, Enquiry.assigned_sales_id == Employee.id)
        .outerjoin(Quotation, and_(Quotation.enquiry_id == Enquiry.id, Quotation.status == "ACCEPTED"))
        .outerjoin(Order, Order.quotation_id == Quotation.id)
        .group_by(Employee.id, User.full_name, User.email)
        .order_by(func.count(distinct(case((Enquiry.status == "WON", Enquiry.id)))).desc())
    )
    rep_rows = db.execute(rep_stmt).all()
    reps_perf: List[SalesRepPerformance] = []
    for r in rep_rows:
        assigned = r[3] or 0
        won = r[4] or 0
        if assigned > 0:
            conv_pct = round((won / assigned * 100.0), 1)
            reps_perf.append(
                SalesRepPerformance(
                    employee_id=r[0],
                    employee_name=r[1],
                    email=r[2],
                    enquiries_assigned=assigned,
                    enquiries_won=won,
                    conversion_rate_percentage=conv_pct,
                    won_order_value=Decimal(str(r[5] or "0.00")),
                )
            )

    # 6. Quotation acceptance rate & metrics
    # Exclude DRAFT quotations; count commercial sent/terminal opportunities
    quot_stmt = select(
        func.count(Quotation.id),
        func.count(case((Quotation.status == "ACCEPTED", 1))),
        func.coalesce(func.avg(Quotation.gross_amount), Decimal("0.00")),
        func.coalesce(func.avg(Quotation.net_payable_amount), Decimal("0.00")),
    ).where(Quotation.status.in_(["SENT", "ACCEPTED", "REVISED", "REJECTED", "EXPIRED"]))

    if start_dt:
        quot_stmt = quot_stmt.where(Quotation.created_at >= start_dt)
    if end_dt:
        quot_stmt = quot_stmt.where(Quotation.created_at < end_dt)

    quot_res = db.execute(quot_stmt).one()
    tot_comm_quot = quot_res[0] or 0
    acc_quot = quot_res[1] or 0
    quot_acc_rate = round((acc_quot / tot_comm_quot * 100.0), 1) if tot_comm_quot > 0 else 0.0
    avg_gross = Decimal(str(quot_res[2] or "0.00")).quantize(Decimal("0.01"))
    avg_net = Decimal(str(quot_res[3] or "0.00")).quantize(Decimal("0.01"))

    quot_metrics = QuotationConversionMetrics(
        total_commercial_quotations=tot_comm_quot,
        accepted_quotations=acc_quot,
        acceptance_rate_percentage=quot_acc_rate,
        average_quotation_gross=avg_gross,
        average_quotation_net=avg_net,
    )

    return APIResponse(
        success=True,
        message="Sales analytics aggregated successfully.",
        data=SalesAnalyticsResponse(
            total_enquiries=total_enquiries,
            status_distribution=status_dist,
            source_distribution=source_dist,
            system_type_distribution=sys_dist,
            volume_over_time=volume_over_time,
            reps_performance=reps_perf,
            quotations_metric=quot_metrics,
        ),
    )


# ==========================================
# 3. PROJECT & OPERATIONS ANALYTICS ENDPOINT
# ==========================================

@router.get("/projects", response_model=APIResponse[ProjectAnalyticsResponse])
def get_project_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Project & Operations Analytics.
    Accessible to SUPER_ADMIN, DIRECTOR, TECHNICAL_MANAGER, or users with 'projects.read'.
    Computes status distribution, delays, completion cycle durations, and PM workloads.
    """
    _check_analytics_access(
        user=current_user,
        allowed_roles=[SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.TECHNICAL_MANAGER],
        required_perms=["reports.read", "projects.read"],
    )

    today_date = date.today()

    # 1. Status distribution
    status_rows = db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status)
    ).all()
    status_map = {r[0]: r[1] for r in status_rows}
    canonical_statuses = [
        "INITIATED", "PROCUREMENT", "DISPATCHED", "INSTALLATION",
        "COMMISSIONED", "HANDED_OVER", "ON_HOLD", "CANCELLED"
    ]
    status_dist = {s: status_map.get(s, 0) for s in canonical_statuses}
    total_projects = sum(status_dist.values())

    active_statuses = ["INITIATED", "PROCUREMENT", "DISPATCHED", "INSTALLATION", "ON_HOLD"]
    active_count = sum(status_dist.get(s, 0) for s in active_statuses)
    completed_statuses = ["COMMISSIONED", "HANDED_OVER"]
    completed_count = sum(status_dist.get(s, 0) for s in completed_statuses)
    cancelled_count = status_dist.get("CANCELLED", 0)

    # 2. Delayed projects (planned date past, not terminal)
    delayed_stmt = select(func.count(Project.id)).where(
        Project.status.notin_(["COMMISSIONED", "HANDED_OVER", "CANCELLED"]),
        Project.planned_completion_date < today_date,
    )
    delayed_count = db.execute(delayed_stmt).scalar() or 0

    # 3. Average completion duration (actual_completion_date - planned_start_date)
    duration_stmt = select(
        func.avg(Project.actual_completion_date - Project.planned_start_date)
    ).where(
        Project.actual_completion_date.isnot(None),
        Project.status.in_(["COMMISSIONED", "HANDED_OVER"]),
    )
    avg_duration = db.execute(duration_stmt).scalar()
    avg_duration_float = round(float(avg_duration), 1) if avg_duration is not None else None

    # 4. Capacity distribution by system type
    cap_stmt = select(
        Project.system_type,
        func.coalesce(func.sum(Project.system_capacity_kw), Decimal("0.00")),
    ).group_by(Project.system_type)
    cap_rows = db.execute(cap_stmt).all()
    capacity_by_type = {r[0]: Decimal(str(r[1] or "0.00")) for r in cap_rows}

    # 5. Project Manager workload
    pm_stmt = (
        select(
            Employee.id,
            User.full_name,
            func.count(case((Project.status.in_(active_statuses), 1))).label("active_cnt"),
            func.count(case((Project.status.in_(completed_statuses), 1))).label("completed_cnt"),
            func.count(
                case(
                    (
                        and_(
                            Project.status.notin_(["COMMISSIONED", "HANDED_OVER", "CANCELLED"]),
                            Project.planned_completion_date < today_date,
                        ),
                        1,
                    )
                )
            ).label("delayed_cnt"),
            func.coalesce(func.sum(Project.system_capacity_kw), Decimal("0.00")).label("total_kw"),
        )
        .select_from(Employee)
        .join(User, Employee.user_id == User.id)
        .join(Project, Project.project_manager_id == Employee.id)
        .group_by(Employee.id, User.full_name)
        .order_by(func.count(Project.id).desc())
    )
    pm_rows = db.execute(pm_stmt).all()
    pm_workloads = [
        ProjectManagerWorkload(
            employee_id=r[0],
            employee_name=r[1],
            active_projects=r[2] or 0,
            completed_projects=r[3] or 0,
            delayed_projects=r[4] or 0,
            total_capacity_kw=Decimal(str(r[5] or "0.00")),
        )
        for r in pm_rows
    ]

    # 6. Installation schedule workload
    sched_stmt = (
        select(InstallationSchedule.status, func.count(InstallationSchedule.id))
        .group_by(InstallationSchedule.status)
    )
    sched_rows = db.execute(sched_stmt).all()
    schedule_workload = [
        InstallationScheduleWorkload(status=r[0], count=r[1])
        for r in sched_rows
    ]

    return APIResponse(
        success=True,
        message="Project analytics aggregated successfully.",
        data=ProjectAnalyticsResponse(
            total_projects=total_projects,
            active_projects=active_count,
            completed_projects=completed_count,
            delayed_projects=delayed_count,
            cancelled_projects=cancelled_count,
            status_distribution=status_dist,
            average_completion_duration_days=avg_duration_float,
            capacity_distribution_by_type=capacity_by_type,
            project_managers_workload=pm_workloads,
            schedule_workload=schedule_workload,
        ),
    )


# ==========================================
# 4. INVENTORY ANALYTICS ENDPOINT
# ==========================================

@router.get("/inventory", response_model=APIResponse[InventoryAnalyticsResponse])
def get_inventory_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inventory & Warehouse Analytics.
    Accessible to SUPER_ADMIN, DIRECTOR, WAREHOUSE_PROCUREMENT, TECHNICAL_MANAGER, or users with 'inventory.read'.
    Computes stock balances, valuation, reorder alerts, and component status.
    """
    _check_analytics_access(
        user=current_user,
        allowed_roles=[
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.TECHNICAL_MANAGER,
        ],
        required_perms=["reports.read", "inventory.read"],
    )

    # 1. Total SKU count, QOH, reserved, available, and valuation
    summary_stmt = select(
        func.count(Inventory.id),
        func.coalesce(func.sum(Inventory.quantity_on_hand), Decimal("0.00")),
        func.coalesce(func.sum(Inventory.reserved_quantity), Decimal("0.00")),
        func.coalesce(func.sum(Inventory.quantity_available), Decimal("0.00")),
        func.count(case((Inventory.quantity_on_hand <= Inventory.reorder_level, 1))),
        func.coalesce(func.sum(Inventory.quantity_on_hand * Inventory.average_unit_cost), Decimal("0.00")),
    )
    sum_res = db.execute(summary_stmt).one()
    total_sku = sum_res[0] or 0
    total_qoh = Decimal(str(sum_res[1] or "0.00"))
    total_res = Decimal(str(sum_res[2] or "0.00"))
    total_avail = Decimal(str(sum_res[3] or "0.00"))
    low_stock_cnt = sum_res[4] or 0
    total_val = Decimal(str(sum_res[5] or "0.00")).quantize(Decimal("0.01"))

    # 2. Total Dispatched quantity (from DispatchItem if present)
    dispatch_stmt = select(
        func.coalesce(func.sum(DispatchItem.dispatched_quantity), Decimal("0.00"))
    )
    total_dispatched = Decimal(str(db.execute(dispatch_stmt).scalar() or "0.00"))

    # 3. Detailed items query
    items_stmt = (
        select(
            Product.id,
            Product.product_code,
            Product.name,
            Product.category,
            Inventory.quantity_on_hand,
            Inventory.reserved_quantity,
            Inventory.quantity_available,
            Inventory.average_unit_cost,
            Inventory.reorder_level,
        )
        .join(Product, Inventory.product_id == Product.id)
        .order_by(Inventory.quantity_on_hand.desc())
    )
    item_rows = db.execute(items_stmt).all()

    all_items: List[InventoryProductItem] = []
    low_stock_items: List[InventoryProductItem] = []

    for r in item_rows:
        qoh = Decimal(str(r[4] or "0.00"))
        res_qty = Decimal(str(r[5] or "0.00"))
        avail = Decimal(str(r[6] or "0.00"))
        cost = Decimal(str(r[7] or "0.00"))
        reorder = Decimal(str(r[8] or "0.00"))
        val = (qoh * cost).quantize(Decimal("0.01"))
        st = "LOW_STOCK" if qoh <= reorder else "OK"

        item_obj = InventoryProductItem(
            product_id=r[0],
            product_code=r[1],
            product_name=r[2],
            category=r[3],
            quantity_on_hand=qoh,
            reserved_quantity=res_qty,
            quantity_available=avail,
            average_unit_cost=cost,
            reorder_level=reorder,
            stock_status=st,
            valuation=val,
        )
        all_items.append(item_obj)
        if st == "LOW_STOCK":
            low_stock_items.append(item_obj)

    return APIResponse(
        success=True,
        message="Inventory analytics aggregated successfully.",
        data=InventoryAnalyticsResponse(
            total_sku_count=total_sku,
            total_quantity_on_hand=total_qoh,
            total_reserved_quantity=total_res,
            total_available_quantity=total_avail,
            low_stock_sku_count=low_stock_cnt,
            total_stock_valuation=total_val,
            total_dispatched_quantity=total_dispatched,
            low_stock_items=low_stock_items,
            top_stock_items=all_items[:10],
        ),
    )


# ==========================================
# 5. FINANCIAL ANALYTICS ENDPOINT
# ==========================================

@router.get("/finance", response_model=APIResponse[FinanceAnalyticsResponse])
def get_financial_analytics(
    date_from: Optional[date] = Query(None, description="Filter invoices and payments from date"),
    date_to: Optional[date] = Query(None, description="Filter invoices and payments to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Financial & Billing Analytics.
    Accessible to SUPER_ADMIN, DIRECTOR, FINANCE_ACCOUNTS, or users with 'reports.read' or 'finance.read'.
    Computes billed revenue, collected cash, receivables aging, milestone breakdown, and estimated gross margin.
    """
    _check_analytics_access(
        user=current_user,
        allowed_roles=[SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.FINANCE_ACCOUNTS],
        required_perms=["reports.read", "finance.read"],
    )

    today_date = date.today()

    # 1. Total Invoiced (filter on invoice_date)
    inv_stmt = select(func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")))
    if date_from:
        inv_stmt = inv_stmt.where(Invoice.invoice_date >= date_from)
    if date_to:
        inv_stmt = inv_stmt.where(Invoice.invoice_date <= date_to)
    total_invoiced = Decimal(str(db.execute(inv_stmt).scalar() or "0.00"))

    # 2. Cash Collected (filter on payment_date, COMPLETED status only)
    pay_stmt = select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(Payment.status == "COMPLETED")
    if date_from:
        pay_stmt = pay_stmt.where(Payment.payment_date >= date_from)
    if date_to:
        pay_stmt = pay_stmt.where(Payment.payment_date <= date_to)
    cash_collected = Decimal(str(db.execute(pay_stmt).scalar() or "0.00"))

    # 3. Outstanding Receivables (Invoices with balance_amount > 0)
    out_stmt = select(func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00"))).where(Invoice.balance_amount > 0)
    outstanding_rec = Decimal(str(db.execute(out_stmt).scalar() or "0.00"))

    # 4. Overdue Receivables (balance > 0 and due_date < today)
    overdue_stmt = select(
        func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00")),
        func.count(Invoice.id),
    ).where(
        Invoice.balance_amount > 0,
        Invoice.due_date < today_date,
    )
    overdue_res = db.execute(overdue_stmt).one()
    overdue_amount = Decimal(str(overdue_res[0] or "0.00"))
    overdue_count = overdue_res[1] or 0

    # 5. Unallocated & Allocated Cash
    unalloc_stmt = select(func.coalesce(func.sum(Payment.unallocated_amount), Decimal("0.00"))).where(Payment.status == "COMPLETED")
    unallocated_cash = Decimal(str(db.execute(unalloc_stmt).scalar() or "0.00"))

    alloc_stmt = select(func.coalesce(func.sum(PaymentAllocation.allocated_amount), Decimal("0.00")))
    allocated_cash = Decimal(str(db.execute(alloc_stmt).scalar() or "0.00"))

    # 6. Unbilled Order Obligation: Per active order, max(0, order.total - sum(invoices on order))
    inv_subq = (
        select(Invoice.order_id, func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")).label("inv_sum"))
        .group_by(Invoice.order_id)
        .subquery()
    )
    unbilled_stmt = (
        select(
            func.coalesce(
                func.sum(
                    func.greatest(
                        Decimal("0.00"),
                        Order.total_amount - func.coalesce(inv_subq.c.inv_sum, Decimal("0.00")),
                    )
                ),
                Decimal("0.00"),
            )
        )
        .outerjoin(inv_subq, Order.id == inv_subq.c.order_id)
        .where(Order.status != "CANCELLED")
    )
    unbilled_obligation = Decimal(str(db.execute(unbilled_stmt).scalar() or "0.00"))

    # 7. Aging Receivables Buckets
    aging_stmt = select(
        case(
            (Invoice.due_date >= today_date, "Current"),
            (Invoice.due_date >= today_date - timedelta(days=30), "1-30 Days"),
            (Invoice.due_date >= today_date - timedelta(days=60), "31-60 Days"),
            (Invoice.due_date >= today_date - timedelta(days=90), "61-90 Days"),
            else_="90+ Days",
        ).label("bucket"),
        func.count(Invoice.id),
        func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00")),
    ).where(Invoice.balance_amount > 0).group_by("bucket")

    aging_rows = db.execute(aging_stmt).all()
    aging_map = {r[0]: (r[1], Decimal(str(r[2] or "0.00"))) for r in aging_rows}
    canonical_buckets = ["Current", "1-30 Days", "31-60 Days", "61-90 Days", "90+ Days"]
    aging_buckets = [
        AgingReceivablesBucket(
            bucket=b,
            count=aging_map.get(b, (0, Decimal("0.00")))[0],
            amount=aging_map.get(b, (0, Decimal("0.00")))[1],
        )
        for b in canonical_buckets
    ]

    # 8. Milestone breakdown
    milestone_stmt = select(
        Invoice.invoice_type,
        func.count(Invoice.id),
        func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.paid_amount), Decimal("0.00")),
        func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00")),
    ).group_by(Invoice.invoice_type)
    milestone_rows = db.execute(milestone_stmt).all()
    milestone_breakdown = [
        MilestoneInvoiceBreakdown(
            invoice_type=r[0],
            count=r[1],
            total_amount=Decimal(str(r[2] or "0.00")),
            paid_amount=Decimal(str(r[3] or "0.00")),
            balance_amount=Decimal(str(r[4] or "0.00")),
        )
        for r in milestone_rows
    ]

    # 9. Monthly Cash Flow Trend (Invoiced vs Collected by YYYY-MM)
    inv_monthly = db.execute(
        select(
            func.to_char(Invoice.invoice_date, "YYYY-MM").label("month"),
            func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00")),
        )
        .group_by(func.to_char(Invoice.invoice_date, "YYYY-MM"))
    ).all()
    inv_month_map = {r[0]: Decimal(str(r[1] or "0.00")) for r in inv_monthly if r[0]}

    pay_monthly = db.execute(
        select(
            func.to_char(Payment.payment_date, "YYYY-MM").label("month"),
            func.coalesce(func.sum(Payment.amount), Decimal("0.00")),
        )
        .where(Payment.status == "COMPLETED")
        .group_by(func.to_char(Payment.payment_date, "YYYY-MM"))
    ).all()
    pay_month_map = {r[0]: Decimal(str(r[1] or "0.00")) for r in pay_monthly if r[0]}

    all_months = sorted(list(set(inv_month_map.keys()) | set(pay_month_map.keys())))
    cash_flow_trend = [
        MonthlyCashFlow(
            month=m,
            invoiced_amount=inv_month_map.get(m, Decimal("0.00")),
            collected_amount=pay_month_map.get(m, Decimal("0.00")),
        )
        for m in all_months[-6:]  # Last 6 active billing months
    ]

    # 10. Estimated Gross Margin (Quotation baseline)
    margin_stmt = (
        select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), Decimal("0.00")),
            func.coalesce(func.sum(Quotation.total_product_cost), Decimal("0.00")),
            func.coalesce(func.sum(Quotation.installation_cost), Decimal("0.00")),
        )
        .join(Quotation, Order.quotation_id == Quotation.id)
        .where(Order.status != "CANCELLED")
    )
    margin_res = db.execute(margin_stmt).one()
    ord_cnt = margin_res[0] or 0
    contract_rev = Decimal(str(margin_res[1] or "0.00"))
    est_prod_cost = Decimal(str(margin_res[2] or "0.00"))
    est_inst_cost = Decimal(str(margin_res[3] or "0.00"))
    est_margin = contract_rev - est_prod_cost - est_inst_cost
    est_margin_pct = round(float(est_margin / contract_rev * 100), 1) if contract_rev > 0 else 0.0

    margin_metric = EstimatedGrossMarginMetric(
        eligible_orders_count=ord_cnt,
        contracted_revenue=contract_rev,
        estimated_product_cost=est_prod_cost,
        estimated_installation_cost=est_inst_cost,
        estimated_gross_margin=est_margin,
        estimated_gross_margin_percentage=est_margin_pct,
    )

    accounting_notes = [
        "Cash collected reflects strictly COMPLETED customer payment receipts. Payment allocations are non-cash internal reconciliations.",
        "Order contract backlog and unbilled obligations are matched per active order to avoid false global offsetting.",
        "Receivables aging is calculated from invoice due_date relative to current system date.",
    ]

    return APIResponse(
        success=True,
        message="Financial analytics aggregated successfully.",
        data=FinanceAnalyticsResponse(
            total_invoiced=total_invoiced,
            cash_collected=cash_collected,
            outstanding_receivables=outstanding_rec,
            overdue_receivables=overdue_amount,
            overdue_invoices_count=overdue_count,
            unallocated_cash=unallocated_cash,
            allocated_cash=allocated_cash,
            unbilled_order_obligation=unbilled_obligation,
            aging_buckets=aging_buckets,
            milestone_breakdown=milestone_breakdown,
            cash_flow_trend=cash_flow_trend,
            estimated_gross_margin=margin_metric,
            accounting_notes=accounting_notes,
        ),
    )


# ==========================================
# 6. OPERATIONAL WORKFLOW ANALYTICS ENDPOINT (PHASES 6-13)
# ==========================================

@router.get("/operations", response_model=APIResponse[OperationalAnalyticsResponse])
def get_operations_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Consolidated Operational Workflow Analytics.
    Aggregates real-time KPIs across Procurement, Inventory, Dispatch, Installations,
    Service/Warranty, and PM Surya Ghar Subsidy Liaison.
    """
    _check_analytics_access(
        user=current_user,
        allowed_roles=[
            SystemRole.SUPER_ADMIN,
            SystemRole.DIRECTOR,
            SystemRole.TECHNICAL_MANAGER,
            SystemRole.WAREHOUSE_PROCUREMENT,
            SystemRole.FIELD_TECHNICIAN,
            SystemRole.SERVICE_WARRANTY,
            SystemRole.FINANCE_ACCOUNTS,
            SystemRole.SALES,
        ],
        required_perms=["reports.read", "analytics:read"],
    )

    # 1. Procurement KPIs
    total_suppliers = db.execute(select(func.count(Supplier.id))).scalar() or 0
    total_pos = db.execute(select(func.count(PurchaseOrder.id))).scalar() or 0
    total_po_val = db.execute(select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0))).scalar() or Decimal("0.00")
    pending_pos = db.execute(select(func.count(PurchaseOrder.id)).where(PurchaseOrder.status.in_(["ISSUED", "PARTIALLY_DELIVERED"]))).scalar() or 0
    grn_count = db.execute(select(func.count(GoodsReceipt.id))).scalar() or 0
    low_stock_count = db.execute(select(func.count(Inventory.id)).where(Inventory.quantity_available <= Inventory.reorder_level)).scalar() or 0

    procurement_kpis = ProcurementOperationsKPIs(
        total_suppliers=total_suppliers,
        total_purchase_orders=total_pos,
        total_po_value=Decimal(str(total_po_val)),
        pending_receipt_pos_count=pending_pos,
        goods_receipts_count=grn_count,
        low_stock_alerts_count=low_stock_count,
    )

    # 2. Dispatch KPIs
    total_dispatches = db.execute(select(func.count(Dispatch.id))).scalar() or 0
    in_transit_dispatches = db.execute(select(func.count(Dispatch.id)).where(Dispatch.dispatch_status.in_(["DISPATCHED", "IN_TRANSIT"]))).scalar() or 0
    delivered_dispatches = db.execute(select(func.count(Dispatch.id)).where(Dispatch.dispatch_status == "DELIVERED")).scalar() or 0
    serialized_items = db.execute(select(func.count(SerialNumber.id))).scalar() or 0

    dispatch_kpis = DispatchOperationsKPIs(
        total_dispatches=total_dispatches,
        dispatches_in_transit=in_transit_dispatches,
        dispatches_delivered=delivered_dispatches,
        total_serialized_items_tracked=serialized_items,
    )

    # 3. Installation KPIs
    total_schedules = db.execute(select(func.count(InstallationSchedule.id))).scalar() or 0
    active_installations = db.execute(select(func.count(Installation.id)).where(Installation.status.in_(["IN_PROGRESS", "SCHEDULED", "PENDING_INSPECTION"]))).scalar() or 0
    completed_installations = db.execute(select(func.count(Installation.id)).where(Installation.status == "COMPLETED")).scalar() or 0
    worklogs_count = db.execute(select(func.count(TechnicianWorklog.id))).scalar() or 0
    tests_count = db.execute(select(func.count(InstallationTest.id))).scalar() or 0

    installation_kpis = InstallationOperationsKPIs(
        total_schedules=total_schedules,
        active_installations=active_installations,
        completed_installations=completed_installations,
        worklogs_recorded=worklogs_count,
        tests_completed=tests_count,
    )

    # 4. Service & Warranty KPIs
    active_warranties = db.execute(select(func.count(WarrantyRecord.id)).where(WarrantyRecord.status == "ACTIVE")).scalar() or 0
    open_tickets = db.execute(select(func.count(ServiceTicket.id)).where(ServiceTicket.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS"]))).scalar() or 0
    critical_tickets = db.execute(select(func.count(ServiceTicket.id)).where(and_(ServiceTicket.priority == "CRITICAL", ServiceTicket.status.not_in(["RESOLVED", "CLOSED", "CANCELLED"])))).scalar() or 0
    resolved_tickets = db.execute(select(func.count(ServiceTicket.id)).where(ServiceTicket.status.in_(["RESOLVED", "CLOSED"]))).scalar() or 0
    visits_completed = db.execute(select(func.count(ServiceVisit.id)).where(ServiceVisit.visit_status == "COMPLETED")).scalar() or 0
    replacements_count = db.execute(select(func.count(Replacement.id))).scalar() or 0

    service_kpis = ServiceWarrantyOperationsKPIs(
        active_warranties_count=active_warranties,
        open_service_tickets_count=open_tickets,
        critical_tickets_count=critical_tickets,
        resolved_tickets_count=resolved_tickets,
        technician_visits_completed=visits_completed,
        components_replaced_count=replacements_count,
    )

    # 5. Subsidy KPIs
    total_subsidy_apps = db.execute(select(func.count(SubsidyApplication.id))).scalar() or 0
    submitted_apps = db.execute(select(func.count(SubsidyApplication.id)).where(SubsidyApplication.status.in_(["SUBMITTED_TO_DISCOM", "INSPECTION_SCHEDULED", "INSPECTION_COMPLETED"]))).scalar() or 0
    approved_apps = db.execute(select(func.count(SubsidyApplication.id)).where(SubsidyApplication.status == "APPROVED")).scalar() or 0
    disbursed_apps = db.execute(select(func.count(SubsidyApplication.id)).where(SubsidyApplication.status == "SUBSIDY_DISBURSED")).scalar() or 0
    total_subsidy_disbursed = db.execute(select(func.coalesce(func.sum(SubsidyPayment.disbursed_amount), 0))).scalar() or Decimal("0.00")

    subsidy_kpis = SubsidyOperationsKPIs(
        total_applications=total_subsidy_apps,
        submitted_applications=submitted_apps,
        approved_applications=approved_apps,
        disbursed_applications=disbursed_apps,
        total_subsidy_disbursed=Decimal(str(total_subsidy_disbursed)),
    )

    # 6. Project Pipeline Execution Stages
    stage_rows = db.execute(
        select(Project.status, func.count(Project.id)).group_by(Project.status).order_by(func.count(Project.id).desc())
    ).all()
    pipeline_stages = [ProjectStageExecution(stage=str(row[0] or "UNKNOWN"), count=int(row[1])) for row in stage_rows]

    return APIResponse(
        success=True,
        message="Operational analytics calculated successfully.",
        data=OperationalAnalyticsResponse(
            procurement=procurement_kpis,
            dispatch=dispatch_kpis,
            installation=installation_kpis,
            service_warranty=service_kpis,
            subsidy=subsidy_kpis,
            pipeline_stages=pipeline_stages,
        ),
    )


# ==========================================
# 7. CSV DATA EXPORT ENDPOINT
# ==========================================

VALID_REPORT_TYPES = [
    "sales_summary",
    "sales_reps",
    "projects_summary",
    "inventory_stock",
    "finance_invoices",
    "finance_payments",
    "receivables_aging",
]

@router.get("/export")
def export_analytics_csv(
    report_type: str = Query(..., description=f"Type of report to export: {', '.join(VALID_REPORT_TYPES)}"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export verified tabular business data as Excel-compatible CSV.
    Enforces strict backend authorization and applies identical filters.
    Includes UTF-8 BOM (\ufeff) for proper rendering in Microsoft Excel.
    """
    _assert_internal_staff(current_user)

    if report_type not in VALID_REPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report_type '{report_type}'. Allowed types: {', '.join(VALID_REPORT_TYPES)}.",
        )

    # Route-level RBAC check based on report type
    if report_type in ["sales_summary", "sales_reps"]:
        _check_analytics_access(current_user, [SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.SALES], ["reports.read", "enquiries.read"])
    elif report_type == "projects_summary":
        _check_analytics_access(current_user, [SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.TECHNICAL_MANAGER], ["reports.read", "projects.read"])
    elif report_type == "inventory_stock":
        _check_analytics_access(current_user, [SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.WAREHOUSE_PROCUREMENT], ["reports.read", "inventory.read"])
    elif report_type in ["finance_invoices", "finance_payments", "receivables_aging"]:
        _check_analytics_access(current_user, [SystemRole.SUPER_ADMIN, SystemRole.DIRECTOR, SystemRole.FINANCE_ACCOUNTS], ["reports.read", "finance.read"])

    output = io.StringIO()
    writer = csv.writer(output, dialect="excel")

    # Generate CSV rows based on validated report_type
    if report_type == "sales_summary":
        writer.writerow(["Enquiry Number", "Customer Name", "Source", "System Type", "Capacity (kW)", "Status", "Created Date"])
        q = select(Enquiry).options(selectinload(Enquiry.customer)).order_by(Enquiry.created_at.desc())
        start_dt, end_dt = _parse_date_range(date_from, date_to)
        if start_dt:
            q = q.where(Enquiry.created_at >= start_dt)
        if end_dt:
            q = q.where(Enquiry.created_at < end_dt)
        for e in db.execute(q).scalars().all():
            writer.writerow([
                e.enquiry_number,
                e.customer.full_name if e.customer else "N/A",
                e.source,
                e.system_type,
                str(e.proposed_capacity_kw),
                e.status,
                e.created_at.strftime("%Y-%m-%d %H:%M:%S") if e.created_at else "",
            ])

    elif report_type == "sales_reps":
        writer.writerow(["Sales Representative", "Email", "Assigned Leads", "Won Leads", "Conversion Rate %", "Won Order Value (INR)"])
        stmt = (
            select(
                User.full_name,
                User.email,
                func.count(distinct(Enquiry.id)),
                func.count(distinct(case((Enquiry.status == "WON", Enquiry.id)))),
                func.coalesce(
                    func.sum(
                        case(
                            ((and_(Enquiry.status == "WON", Order.status != "CANCELLED")), Order.total_amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ),
            )
            .select_from(Employee)
            .join(User, Employee.user_id == User.id)
            .outerjoin(Enquiry, Enquiry.assigned_sales_id == Employee.id)
            .outerjoin(Quotation, and_(Quotation.enquiry_id == Enquiry.id, Quotation.status == "ACCEPTED"))
            .outerjoin(Order, Order.quotation_id == Quotation.id)
            .group_by(User.full_name, User.email)
        )
        for r in db.execute(stmt).all():
            assigned = r[2] or 0
            won = r[3] or 0
            conv = round((won / assigned * 100.0), 1) if assigned > 0 else 0.0
            writer.writerow([r[0], r[1] or "", assigned, won, conv, str(r[4] or "0.00")])

    elif report_type == "projects_summary":
        writer.writerow(["Project Code", "Customer Name", "System Type", "Capacity (kW)", "Status", "Planned Start", "Planned End", "Actual End", "Project Manager"])
        q = (
            select(Project)
            .options(
                selectinload(Project.customer),
                selectinload(Project.project_manager).selectinload(Employee.user),
            )
            .order_by(Project.created_at.desc())
        )
        for p in db.execute(q).scalars().all():
            pm_name = p.project_manager.user.full_name if (p.project_manager and p.project_manager.user) else "Unassigned"
            writer.writerow([
                p.project_code,
                p.customer.full_name if p.customer else "N/A",
                p.system_type,
                str(p.system_capacity_kw),
                p.status,
                str(p.planned_start_date),
                str(p.planned_completion_date),
                str(p.actual_completion_date or ""),
                pm_name,
            ])

    elif report_type == "inventory_stock":
        writer.writerow(["Product Code", "Product Name", "Category", "Quantity On Hand", "Reserved Quantity", "Available Quantity", "Unit Cost (INR)", "Reorder Level", "Status", "Valuation (INR)"])
        q = (
            select(Inventory)
            .options(selectinload(Inventory.product))
            .order_by(Inventory.quantity_on_hand.desc())
        )
        for inv in db.execute(q).scalars().all():
            prod = inv.product
            qoh = Decimal(str(inv.quantity_on_hand))
            cost = Decimal(str(inv.average_unit_cost))
            val = (qoh * cost).quantize(Decimal("0.01"))
            st = "LOW_STOCK" if qoh <= inv.reorder_level else "OK"
            writer.writerow([
                prod.product_code if prod else "N/A",
                prod.name if prod else "N/A",
                prod.category if prod else "N/A",
                str(qoh),
                str(inv.reserved_quantity),
                str(inv.quantity_available),
                str(cost),
                str(inv.reorder_level),
                st,
                str(val),
            ])

    elif report_type == "finance_invoices":
        writer.writerow(["Invoice Number", "Customer Name", "Order Number", "Invoice Type", "Invoice Date", "Due Date", "Subtotal (INR)", "Tax (INR)", "Total (INR)", "Paid (INR)", "Balance (INR)", "Status"])
        q = (
            select(Invoice)
            .options(selectinload(Invoice.customer), selectinload(Invoice.order))
            .order_by(Invoice.invoice_date.desc())
        )
        if date_from:
            q = q.where(Invoice.invoice_date >= date_from)
        if date_to:
            q = q.where(Invoice.invoice_date <= date_to)
        for inv in db.execute(q).scalars().all():
            writer.writerow([
                inv.invoice_number,
                inv.customer.full_name if inv.customer else "N/A",
                inv.order.order_number if inv.order else "N/A",
                inv.invoice_type,
                str(inv.invoice_date),
                str(inv.due_date),
                str(inv.subtotal),
                str(inv.tax_amount),
                str(inv.total_amount),
                str(inv.paid_amount),
                str(inv.balance_amount),
                inv.payment_status,
            ])

    elif report_type == "finance_payments":
        writer.writerow(["Payment Number", "Customer Name", "Order Number", "Payment Date", "Payment Method", "Amount (INR)", "Unallocated (INR)", "Status", "Reference"])
        q = (
            select(Payment)
            .options(selectinload(Payment.customer), selectinload(Payment.order))
            .order_by(Payment.payment_date.desc())
        )
        if date_from:
            q = q.where(Payment.payment_date >= date_from)
        if date_to:
            q = q.where(Payment.payment_date <= date_to)
        for pay in db.execute(q).scalars().all():
            writer.writerow([
                pay.payment_number,
                pay.customer.full_name if pay.customer else "N/A",
                pay.order.order_number if pay.order else "N/A",
                str(pay.payment_date),
                pay.payment_method,
                str(pay.amount),
                str(pay.unallocated_amount),
                pay.status,
                pay.transaction_reference or "",
            ])

    elif report_type == "receivables_aging":
        writer.writerow(["Invoice Number", "Customer Name", "Customer Phone", "Due Date", "Days Overdue", "Invoice Amount (INR)", "Outstanding Balance (INR)", "Aging Bucket"])
        today = date.today()
        q = (
            select(Invoice)
            .options(selectinload(Invoice.customer))
            .where(Invoice.balance_amount > 0)
            .order_by(Invoice.due_date.asc())
        )
        for inv in db.execute(q).scalars().all():
            days_overdue = (today - inv.due_date).days if inv.due_date < today else 0
            if inv.due_date >= today:
                bucket = "Current"
            elif days_overdue <= 30:
                bucket = "1-30 Days"
            elif days_overdue <= 60:
                bucket = "31-60 Days"
            elif days_overdue <= 90:
                bucket = "61-90 Days"
            else:
                bucket = "90+ Days"
            writer.writerow([
                inv.invoice_number,
                inv.customer.full_name if inv.customer else "N/A",
                inv.customer.phone if inv.customer else "N/A",
                str(inv.due_date),
                days_overdue,
                str(inv.total_amount),
                str(inv.balance_amount),
                bucket,
            ])

    csv_data = output.getvalue()
    # Add UTF-8 BOM so Microsoft Excel cleanly detects character encoding
    bom_csv_bytes = b"\xef\xbb\xbf" + csv_data.encode("utf-8")

    filename = f"sims_{report_type}_{date.today().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        io.BytesIO(bom_csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
