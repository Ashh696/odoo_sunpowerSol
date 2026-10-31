from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


# 11. customers
class Customer(Base):
    __tablename__ = "customers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True, index=True)
    customer_type = Column(String(50), default="RESIDENTIAL", nullable=False) # RESIDENTIAL, COMMERCIAL, INDUSTRIAL
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(30), nullable=False, index=True)
    alternate_phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    pincode = Column(String(20), nullable=False)
    electricity_consumer_number = Column(String(100), nullable=True)
    sanctioned_load_kw = Column(Numeric(6, 2), nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    enquiries = relationship("Enquiry", back_populates="customer")

    __table_args__ = (
        CheckConstraint("sanctioned_load_kw IS NULL OR sanctioned_load_kw >= 0", name="chk_customer_sanctioned_load"),
    )


# 12. enquiries
class Enquiry(Base):
    __tablename__ = "enquiries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    enquiry_number = Column(String(50), unique=True, nullable=False, index=True)
    source = Column(String(50), default="DIRECT", nullable=False) # WEBSITE, REFERRAL, DIRECT, CAMPAIGN
    system_type = Column(String(50), default="ON_GRID", nullable=False) # ON_GRID, OFF_GRID, HYBRID
    proposed_capacity_kw = Column(Numeric(5, 2), nullable=False) # e.g. 1.0 to 5.0 kW
    monthly_electricity_bill = Column(Numeric(12, 2), nullable=True)
    roof_type = Column(String(100), nullable=True) # RCC_FLAT, METAL_SHED, TILED_ROOF
    status = Column(String(50), default="NEW", nullable=False, index=True) # NEW, CONTACTED, SURVEY_REQUESTED, QUOTED, WON, LOST, CANCELLED
    assigned_sales_id = Column(BigInteger, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="enquiries")
    assigned_sales = relationship("Employee", foreign_keys=[assigned_sales_id])
    followups = relationship("Followup", back_populates="enquiry", cascade="all, delete-orphan")
    surveys = relationship("Survey", back_populates="enquiry")
    quotations = relationship("Quotation", back_populates="enquiry")

    __table_args__ = (
        CheckConstraint("proposed_capacity_kw > 0", name="chk_enquiry_capacity_positive"),
        CheckConstraint("monthly_electricity_bill IS NULL OR monthly_electricity_bill >= 0", name="chk_enquiry_bill_non_negative"),
    )


# 13. followups
class Followup(Base):
    __tablename__ = "followups"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    enquiry_id = Column(BigInteger, ForeignKey("enquiries.id", ondelete="CASCADE"), nullable=False, index=True)
    conducted_by = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    followup_type = Column(String(50), default="CALL", nullable=False) # CALL, EMAIL, VISIT, WHATSAPP
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="SCHEDULED", nullable=False) # SCHEDULED, COMPLETED, CANCELLED
    discussion_summary = Column(Text, nullable=True)
    next_followup_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    enquiry = relationship("Enquiry", back_populates="followups")
    conductor = relationship("Employee", foreign_keys=[conducted_by])


