from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    contact_information = Column(Text, nullable=True)

    officials = relationship("User", back_populates="department")
    complaints = relationship("Complaint", back_populates="department")
