from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 20. orders
class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    quotation_id = Column(BigInteger, ForeignKey("quotations.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_date = Column(Date, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    advance_paid = Column(Numeric(12, 2), default=0.00, nullable=False)
    balance_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="CONFIRMED", nullable=False, index=True) # DRAFT, CONFIRMED, PROCESSING, COMPLETED, CANCELLED
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    quotation = relationship("Quotation")
    customer = relationship("Customer")
    creator = relationship("User", foreign_keys=[created_by])
    project = relationship("Project", back_populates="order", uselist=False)

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_order_total_amount"),
        CheckConstraint("advance_paid >= 0", name="chk_order_advance_paid"),
        CheckConstraint("balance_amount >= 0", name="chk_order_balance_amount"),
    )


# 21. projects
class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_manager_id = Column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    system_capacity_kw = Column(Numeric(5, 2), nullable=False) # 1.0 to 5.0 kW
    system_type = Column(String(50), nullable=False) # ON_GRID, OFF_GRID, HYBRID
    site_address = Column(Text, nullable=False)
    planned_start_date = Column(Date, nullable=False)
    planned_completion_date = Column(Date, nullable=False)
    actual_completion_date = Column(Date, nullable=True)
    status = Column(String(50), default="INITIATED", nullable=False, index=True) # INITIATED, PROCUREMENT, DISPATCHED, INSTALLATION, COMMISSIONED, HANDED_OVER, ON_HOLD, CANCELLED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order = relationship("Order", back_populates="project")
    customer = relationship("Customer")
    project_manager = relationship("Employee", foreign_keys=[project_manager_id])
    bom_items = relationship("ProjectBomItem", back_populates="project", cascade="all, delete-orphan")
    notes = relationship("ProjectNote", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("system_capacity_kw > 0", name="chk_project_capacity"),
        CheckConstraint("planned_completion_date >= planned_start_date", name="chk_project_planned_dates"),
        CheckConstraint("actual_completion_date IS NULL OR actual_completion_date >= planned_start_date", name="chk_project_actual_dates"),
    )


# 22. bom_templates
class BomTemplate(Base):
    __tablename__ = "bom_templates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    template_name = Column(String(150), unique=True, nullable=False)
    system_type = Column(String(50), nullable=False, index=True) # ON_GRID, OFF_GRID, HYBRID
    capacity_kw = Column(Numeric(5, 2), nullable=False, index=True) # 1.0 to 5.0
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    items = relationship("BomItem", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("capacity_kw > 0", name="chk_bom_template_capacity"),
    )


# 23. bom_items
class BomItem(Base):
    __tablename__ = "bom_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    bom_template_id = Column(BigInteger, ForeignKey("bom_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_category = Column(String(100), nullable=False)
    default_quantity = Column(Numeric(10, 2), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    template = relationship("BomTemplate", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("default_quantity > 0", name="chk_bom_item_default_qty"),
        UniqueConstraint("bom_template_id", "product_id", name="uq_bom_template_product"),
    )


# 24. project_bom_items
class ProjectBomItem(Base):
    __tablename__ = "project_bom_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_category = Column(String(100), nullable=False)
    planned_quantity = Column(Numeric(10, 2), nullable=False)
    allocated_quantity = Column(Numeric(10, 2), default=0.00, nullable=False)
    dispatched_quantity = Column(Numeric(10, 2), default=0.00, nullable=False)
    installed_quantity = Column(Numeric(10, 2), default=0.00, nullable=False)
    unit_cost_snapshot = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project", back_populates="bom_items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("planned_quantity >= 0", name="chk_project_bom_planned_qty"),
        CheckConstraint("allocated_quantity >= 0", name="chk_project_bom_allocated_qty"),
        CheckConstraint("dispatched_quantity >= 0", name="chk_project_bom_dispatched_qty"),
        CheckConstraint("installed_quantity >= 0", name="chk_project_bom_installed_qty"),
        CheckConstraint("unit_cost_snapshot >= 0", name="chk_project_bom_unit_cost"),
        UniqueConstraint("project_id", "product_id", name="uq_project_bom_product"),
    )


# 25. project_notes
class ProjectNote(Base):
    __tablename__ = "project_notes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    note_type = Column(String(50), default="GENERAL", nullable=False) # GENERAL, TECHNICAL, SITE, CLIENT, ESCALATION
    note_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="notes")
    author = relationship("User", foreign_keys=[author_id])


# 26. suppliers
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    supplier_code = Column(String(50), unique=True, nullable=False, index=True)
    company_name = Column(String(255), unique=True, nullable=False, index=True)
    contact_person = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(30), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    gst_number = Column(String(30), unique=True, nullable=True)
    pan_number = Column(String(20), nullable=True)
    bank_account_details = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


