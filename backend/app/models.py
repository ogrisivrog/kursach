from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    qty_available = Column(Integer, nullable=False, default=0)

    item = relationship("Item")
    location = relationship("Location")

    __table_args__ = (
        UniqueConstraint("item_id", "location_id", name="uq_inventory_item_location"),
    )

class Requirement(Base):
    """
    Требования по ОП (простая версия).
    Пока item_name храним строкой (без маппинга на Item).
    """
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True)

    discipline = Column(String, nullable=True, index=True)  # например: "Технология программирования"
    lab = Column(String, nullable=True, index=True)         # например: "Компьютерный класс 201В"

    item_name = Column(String, nullable=False, index=True)
    qty_required = Column(Integer, nullable=False, default=0)