from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 34. inventory
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    warehouse_location = Column(String(100), default="MAIN_WAREHOUSE", nullable=False)
    quantity_on_hand = Column(Numeric(12, 2), default=0.00, nullable=False)
    reserved_quantity = Column(Numeric(12, 2), default=0.00, nullable=False)
    quantity_available = Column(Numeric(12, 2), default=0.00, nullable=False)
    average_unit_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    reorder_level = Column(Numeric(10, 2), default=5.00, nullable=False)
    last_restocked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity_on_hand >= 0", name="chk_inventory_qoh_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="chk_inventory_reserved_non_negative"),
        CheckConstraint("quantity_available >= 0", name="chk_inventory_available_non_negative"),
        CheckConstraint("quantity_on_hand >= reserved_quantity", name="chk_inventory_qoh_ge_reserved"),
        CheckConstraint("reorder_level >= 0", name="chk_inventory_reorder_non_negative"),
    )


# 35. stock_movements
class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inventory_id = Column(BigInteger, ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    movement_type = Column(String(50), nullable=False, index=True) # PURCHASE_RECEIPT, DISPATCH, RETURN, ADJUSTMENT, SCRAP
    reference_type = Column(String(50), nullable=False) # GRN, DISPATCH, PROJECT, AUDIT
    reference_id = Column(BigInteger, nullable=True)
    quantity = Column(Numeric(10, 2), nullable=False) # Positive or negative
    unit_cost = Column(Numeric(12, 2), nullable=False)
    quantity_before = Column(Numeric(12, 2), nullable=False)
    quantity_after = Column(Numeric(12, 2), nullable=False)
    performed_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    inventory = relationship("Inventory")
    product = relationship("Product")
    performer = relationship("User", foreign_keys=[performed_by])

    __table_args__ = (
        CheckConstraint("quantity_before >= 0", name="chk_stock_mov_q_before_non_negative"),
        CheckConstraint("quantity_after >= 0", name="chk_stock_mov_q_after_non_negative"),
    )


# 36. stock_reservations
class StockReservation(Base):
    __tablename__ = "stock_reservations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inventory_id = Column(BigInteger, ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    reserved_quantity = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="RESERVED", nullable=False, index=True) # RESERVED, FULFILLED, RELEASED, CANCELLED
    reserved_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    expiry_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    inventory = relationship("Inventory")
    product = relationship("Product")
    project = relationship("Project")
    reserver = relationship("User", foreign_keys=[reserved_by])

    __table_args__ = (
        CheckConstraint("reserved_quantity > 0", name="chk_stock_res_qty_positive"),
    )


# 37. serial_numbers
class SerialNumber(Base):
    __tablename__ = "serial_numbers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    inventory_id = Column(BigInteger, ForeignKey("inventory.id", ondelete="SET NULL"), nullable=True, index=True)
    purchase_order_id = Column(BigInteger, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(BigInteger, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="IN_STOCK", nullable=False, index=True) # IN_STOCK, RESERVED, DISPATCHED, INSTALLED, COMMISSIONED, IN_REPAIR, REPLACED, SCRAPPED
    warranty_months = Column(BigInteger, default=60, nullable=False)
    received_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product")
    inventory = relationship("Inventory")
    project = relationship("Project")

    __table_args__ = (
        CheckConstraint("warranty_months >= 0", name="chk_serial_warranty_months"),
    )


# 38. serial_number_history
class SerialNumberHistory(Base):
    __tablename__ = "serial_number_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    serial_number_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    action_taken = Column(String(100), nullable=False)
    recorded_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    serial = relationship("SerialNumber")
    recorder = relationship("User", foreign_keys=[recorded_by])


# 39. dispatches
class Dispatch(Base):
    __tablename__ = "dispatches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dispatch_number = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    dispatched_date = Column(Date, nullable=False)
    dispatch_status = Column(String(50), default="PREPARED", nullable=False, index=True) # PREPARED, DISPATCHED, IN_TRANSIT, DELIVERED, RETURNED
    vehicle_number = Column(String(50), nullable=True)
    driver_name = Column(String(150), nullable=True)
    driver_phone = Column(String(30), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    dispatched_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    order = relationship("Order")
    dispatcher = relationship("User", foreign_keys=[dispatched_by])
    items = relationship("DispatchItem", back_populates="dispatch", cascade="all, delete-orphan")
    delivery_confirmation = relationship("DeliveryConfirmation", back_populates="dispatch", uselist=False)


# 40. dispatch_items
class DispatchItem(Base):
    __tablename__ = "dispatch_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dispatch_id = Column(BigInteger, ForeignKey("dispatches.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    dispatched_quantity = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dispatch = relationship("Dispatch", back_populates="items")
    product = relationship("Product")
    serials = relationship("DispatchSerial", back_populates="dispatch_item", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("dispatched_quantity > 0", name="chk_dispatch_item_qty_positive"),
    )


# 41. dispatch_serials
class DispatchSerial(Base):
    __tablename__ = "dispatch_serials"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dispatch_item_id = Column(BigInteger, ForeignKey("dispatch_items.id", ondelete="CASCADE"), nullable=False, index=True)
    serial_number_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="RESTRICT"), nullable=False, index=True)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scanned_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dispatch_item = relationship("DispatchItem", back_populates="serials")
    serial = relationship("SerialNumber")
    scanner = relationship("User", foreign_keys=[scanned_by])

    __table_args__ = (
        UniqueConstraint("dispatch_item_id", "serial_number_id", name="uq_dispatch_item_serial"),
    )


# 42. delivery_confirmations
class DeliveryConfirmation(Base):
    __tablename__ = "delivery_confirmations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dispatch_id = Column(BigInteger, ForeignKey("dispatches.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    confirmed_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    confirmation_type = Column(String(50), default="CUSTOMER_SIGN", nullable=False) # CUSTOMER_SIGN, OTP, PHOTO, SUPERVISOR_VERIFY
    recipient_name = Column(String(150), nullable=False)
    recipient_phone = Column(String(30), nullable=False)
    confirmation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    signature_attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    delivery_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    dispatch = relationship("Dispatch", back_populates="delivery_confirmation")
    project = relationship("Project")
    confirmer = relationship("User", foreign_keys=[confirmed_by])
    signature_attachment = relationship("FileAttachment", foreign_keys=[signature_attachment_id])