# 27. purchase_orders
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    po_date = Column(Date, nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True) # DRAFT, ISSUED, PARTIALLY_RECEIVED, RECEIVED, CANCELLED
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    supplier = relationship("Supplier")
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_po_total_amount"),
        CheckConstraint("tax_amount >= 0", name="chk_po_tax_amount"),
        CheckConstraint("expected_delivery_date IS NULL OR expected_delivery_date >= po_date", name="chk_po_dates"),
    )


# 28. purchase_order_items
class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    ordered_quantity = Column(Numeric(10, 2), nullable=False)
    received_quantity = Column(Numeric(10, 2), default=0.00, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=12.00, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("ordered_quantity > 0", name="chk_po_item_ordered_qty"),
        CheckConstraint("received_quantity >= 0", name="chk_po_item_received_qty"),
        CheckConstraint("unit_price >= 0", name="chk_po_item_unit_price"),
        CheckConstraint("total_amount >= 0", name="chk_po_item_total_amount"),
    )


# 29. goods_receipts
class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    grn_number = Column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    received_date = Column(Date, nullable=False)
    received_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    challan_number = Column(String(100), nullable=True)
    challan_date = Column(Date, nullable=True)
    status = Column(String(50), default="ACCEPTED", nullable=False) # RECEIVED, INSPECTED, ACCEPTED, REJECTED
    inspection_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    receiver = relationship("User", foreign_keys=[received_by])
    items = relationship("GoodsReceiptItem", back_populates="goods_receipt", cascade="all, delete-orphan")


# 30. goods_receipt_items
class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    goods_receipt_id = Column(BigInteger, ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    po_item_id = Column(BigInteger, ForeignKey("purchase_order_items.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    received_quantity = Column(Numeric(10, 2), nullable=False)
    accepted_quantity = Column(Numeric(10, 2), nullable=False)
    rejected_quantity = Column(Numeric(10, 2), default=0.00, nullable=False)
    rejection_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    goods_receipt = relationship("GoodsReceipt", back_populates="items")
    po_item = relationship("PurchaseOrderItem")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("received_quantity >= 0", name="chk_grn_item_received_qty"),
        CheckConstraint("accepted_quantity >= 0", name="chk_grn_item_accepted_qty"),
        CheckConstraint("rejected_quantity >= 0", name="chk_grn_item_rejected_qty"),
        CheckConstraint("received_quantity = accepted_quantity + rejected_quantity", name="chk_grn_item_balance"),
    )


# 31. supplier_invoices
class SupplierInvoice(Base):
    __tablename__ = "supplier_invoices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    balance_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, PARTIALLY_PAID, PAID, OVERDUE
    attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    purchase_order = relationship("PurchaseOrder")
    supplier = relationship("Supplier")
    allocations = relationship("SupplierPaymentAllocation", back_populates="supplier_invoice")

    __table_args__ = (
        UniqueConstraint("supplier_id", "invoice_number", name="uq_supplier_invoice_number"),
        CheckConstraint("total_amount >= 0", name="chk_supplier_invoice_total"),
        CheckConstraint("paid_amount >= 0", name="chk_supplier_invoice_paid"),
        CheckConstraint("balance_amount >= 0", name="chk_supplier_invoice_balance"),
        CheckConstraint("due_date >= invoice_date", name="chk_supplier_invoice_dates"),
    )


# 32. supplier_payments
class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_reference = Column(String(100), unique=True, nullable=False, index=True)
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_date = Column(Date, nullable=False)
    payment_mode = Column(String(50), default="NEFT", nullable=False) # NEFT, RTGS, CHEQUE, UPI
    amount = Column(Numeric(12, 2), nullable=False)
    unallocated_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False) # COMPLETED, FAILED, VOID
    notes = Column(Text, nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supplier = relationship("Supplier")
    creator = relationship("User", foreign_keys=[created_by])
    allocations = relationship("SupplierPaymentAllocation", back_populates="supplier_payment", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_supplier_payment_amount_positive"),
        CheckConstraint("unallocated_amount >= 0", name="chk_supplier_payment_unallocated_non_negative"),
        CheckConstraint("unallocated_amount <= amount", name="chk_supplier_payment_unallocated_le_total"),
    )


# 33. supplier_payment_allocations
class SupplierPaymentAllocation(Base):
    __tablename__ = "supplier_payment_allocations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    supplier_payment_id = Column(BigInteger, ForeignKey("supplier_payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_invoice_id = Column(BigInteger, ForeignKey("supplier_invoices.id", ondelete="RESTRICT"), nullable=False, index=True)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    allocated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supplier_payment = relationship("SupplierPayment", back_populates="allocations")
    supplier_invoice = relationship("SupplierInvoice", back_populates="allocations")

    __table_args__ = (
        CheckConstraint("allocated_amount > 0", name="chk_supplier_alloc_amount_positive"),
        Index("idx_supp_alloc_pay_inv", "supplier_payment_id", "supplier_invoice_id"),
    )
