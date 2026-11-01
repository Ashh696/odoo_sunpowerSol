from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date, datetime


# ==========================================
# COMMON & FILTER SCHEMAS
# ==========================================

class DateRangeFilter(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None


# ==========================================
# EXECUTIVE DASHBOARD SCHEMAS
# ==========================================

class ExecutiveEnquiryKPIs(BaseModel):
    total_enquiries: int = 0
    won_enquiries: int = 0
    lost_enquiries: int = 0
    cancelled_enquiries: int = 0
    status_distribution: Dict[str, int] = Field(default_factory=dict)


class ExecutiveConversionKPIs(BaseModel):
    overall_conversion_percentage: float = 0.0
    formula_label: str = "Overall Conversion (Won / All Leads)"
    total_leads_denominator: int = 0
    won_leads_numerator: int = 0


class ExecutiveOrderKPIs(BaseModel):
    total_orders: int = 0
    contract_value: Decimal = Decimal("0.00")
    advance_collected: Decimal = Decimal("0.00")
    balance_due: Decimal = Decimal("0.00")


class ExecutiveProjectKPIs(BaseModel):
    active_projects: int = 0
    completed_projects: int = 0
    delayed_projects: int = 0
    commissioned_capacity_kw: Decimal = Decimal("0.00")


class ExecutiveFinanceKPIs(BaseModel):
    total_invoiced: Decimal = Decimal("0.00")
    cash_collected: Decimal = Decimal("0.00")
    outstanding_receivables: Decimal = Decimal("0.00")
    overdue_receivables: Decimal = Decimal("0.00")
    overdue_invoices_count: int = 0
    unbilled_order_obligation: Decimal = Decimal("0.00")


class ExecutiveInventoryKPIs(BaseModel):
    total_products_tracked: int = 0
    low_stock_products_count: int = 0
    total_quantity_on_hand: Decimal = Decimal("0.00")


class ExecutiveDashboardResponse(BaseModel):
    as_of_date: date
    enquiries: ExecutiveEnquiryKPIs
    conversion: ExecutiveConversionKPIs
    orders: ExecutiveOrderKPIs
    projects: ExecutiveProjectKPIs
    finance: ExecutiveFinanceKPIs
    inventory: ExecutiveInventoryKPIs


# ==========================================
# SALES ANALYTICS SCHEMAS
# ==========================================

class SalesRepPerformance(BaseModel):
    employee_id: int
    employee_name: str
    email: Optional[str] = None
    enquiries_assigned: int = 0
    enquiries_won: int = 0
    conversion_rate_percentage: float = 0.0
    won_order_value: Decimal = Decimal("0.00")


class QuotationConversionMetrics(BaseModel):
    total_commercial_quotations: int = 0  # Sent/terminal quotations (excluding draft)
    accepted_quotations: int = 0
    acceptance_rate_percentage: float = 0.0
    average_quotation_gross: Decimal = Decimal("0.00")
    average_quotation_net: Decimal = Decimal("0.00")


class SalesVolumeByPeriod(BaseModel):
    period: str  # e.g. "2026-10"
    count: int = 0
    won_count: int = 0


class SalesAnalyticsResponse(BaseModel):
    total_enquiries: int = 0
    status_distribution: Dict[str, int] = Field(default_factory=dict)
    source_distribution: Dict[str, int] = Field(default_factory=dict)
    system_type_distribution: Dict[str, int] = Field(default_factory=dict)
    volume_over_time: List[SalesVolumeByPeriod] = Field(default_factory=list)
    reps_performance: List[SalesRepPerformance] = Field(default_factory=list)
    quotations_metric: QuotationConversionMetrics


# ==========================================
# PROJECT & OPERATIONS ANALYTICS SCHEMAS
# ==========================================

class ProjectManagerWorkload(BaseModel):
    employee_id: int
    employee_name: str
    active_projects: int = 0
    completed_projects: int = 0
    delayed_projects: int = 0
    total_capacity_kw: Decimal = Decimal("0.00")


class InstallationScheduleWorkload(BaseModel):
    status: str
    count: int = 0


class ProjectAnalyticsResponse(BaseModel):
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    delayed_projects: int = 0
    cancelled_projects: int = 0
    status_distribution: Dict[str, int] = Field(default_factory=dict)
    average_completion_duration_days: Optional[float] = None
    capacity_distribution_by_type: Dict[str, Decimal] = Field(default_factory=dict)
    project_managers_workload: List[ProjectManagerWorkload] = Field(default_factory=list)
    schedule_workload: List[InstallationScheduleWorkload] = Field(default_factory=list)


# ==========================================
# INVENTORY ANALYTICS SCHEMAS
# ==========================================

class InventoryProductItem(BaseModel):
    product_id: int
    product_code: str
    product_name: str
    category: str
    quantity_on_hand: Decimal
    reserved_quantity: Decimal
    quantity_available: Decimal
    average_unit_cost: Decimal
    reorder_level: Decimal
    stock_status: str  # "OK" or "LOW_STOCK"
    valuation: Decimal


class InventoryAnalyticsResponse(BaseModel):
    total_sku_count: int = 0
    total_quantity_on_hand: Decimal = Decimal("0.00")
    total_reserved_quantity: Decimal = Decimal("0.00")
    total_available_quantity: Decimal = Decimal("0.00")
    low_stock_sku_count: int = 0
    total_stock_valuation: Decimal = Decimal("0.00")
    total_dispatched_quantity: Decimal = Decimal("0.00")
    low_stock_items: List[InventoryProductItem] = Field(default_factory=list)
    top_stock_items: List[InventoryProductItem] = Field(default_factory=list)


# ==========================================
# FINANCE ANALYTICS SCHEMAS
# ==========================================

class AgingReceivablesBucket(BaseModel):
    bucket: str  # "Current", "1-30 Days", "31-60 Days", "61-90 Days", "90+ Days"
    count: int = 0
    amount: Decimal = Decimal("0.00")


class MilestoneInvoiceBreakdown(BaseModel):
    invoice_type: str
    count: int = 0
    total_amount: Decimal = Decimal("0.00")
    paid_amount: Decimal = Decimal("0.00")
    balance_amount: Decimal = Decimal("0.00")


class MonthlyCashFlow(BaseModel):
    month: str  # "2026-10"
    invoiced_amount: Decimal = Decimal("0.00")
    collected_amount: Decimal = Decimal("0.00")


class EstimatedGrossMarginMetric(BaseModel):
    eligible_orders_count: int = 0
    contracted_revenue: Decimal = Decimal("0.00")
    estimated_product_cost: Decimal = Decimal("0.00")
    estimated_installation_cost: Decimal = Decimal("0.00")
    estimated_gross_margin: Decimal = Decimal("0.00")
    estimated_gross_margin_percentage: float = 0.0
    disclosure_note: str = (
        "Estimated gross margin is calculated from quotation baseline cost estimates "
        "(gross_amount - total_product_cost - installation_cost) on accepted orders. "
        "Actual job costing is deferred until procurement expense and subcontractor accounting is operational."
    )


class FinanceAnalyticsResponse(BaseModel):
    total_invoiced: Decimal = Decimal("0.00")
    cash_collected: Decimal = Decimal("0.00")
    outstanding_receivables: Decimal = Decimal("0.00")
    overdue_receivables: Decimal = Decimal("0.00")
    overdue_invoices_count: int = 0
    unallocated_cash: Decimal = Decimal("0.00")
    allocated_cash: Decimal = Decimal("0.00")
    unbilled_order_obligation: Decimal = Decimal("0.00")
    aging_buckets: List[AgingReceivablesBucket] = Field(default_factory=list)
    milestone_breakdown: List[MilestoneInvoiceBreakdown] = Field(default_factory=list)
    cash_flow_trend: List[MonthlyCashFlow] = Field(default_factory=list)
    estimated_gross_margin: EstimatedGrossMarginMetric
    accounting_notes: List[str] = Field(default_factory=list)


# ==========================================
# 6. OPERATIONAL WORKFLOW ANALYTICS (PHASES 6-13)
# ==========================================

class ProcurementOperationsKPIs(BaseModel):
    total_suppliers: int = 0
    total_purchase_orders: int = 0
    total_po_value: Decimal = Decimal("0.00")
    pending_receipt_pos_count: int = 0
    goods_receipts_count: int = 0
    low_stock_alerts_count: int = 0


class DispatchOperationsKPIs(BaseModel):
    total_dispatches: int = 0
    dispatches_in_transit: int = 0
    dispatches_delivered: int = 0
    total_serialized_items_tracked: int = 0


class InstallationOperationsKPIs(BaseModel):
    total_schedules: int = 0
    active_installations: int = 0
    completed_installations: int = 0
    worklogs_recorded: int = 0
    tests_completed: int = 0


class ServiceWarrantyOperationsKPIs(BaseModel):
    active_warranties_count: int = 0
    open_service_tickets_count: int = 0
    critical_tickets_count: int = 0
    resolved_tickets_count: int = 0
    technician_visits_completed: int = 0
    components_replaced_count: int = 0


class SubsidyOperationsKPIs(BaseModel):
    total_applications: int = 0
    submitted_applications: int = 0
    approved_applications: int = 0
    disbursed_applications: int = 0
    total_subsidy_disbursed: Decimal = Decimal("0.00")


class ProjectStageExecution(BaseModel):
    stage: str
    count: int


class OperationalAnalyticsResponse(BaseModel):
    procurement: ProcurementOperationsKPIs
    dispatch: DispatchOperationsKPIs
    installation: InstallationOperationsKPIs
    service_warranty: ServiceWarrantyOperationsKPIs
    subsidy: SubsidyOperationsKPIs
    pipeline_stages: List[ProjectStageExecution] = Field(default_factory=list)

