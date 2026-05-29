from sqlalchemy import Column, Integer, String, Numeric
from app.database import Base

class Material(Base):
    __tablename__ = "materials"

    material_id = Column(Integer, primary_key=True)
    material_code = Column(String(50))
    material_name = Column(String(255))
    category = Column(String(100))
    unit_of_measure = Column(String(50))

    current_quantity = Column(Numeric(12, 3))
    minimum_stock_level = Column(Numeric(12, 3))

    status = Column(Integer)