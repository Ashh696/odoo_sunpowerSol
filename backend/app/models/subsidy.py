from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 66. subsidy_applications
class SubsidyApplication(Base):
    __tablename__ = "subsidy_applications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    customer_id = Column(BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    portal_registration_number = Column(String(100), unique=True, nullable=True, index=True)
    discom_name = Column(String(150), nullable=False)
    sanctioned_capacity_kw = Column(Numeric(5, 2), nullable=False)
    eligible_subsidy_amount = Column(Numeric(12, 2), nullable=False)
    application_date = Column(Date, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False, index=True) # DRAFT, SUBMITTED_TO_DISCOM, INSPECTION_SCHEDULED, INSPECTION_COMPLETED, APPROVED, SUBSIDY_DISBURSED, REJECTED
    rejection_reason = Column(Text, nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    customer = relationship("Customer")
    creator = relationship("User", foreign_keys=[created_by])
    documents = relationship("SubsidyDocument", back_populates="application", cascade="all, delete-orphan")
    history = relationship("SubsidyStatusHistory", back_populates="application", cascade="all, delete-orphan")
    payments = relationship("SubsidyPayment", back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("sanctioned_capacity_kw > 0", name="chk_subsidy_capacity_positive"),
        CheckConstraint("eligible_subsidy_amount >= 0", name="chk_subsidy_amount_non_negative"),
    )


# 67. subsidy_documents
class SubsidyDocument(Base):
    __tablename__ = "subsidy_documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subsidy_application_id = Column(BigInteger, ForeignKey("subsidy_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(100), nullable=False) # ELECTRICITY_BILL, AADHAAR_CARD, BANK_PASSBOOK, JOINT_INSPECTION_REPORT, NET_METER_INSTALL_REPORT
    attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="RESTRICT"), nullable=False)
    verification_status = Column(String(50), default="PENDING", nullable=False) # PENDING, VERIFIED, REJECTED
    remarks = Column(Text, nullable=True)
    verified_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    application = relationship("SubsidyApplication", back_populates="documents")
    attachment = relationship("FileAttachment")
    verifier = relationship("User", foreign_keys=[verified_by])


# 68. subsidy_status_history
class SubsidyStatusHistory(Base):
    __tablename__ = "subsidy_status_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subsidy_application_id = Column(BigInteger, ForeignKey("subsidy_applications.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    action_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    comments = Column(Text, nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    application = relationship("SubsidyApplication", back_populates="history")
    updater = relationship("User", foreign_keys=[updated_by])


# 69. subsidy_payments
class SubsidyPayment(Base):
    __tablename__ = "subsidy_payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subsidy_application_id = Column(BigInteger, ForeignKey("subsidy_applications.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_reference = Column(String(100), unique=True, nullable=False, index=True)
    disbursement_date = Column(Date, nullable=False)
    disbursed_amount = Column(Numeric(12, 2), nullable=False)
    bank_reference_number = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    application = relationship("SubsidyApplication", back_populates="payments")
    project = relationship("Project")

    __table_args__ = (
        CheckConstraint("disbursed_amount > 0", name="chk_subsidy_payment_amount_positive"),
    )
