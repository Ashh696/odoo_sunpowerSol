from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 59. warranty_policies
class WarrantyPolicy(Base):
    __tablename__ = "warranty_policies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    policy_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=True, index=True)
    warranty_period_months = Column(BigInteger, nullable=False) # e.g. 60, 120, 300 months
    activation_trigger = Column(String(50), default="COMMISSIONING", nullable=False) # DELIVERY, INSTALLATION, COMMISSIONING
    terms_and_conditions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("warranty_period_months > 0", name="chk_warranty_period_positive"),
    )


# 60. warranty_records
class WarrantyRecord(Base):
    __tablename__ = "warranty_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    certificate_number = Column(String(100), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    serial_number_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warranty_policy_id = Column(BigInteger, ForeignKey("warranty_policies.id", ondelete="RESTRICT"), nullable=False, index=True)
    delivery_date = Column(Date, nullable=False) # Preserved delivery date
    activation_trigger = Column(String(50), nullable=False) # DELIVERY, INSTALLATION, COMMISSIONING
    activation_date = Column(Date, nullable=True) # Activation date
    warranty_start_date = Column(Date, nullable=False)
    warranty_end_date = Column(Date, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False, index=True) # PENDING_ACTIVATION, ACTIVE, EXPIRED, VOID, CLAIMED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    product = relationship("Product")
    serial = relationship("SerialNumber")
    customer = relationship("Customer")
    policy = relationship("WarrantyPolicy")
    events = relationship("WarrantyEvent", back_populates="warranty_record", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("warranty_end_date >= warranty_start_date", name="chk_warranty_dates"),
    )


# 61. warranty_events
class WarrantyEvent(Base):
    __tablename__ = "warranty_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    warranty_record_id = Column(BigInteger, ForeignKey("warranty_records.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # ACTIVATION, CLAIM_RAISED, INSPECTION, REPAIR, REPLACEMENT, VOIDED
    event_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(Text, nullable=False)
    recorded_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    warranty_record = relationship("WarrantyRecord", back_populates="events")
    recorder = relationship("User", foreign_keys=[recorded_by])


# 62. service_tickets
class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    serial_number_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    warranty_record_id = Column(BigInteger, ForeignKey("warranty_records.id", ondelete="SET NULL"), nullable=True, index=True)
    issue_category = Column(String(50), nullable=False) # INVERTER_FAULT, LOW_GENERATION, PHYSICAL_DAMAGE, GRID_FAILURE, WIRING_ISSUE, GENERAL
    priority = Column(String(50), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False, index=True) # OPEN, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, CANCELLED
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    customer = relationship("Customer")
    serial = relationship("SerialNumber")
    warranty_record = relationship("WarrantyRecord")
    creator = relationship("User", foreign_keys=[created_by])
    visits = relationship("ServiceVisit", back_populates="ticket", cascade="all, delete-orphan")
    replacements = relationship("Replacement", back_populates="ticket", cascade="all, delete-orphan")
    confirmation = relationship("ServiceTicketConfirmation", back_populates="ticket", uselist=False)


# 63. service_visits
class ServiceVisit(Base):
    __tablename__ = "service_visits"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(BigInteger, ForeignKey("service_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    technician_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    visit_number = Column(BigInteger, default=1, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    visit_status = Column(String(50), default="SCHEDULED", nullable=False) # SCHEDULED, IN_PROGRESS, COMPLETED, RESCHEDULED
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    findings = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)
    parts_replaced = Column(Boolean, default=False, nullable=False)
    customer_present_name = Column(String(150), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("ServiceTicket", back_populates="visits")
    technician = relationship("Employee")

    __table_args__ = (
        CheckConstraint("actual_end IS NULL OR actual_start IS NULL OR actual_end >= actual_start", name="chk_service_visit_times"),
    )


# 64. replacements
class Replacement(Base):
    __tablename__ = "replacements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(BigInteger, ForeignKey("service_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    original_serial_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="RESTRICT"), nullable=False, index=True)
    replacement_serial_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="RESTRICT"), nullable=False, index=True)
    replacement_reason = Column(Text, nullable=False)
    replacement_date = Column(Date, nullable=False)
    replaced_by = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("ServiceTicket", back_populates="replacements")
    original_serial = relationship("SerialNumber", foreign_keys=[original_serial_id])
    replacement_serial = relationship("SerialNumber", foreign_keys=[replacement_serial_id])
    replacer = relationship("Employee", foreign_keys=[replaced_by])

    __table_args__ = (
        CheckConstraint("original_serial_id != replacement_serial_id", name="chk_replacement_distinct_serials"),
    )


# 65. service_ticket_confirmations
class ServiceTicketConfirmation(Base):
    __tablename__ = "service_ticket_confirmations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticket_id = Column(BigInteger, ForeignKey("service_tickets.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    resolution_confirmed = Column(Boolean, default=True, nullable=False)
    customer_rating = Column(BigInteger, nullable=True) # 1 to 5
    customer_feedback = Column(Text, nullable=True)
    confirmed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    confirmation_channel = Column(String(50), default="PORTAL", nullable=False) # PORTAL, OTP, SIGNATURE
    signature_attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("ServiceTicket", back_populates="confirmation")
    customer = relationship("Customer")
    signature = relationship("FileAttachment", foreign_keys=[signature_attachment_id])

    __table_args__ = (
        CheckConstraint("customer_rating IS NULL OR (customer_rating >= 1 AND customer_rating <= 5)", name="chk_ticket_rating_range"),
    )
