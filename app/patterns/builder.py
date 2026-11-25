"""Builder: покрокове складання угоди прокату з валідацією і розрахунком ціни."""
from datetime import date
from ..models import Client, Vehicle, Rental
from .pricing import calculate_price


class DomainError(Exception):
    pass


class RentalBuilder:
    def __init__(self, db):
        self.db = db
        self._client = self._vehicle = self._issue = self._expected = None

    def for_client(self, client_id: int):
        self._client = self.db.get(Client, client_id)
        return self

    def with_vehicle(self, vehicle_id: int):
        self._vehicle = self.db.get(Vehicle, vehicle_id)
        return self

    def for_period(self, issue: date, expected_return: date):
        self._issue, self._expected = issue, expected_return
        return self

    def build(self) -> Rental:
        if not self._client:
            raise DomainError("Клієнта не знайдено (спочатку зареєструйтесь)")
        if not self._vehicle:
            raise DomainError("Автомобіль не знайдено")
        if self._vehicle.status != "available":
            raise DomainError("Автомобіль зараз недоступний")
        if not (self._issue and self._expected) or self._expected <= self._issue:
            raise DomainError("Дата повернення має бути пізніше дати видачі")
        days = (self._expected - self._issue).days
        done = sum(1 for r in self._client.rentals if r.status == "closed")
        price = calculate_price(self._vehicle, days, done, self._issue)
        return Rental(client_id=self._client.id, vehicle_id=self._vehicle.id,
                      issue_date=self._issue, expected_return=self._expected, days=days,
                      rent_price=price["total"], deposit=self._vehicle.deposit, status="active")