# 14. surveys
class Survey(Base):
    __tablename__ = "surveys"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    enquiry_id = Column(BigInteger, ForeignKey("enquiries.id", ondelete="RESTRICT"), nullable=False, index=True)
    surveyor_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    survey_number = Column(String(50), unique=True, nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    conducted_at = Column(DateTime(timezone=True), nullable=True)
    roof_area_sqft = Column(Numeric(10, 2), nullable=True)
    shadow_free_area_sqft = Column(Numeric(10, 2), nullable=True)
    roof_orientation = Column(String(50), nullable=True) # SOUTH, SOUTH_WEST, SOUTH_EAST, NORTH, FLAT
    roof_tilt_degrees = Column(Numeric(4, 1), nullable=True)
    roof_structure_type = Column(String(100), nullable=True) # ELEVATED, FLUSH, TIN_SHED
    existing_phase = Column(String(50), default="SINGLE_PHASE", nullable=False) # SINGLE_PHASE, THREE_PHASE
    sanctioned_load_kw = Column(Numeric(6, 2), nullable=True)
    gps_latitude = Column(Numeric(10, 7), nullable=True)
    gps_longitude = Column(Numeric(10, 7), nullable=True)
    technical_feasibility = Column(String(50), default="FEASIBLE", nullable=False) # FEASIBLE, NOT_FEASIBLE, CONDITIONAL
    remarks = Column(Text, nullable=True)
    status = Column(String(50), default="DRAFT", nullable=False, index=True) # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, CORRECTION_REQUESTED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    enquiry = relationship("Enquiry", back_populates="surveys")
    surveyor = relationship("Employee", foreign_keys=[surveyor_id])
    approvals = relationship("SurveyApproval", back_populates="survey", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("roof_area_sqft IS NULL OR roof_area_sqft >= 0", name="chk_survey_roof_area"),
        CheckConstraint("shadow_free_area_sqft IS NULL OR shadow_free_area_sqft >= 0", name="chk_survey_shadow_area"),
    )


# 15. survey_approvals
class SurveyApproval(Base):
    __tablename__ = "survey_approvals"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    survey_id = Column(BigInteger, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action = Column(String(50), nullable=False) # APPROVED, REJECTED, CORRECTION_REQUESTED
    comments = Column(Text, nullable=False)
    revision_number = Column(BigInteger, default=1, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    survey = relationship("Survey", back_populates="approvals")
    reviewer = relationship("User", foreign_keys=[reviewer_id])


# 16. quotations
class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    enquiry_id = Column(BigInteger, ForeignKey("enquiries.id", ondelete="RESTRICT"), nullable=False, index=True)
    survey_id = Column(BigInteger, ForeignKey("surveys.id", ondelete="SET NULL"), nullable=True, index=True)
    quotation_number = Column(String(50), unique=True, nullable=False, index=True)
    version = Column(BigInteger, default=1, nullable=False)
    system_type = Column(String(50), nullable=False) # ON_GRID, OFF_GRID, HYBRID
    capacity_kw = Column(Numeric(5, 2), nullable=False) # 1.0 to 5.0
    total_product_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    installation_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    gross_amount = Column(Numeric(12, 2), nullable=False)
    subsidy_estimate = Column(Numeric(12, 2), default=0.00, nullable=False)
    net_payable_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True) # DRAFT, SENT, ACCEPTED, REVISED, REJECTED, EXPIRED
    valid_until = Column(Date, nullable=False)
    quotation_date = Column(Date, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    terms_and_conditions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    enquiry = relationship("Enquiry", back_populates="quotations")
    survey = relationship("Survey")
    creator = relationship("User", foreign_keys=[created_by])
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")
    revisions = relationship("QuotationRevision", back_populates="quotation", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("capacity_kw > 0", name="chk_quotation_capacity"),
        CheckConstraint("gross_amount >= 0", name="chk_quotation_gross_amount"),
        CheckConstraint("net_payable_amount >= 0", name="chk_quotation_net_amount"),
        CheckConstraint("valid_until >= quotation_date", name="chk_quotation_dates"),
    )


# 17. products
class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True) # SOLAR_PANEL, INVERTER, BATTERY, STRUCTURE, CABLES, DCDB, ACDB, LIGHTNING_ARRESTER, EARTHING, MISC
    brand = Column(String(100), nullable=True)
    model_number = Column(String(150), nullable=True)
    wattage_or_capacity = Column(String(100), nullable=True) # e.g. "550W", "5kW", "150Ah"
    unit_of_measure = Column(String(50), default="NOS", nullable=False) # NOS, METERS, SETS, KG
    is_serialized = Column(Boolean, default=False, nullable=False)
    base_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=12.00, nullable=False)
    min_stock_alert = Column(Numeric(10, 2), default=5.00, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("base_price >= 0", name="chk_product_base_price"),
        CheckConstraint("tax_rate_percent >= 0", name="chk_product_tax_rate"),
        CheckConstraint("min_stock_alert >= 0", name="chk_product_min_stock"),
    )


# 18. quotation_items
class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quotation_id = Column(BigInteger, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    item_description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False) # Snapshotted price
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=12.00, nullable=False) # Snapshotted tax rate
    total_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quotation = relationship("Quotation", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_quotation_item_qty"),
        CheckConstraint("unit_price >= 0", name="chk_quotation_item_price"),
        CheckConstraint("total_amount >= 0", name="chk_quotation_item_total"),
    )


# 19. quotation_revisions
class QuotationRevision(Base):
    __tablename__ = "quotation_revisions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quotation_id = Column(BigInteger, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_number = Column(BigInteger, nullable=False)
    snapshot_data = Column(JSONB, nullable=False) # Full JSON snapshot of previous quotation state
    reason_for_revision = Column(Text, nullable=False)
    revised_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quotation = relationship("Quotation", back_populates="revisions")
    reviser = relationship("User", foreign_keys=[revised_by])

    __table_args__ = (
        UniqueConstraint("quotation_id", "revision_number", name="uq_quotation_revision"),
    )
