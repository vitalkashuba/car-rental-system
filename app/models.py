"""ORM-моделі (SQLAlchemy). Таблиці: vehicles, clients, rentals, finance_records, notifications."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    vtype = Column(String(20), nullable=False)          # economy | suv | premium | minivan
    year = Column(Integer, nullable=False)
    price_per_day = Column(Float, nullable=False)       # ціна прокату за добу, грн
    deposit = Column(Float, nullable=False)             # заставна сума, грн
    status = Column(String(20), default="available")    # available | rented | maintenance
    rentals = relationship("Rental", back_populates="vehicle")


class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(120), nullable=False)
    address = Column(String(200), nullable=False)
    phone = Column(String(30), nullable=False)
    rentals = relationship("Rental", back_populates="client")


class Rental(Base):
    __tablename__ = "rentals"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    issue_date = Column(Date, nullable=False)
    expected_return = Column(Date, nullable=False)
    actual_return = Column(Date)
    days = Column(Integer, nullable=False)
    rent_price = Column(Float, nullable=False)
    deposit = Column(Float, nullable=False)
    fine = Column(Float, default=0.0)
    fine_reason = Column(String(200), default="")
    deposit_returned = Column(Float, default=0.0)
    status = Column(String(20), default="active")       # active | closed
    client = relationship("Client", back_populates="rentals")
    vehicle = relationship("Vehicle", back_populates="rentals")


class FinanceRecord(Base):
    __tablename__ = "finance_records"
    id = Column(Integer, primary_key=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"))
    kind = Column(String(20))      # rent | fine | deposit_hold | deposit_refund
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    message = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow)
