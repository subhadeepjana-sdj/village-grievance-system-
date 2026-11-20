import enum
import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class UserRole(str, enum.Enum):
    CITIZEN = "CITIZEN"
    PANCHAYAT_STAFF = "PANCHAYAT_STAFF"
    DEPARTMENT_OFFICIAL = "DEPARTMENT_OFFICIAL"
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CITIZEN, nullable=False)
    village_id = Column(Integer, ForeignKey("villages.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    village = relationship("Village", back_populates="users")
    department = relationship("Department", back_populates="officials")
    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.user_id")
    ai_queries = relationship("AIQuery", back_populates="user")
