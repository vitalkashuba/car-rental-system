from datetime import date
from pydantic import BaseModel, Field


class VehicleIn(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    vtype: str
    year: int = Field(ge=1990, le=2100)
    base_price: float = Field(gt=0, description="Базова ціна доби (до множника класу)")


class VehicleUpdate(BaseModel):
    price_per_day: float | None = Field(default=None, gt=0)
    deposit: float | None = Field(default=None, gt=0)
    status: str | None = None


class ClientIn(BaseModel):
    full_name: str = Field(min_length=3)
    address: str = Field(min_length=3)
    phone: str = Field(min_length=7)


class QuoteIn(BaseModel):
    vehicle_id: int
    issue_date: date
    expected_return: date
    client_id: int | None = None


class RentalIn(BaseModel):
    client_id: int
    vehicle_id: int
    issue_date: date
    expected_return: date


class ReturnIn(BaseModel):
    condition: str = "ok"          # ok | dirty | minor | major
    actual_return: date | None = None
