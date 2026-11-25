"""Facade: єдина точка входу до бізнес-логіки прокату (приховує builder, pricing, observer, БД)."""
from datetime import date
from ..models import Client, Vehicle, Rental
from .builder import RentalBuilder, DomainError
from .pricing import calculate_price, FINE_STRATEGIES, LATE_FEE_COEFF
from .observer import EventBus, VehicleStatusObserver, FinanceObserver, NotificationObserver


def make_bus() -> EventBus:
    bus = EventBus()
    for obs in (VehicleStatusObserver(), FinanceObserver(), NotificationObserver()):
        bus.subscribe(obs)
    return bus


class RentalFacade:
    def __init__(self, db, bus: EventBus | None = None):
        self.db, self.bus = db, bus or make_bus()

    def quote(self, vehicle_id: int, issue: date, expected: date, client_id: int | None = None) -> dict:
        v = self.db.get(Vehicle, vehicle_id)
        if not v:
            raise DomainError("Автомобіль не знайдено")
        if expected <= issue:
            raise DomainError("Дата повернення має бути пізніше дати видачі")
        done = 0
        if client_id:
            c = self.db.get(Client, client_id)
            done = sum(1 for r in c.rentals if r.status == "closed") if c else 0
        q = calculate_price(v, (expected - issue).days, done, issue)
        q["days"] = (expected - issue).days
        return q

    def rent(self, client_id, vehicle_id, issue: date, expected: date) -> Rental:
        rental = (RentalBuilder(self.db).for_client(client_id).with_vehicle(vehicle_id)
                  .for_period(issue, expected).build())
        self.db.add(rental)
        self.db.flush()
        self.bus.publish("rental_created", {"db": self.db, "rental": rental})
        self.db.commit()
        return rental

    def return_vehicle(self, rental_id: int, condition: str = "ok", actual: date | None = None) -> Rental:
        r = self.db.get(Rental, rental_id)
        if not r or r.status != "active":
            raise DomainError("Активну угоду не знайдено")
        if condition not in FINE_STRATEGIES:
            raise DomainError("Невідомий стан авто")
        actual = actual or date.today()
        overdue = max(0, (actual - r.expected_return).days)
        late_fee = round(overdue * r.vehicle.price_per_day * LATE_FEE_COEFF, 2)
        strategy = FINE_STRATEGIES[condition]
        damage = strategy.fine(r.vehicle)
        reasons = []
        if overdue: reasons.append(f"прострочення {overdue} діб: {late_fee:.0f} грн")
        if damage: reasons.append(f"{strategy.label}: {damage:.0f} грн")
        r.actual_return, r.fine = actual, round(late_fee + damage, 2)
        r.fine_reason = "; ".join(reasons)
        r.deposit_returned = round(max(0.0, r.deposit - r.fine), 2)
        r.status = "closed"
        self.bus.publish("rental_closed", {"db": self.db, "rental": r, "condition": condition})
        self.db.commit()
        return r
