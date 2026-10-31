from sqlalchemy import (
    Column, BigInteger, String, Boolean, DateTime, Date, Numeric, ForeignKey,
    Text, CheckConstraint, UniqueConstraint, Index, func
)
from sqlalchemy.orm import relationship
from app.database import Base


# 1. roles
class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    users = relationship("User", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


# 2. permissions
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    code = Column(String(100), unique=True, nullable=False, index=True)
    module = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


# 3. users
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(30), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    role = relationship("Role", back_populates="users")
    employee = relationship("Employee", back_populates="user", uselist=False)


# 4. role_permissions
class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("idx_role_permissions_role", "role_id"),
        Index("idx_role_permissions_perm", "permission_id"),
    )


# 5. departments
class Department(Base):
    __tablename__ = "departments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    manager_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    manager = relationship("User", foreign_keys=[manager_id])
    employees = relationship("Employee", back_populates="department")


# 6. employees
class Employee(Base):
    __tablename__ = "employees"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    department_id = Column(BigInteger, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    employee_code = Column(String(50), unique=True, nullable=False, index=True)
    designation = Column(String(100), nullable=False)
    employment_type = Column(String(50), default="FULL_TIME", nullable=False) # FULL_TIME, CONTRACTOR, INTERN
    joining_date = Column(Date, nullable=False)
    exit_date = Column(Date, nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    certifications = relationship("EmployeeCertification", back_populates="employee", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("exit_date IS NULL OR exit_date >= joining_date", name="chk_employee_exit_date"),
    )


# 7. skills
class Skill(Base):
    __tablename__ = "skills"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100), nullable=False, index=True) # ELECTRICAL, MOUNTING, SAFETY, COMMISSIONING
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# 8. employee_skills
class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(BigInteger, ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False)
    proficiency_level = Column(String(50), default="INTERMEDIATE", nullable=False) # BEGINNER, INTERMEDIATE, EXPERT
    years_of_experience = Column(Numeric(4, 1), default=0.0, nullable=False)
    verified_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    employee = relationship("Employee", back_populates="skills")
    skill = relationship("Skill")

    __table_args__ = (
        UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill"),
        CheckConstraint("years_of_experience >= 0", name="chk_skill_experience_non_negative"),
        Index("idx_employee_skills_emp", "employee_id"),
        Index("idx_employee_skills_skill", "skill_id"),
    )


# 9. file_attachments
class FileAttachment(Base):
    __tablename__ = "file_attachments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False, index=True) # SURVEY, INSTALLATION, INVOICE, SUBSIDY, CERTIFICATION
    entity_id = Column(BigInteger, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    storage_backend = Column(String(50), default="LOCAL", nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    uploaded_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    uploader = relationship("User", foreign_keys=[uploaded_by])

    __table_args__ = (
        CheckConstraint("file_size_bytes >= 0", name="chk_file_size_non_negative"),
        Index("idx_file_attachment_entity", "entity_type", "entity_id"),
    )


# 10. employee_certifications
class EmployeeCertification(Base):
    __tablename__ = "employee_certifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(BigInteger, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    certification_name = Column(String(255), nullable=False)
    issuing_authority = Column(String(255), nullable=False)
    certificate_number = Column(String(100), nullable=True)
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True)
    attachment_id = Column(BigInteger, ForeignKey("file_attachments.id", ondelete="SET NULL"), nullable=True)
    verification_status = Column(String(50), default="PENDING", nullable=False) # PENDING, VERIFIED, EXPIRED, REJECTED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    employee = relationship("Employee", back_populates="certifications")
    attachment = relationship("FileAttachment", foreign_keys=[attachment_id])

    __table_args__ = (
        CheckConstraint("expiry_date IS NULL OR expiry_date >= issue_date", name="chk_certification_dates"),
    )
