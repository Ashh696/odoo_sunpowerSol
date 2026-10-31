from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 52. payments
class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50), default="UPI", nullable=False) # NEFT, RTGS, CHEQUE, UPI, CASH
    transaction_reference = Column(String(100), unique=True, nullable=True, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    unallocated_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False, index=True) # COMPLETED, PENDING, FAILED, REFUNDED
    notes = Column(Text, nullable=True)
    received_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer = relationship("Customer")
    order = relationship("Order")
    project = relationship("Project")
    receiver = relationship("User", foreign_keys=[received_by])
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payment_amount_positive"),
        CheckConstraint("unallocated_amount >= 0", name="chk_payment_unalloc_non_negative"),
        CheckConstraint("unallocated_amount <= amount", name="chk_payment_unalloc_le_amount"),
    )


# 53. invoices
class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_type = Column(String(50), default="MILESTONE_INSTALLATION", nullable=False) # ADVANCE, MILESTONE_DISPATCH, MILESTONE_INSTALLATION, FINAL, SUBSIDY
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    balance_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, PARTIALLY_PAID, PAID, OVERDUE
    pdf_attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order = relationship("Order")
    project = relationship("Project")
    customer = relationship("Customer")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("PaymentAllocation", back_populates="invoice")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_invoice_total_non_negative"),
        CheckConstraint("paid_amount >= 0", name="chk_invoice_paid_non_negative"),
        CheckConstraint("balance_amount >= 0", name="chk_invoice_balance_non_negative"),
        CheckConstraint("due_date >= invoice_date", name="chk_invoice_dates"),
    )


# 54. invoice_items
class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(BigInteger, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=12.00, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_invoice_item_qty_positive"),
        CheckConstraint("unit_price >= 0", name="chk_invoice_item_price_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_invoice_item_total_non_negative"),
    )


# 55. payment_allocations
class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_id = Column(BigInteger, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_id = Column(BigInteger, ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    allocated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payment = relationship("Payment", back_populates="allocations")
    invoice = relationship("Invoice", back_populates="allocations")

    __table_args__ = (
        CheckConstraint("allocated_amount > 0", name="chk_payment_alloc_positive"),
        Index("idx_pay_alloc_pair", "payment_id", "invoice_id"),
    )


# 56. expenses
class Expense(Base):
    __tablename__ = "expenses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    expense_number = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(BigInteger, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    expense_category = Column(String(50), nullable=False) # TRAVEL, SITE_MATERIAL, PERMIT_FEE, LABOUR, FOOD, LODGING, MISC
    expense_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    payment_status = Column(String(50), default="PENDING", nullable=False) # PENDING, APPROVED, REJECTED, PAID
    approved_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    receipt_attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    department = relationship("Department")
    employee = relationship("Employee")
    approver = relationship("User", foreign_keys=[approved_by])
    receipt = relationship("FileAttachment", foreign_keys=[receipt_attachment_id])

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_expense_amount_positive"),
        CheckConstraint("tax_amount >= 0", name="chk_expense_tax_non_negative"),
    )


# 57. technician_payments
class TechnicianPayment(Base):
    __tablename__ = "technician_payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_reference = Column(String(50), unique=True, nullable=False, index=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_type = Column(String(50), default="PER_KW_COMMISSION", nullable=False) # PER_KW_COMMISSION, DAILY_WAGE, OVERTIME, BONUS
    amount = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(Date, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, APPROVED, PROCESSED
    approved_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employee = relationship("Employee")
    installation = relationship("Installation")
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_tech_payment_amount_positive"),
    )


# 58. project_costs
class ProjectCost(Base):
    __tablename__ = "project_costs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_category = Column(String(50), nullable=False, index=True) # EQUIPMENT, LABOUR, TRANSPORT, PERMITS, WARRANTY_CONTINGENCY, OVERHEADS
    cost_amount = Column(Numeric(12, 2), nullable=False)
    source_reference_type = Column(String(50), nullable=False) # PO, EXPENSE, TECHNICIAN_PAYMENT, MANUAL
    source_reference_id = Column(BigInteger, nullable=True)
    recorded_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project")
    recorder = relationship("User", foreign_keys=[recorded_by])

    __table_args__ = (
        CheckConstraint("cost_amount >= 0", name="chk_project_cost_non_negative"),
    )
