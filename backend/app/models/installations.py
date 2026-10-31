from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 43. installation_schedules
class InstallationSchedule(Base):
    __tablename__ = "installation_schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    scheduled_start_date = Column(Date, nullable=False)
    scheduled_end_date = Column(Date, nullable=False)
    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    status = Column(String(50), default="SCHEDULED", nullable=False, index=True) # SCHEDULED, IN_PROGRESS, COMPLETED, POSTPONED, CANCELLED
    notes = Column(Text, nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    technicians = relationship("InstallationScheduleTechnician", back_populates="schedule", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("scheduled_end_date >= scheduled_start_date", name="chk_schedule_planned_dates"),
        CheckConstraint("actual_end_date IS NULL OR actual_start_date IS NULL OR actual_end_date >= actual_start_date", name="chk_schedule_actual_dates"),
    )


# 44. installation_schedule_technicians
class InstallationScheduleTechnician(Base):
    __tablename__ = "installation_schedule_technicians"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(BigInteger, ForeignKey("installation_schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    role_in_team = Column(String(50), default="TECHNICIAN", nullable=False) # LEAD, TECHNICIAN, ASSISTANT, ELECTRICIAN
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    schedule = relationship("InstallationSchedule", back_populates="technicians")
    employee = relationship("Employee")

    __table_args__ = (
        UniqueConstraint("schedule_id", "employee_id", name="uq_schedule_technician"),
    )


# 45. installations
class Installation(Base):
    __tablename__ = "installations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    schedule_id = Column(BigInteger, ForeignKey("installation_schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    lead_technician_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    system_capacity_kw = Column(Numeric(5, 2), nullable=False)
    inverter_make_model = Column(String(150), nullable=True)
    total_panels_installed = Column(BigInteger, nullable=False)
    structure_type = Column(String(100), nullable=True)
    installation_date = Column(Date, nullable=False)
    commissioning_date = Column(Date, nullable=True)
    status = Column(String(50), default="IN_PROGRESS", nullable=False, index=True) # IN_PROGRESS, PENDING_INSPECTION, COMPLETED, FAILED_INSPECTION
    technician_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    schedule = relationship("InstallationSchedule")
    lead_technician = relationship("Employee", foreign_keys=[lead_technician_id])
    checklists = relationship("InstallationChecklist", back_populates="installation", cascade="all, delete-orphan")
    photos = relationship("InstallationPhoto", back_populates="installation", cascade="all, delete-orphan")
    worklogs = relationship("TechnicianWorklog", back_populates="installation", cascade="all, delete-orphan")
    tests = relationship("InstallationTest", back_populates="installation", cascade="all, delete-orphan")
    materials = relationship("MaterialConsumption", back_populates="installation", cascade="all, delete-orphan")
    customer_acceptance = relationship("CustomerAcceptance", back_populates="installation", uselist=False)

    __table_args__ = (
        CheckConstraint("system_capacity_kw > 0", name="chk_installation_capacity"),
        CheckConstraint("total_panels_installed >= 0", name="chk_installation_panels_installed"),
        CheckConstraint("commissioning_date IS NULL OR commissioning_date >= installation_date", name="chk_installation_dates"),
    )


# 46. installation_checklists
class InstallationChecklist(Base):
    __tablename__ = "installation_checklists"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="CASCADE"), nullable=False, index=True)
    checklist_item = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False) # CIVIL, MECHANICAL, ELECTRICAL, SAFETY, COMMISSIONING
    is_checked = Column(Boolean, default=False, nullable=False)
    remarks = Column(Text, nullable=True)
    verified_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    installation = relationship("Installation", back_populates="checklists")
    verifier = relationship("User", foreign_keys=[verified_by])


# 47. installation_photos
class InstallationPhoto(Base):
    __tablename__ = "installation_photos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(50), nullable=False, index=True) # PRE_INSTALL, STRUCTURE, PANELS, WIRING, INVERTER, EARTHING, NET_METER, FINAL
    attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="RESTRICT"), nullable=False)
    caption = Column(String(255), nullable=True)
    gps_latitude = Column(Numeric(10, 7), nullable=True)
    gps_longitude = Column(Numeric(10, 7), nullable=True)
    captured_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    installation = relationship("Installation", back_populates="photos")
    attachment = relationship("FileAttachment")


# 48. technician_worklogs
class TechnicianWorklog(Base):
    __tablename__ = "technician_worklogs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    work_date = Column(Date, nullable=False)
    hours_worked = Column(Numeric(4, 2), nullable=False)
    work_description = Column(Text, nullable=False)
    approved_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    installation = relationship("Installation", back_populates="worklogs")
    employee = relationship("Employee")
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        CheckConstraint("hours_worked > 0 AND hours_worked <= 24", name="chk_worklog_hours_valid"),
    )


# 49. installation_tests
class InstallationTest(Base):
    __tablename__ = "installation_tests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String(100), nullable=False) # VOC_TEST, ISC_TEST, INSULATION_RESISTANCE, EARTHING_RESISTANCE, GRID_SYNC, INVERTER_EFFICIENCY
    standard_value = Column(String(100), nullable=True)
    measured_value = Column(String(100), nullable=False)
    unit_of_measure = Column(String(30), nullable=False) # Volts, Amps, Ohms, %
    is_passed = Column(Boolean, default=True, nullable=False)
    tested_by = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    test_date = Column(Date, nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    installation = relationship("Installation", back_populates="tests")
    tester = relationship("Employee", foreign_keys=[tested_by])


# 50. material_consumption
class MaterialConsumption(Base):
    __tablename__ = "material_consumption"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    serial_number_id = Column(BigInteger, ForeignKey("serial_numbers.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity_consumed = Column(Numeric(10, 2), nullable=False)
    unit_of_measure = Column(String(50), nullable=False)
    is_extra_material = Column(Boolean, default=False, nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    installation = relationship("Installation", back_populates="materials")
    product = relationship("Product")
    serial = relationship("SerialNumber")

    __table_args__ = (
        CheckConstraint("quantity_consumed > 0", name="chk_mat_consumption_qty_positive"),
    )


# 51. customer_acceptances
class CustomerAcceptance(Base):
    __tablename__ = "customer_acceptances"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    installation_id = Column(BigInteger, ForeignKey("installations.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    acceptance_date = Column(Date, nullable=False)
    rating_overall = Column(BigInteger, nullable=True) # 1 to 5
    satisfaction_notes = Column(Text, nullable=True)
    customer_signature_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    is_accepted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    installation = relationship("Installation", back_populates="customer_acceptance")
    project = relationship("Project")
    customer = relationship("Customer")
    signature = relationship("FileAttachment", foreign_keys=[customer_signature_id])

    __table_args__ = (
        CheckConstraint("rating_overall IS NULL OR (rating_overall >= 1 AND rating_overall <= 5)", name="chk_customer_rating_range"),
    )
