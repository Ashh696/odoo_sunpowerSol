from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


# 70. tasks
class Task(Base):
    __tablename__ = "tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_code = Column(String(50), unique=True, nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False, index=True) # SURVEY, PROCUREMENT, DISPATCH, INSTALLATION, COMMISSIONING, SUBSIDY, SERVICE
    priority = Column(String(50), default="MEDIUM", nullable=False) # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(50), default="PENDING", nullable=False, index=True) # PENDING, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED
    due_date = Column(Date, nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    history = relationship("TaskHistory", back_populates="task", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="task", cascade="all, delete-orphan")


# 71. task_assignments
class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(50), default="ASSIGNED", nullable=False) # ASSIGNED, ACCEPTED, REJECTED, COMPLETED
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("Task", back_populates="assignments")
    employee = relationship("Employee")
    assigner = relationship("User", foreign_keys=[assigned_by])

    __table_args__ = (
        UniqueConstraint("task_id", "employee_id", name="uq_task_employee_assignment"),
    )


# 72. task_history
class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    comment = Column(Text, nullable=True)
    changed_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("Task", back_populates="history")
    changer = relationship("User", foreign_keys=[changed_by])


# 73. escalations
class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    escalated_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    escalated_to = Column(BigInteger, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    escalation_level = Column(String(50), default="LEVEL_1", nullable=False) # LEVEL_1, LEVEL_2, LEVEL_3
    reason = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    task = relationship("Task", back_populates="escalations")
    project = relationship("Project")
    escalator = relationship("User", foreign_keys=[escalated_by])
    assignee = relationship("Employee", foreign_keys=[escalated_to])


# 74. notifications
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="ALERT", nullable=False) # TASK, ALERT, APPROVAL, REMINDER, SYSTEM
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    link_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])


# 75. audit_logs
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True) # CREATE, UPDATE, DELETE, LOGIN, EXPORT, APPROVE, REJECT
    entity_name = Column(String(100), nullable=False, index=True)
    entity_id = Column(BigInteger, nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_audit_logs_action_entity", "action", "entity_name"),
    )
