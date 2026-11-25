"""Observer: подієва шина. Підписники реагують на події прокату незалежно один від одного."""
from abc import ABC, abstractmethod
from ..models import FinanceRecord, Notification


class Observer(ABC):
    @abstractmethod
    def update(self, event: str, ctx: dict) -> None: ...


class EventBus:                       # Subject
    def __init__(self):
        self._subs: list[Observer] = []

    def subscribe(self, obs: Observer):
        self._subs.append(obs)

    def publish(self, event: str, ctx: dict):
        for obs in self._subs:
            obs.update(event, ctx)


class VehicleStatusObserver(Observer):
    def update(self, event, ctx):
        rental, db = ctx["rental"], ctx["db"]
        if event == "rental_created":
            rental.vehicle.status = "rented"
        elif event == "rental_closed":
            rental.vehicle.status = "maintenance" if ctx.get("condition") == "major" else "available"


class FinanceObserver(Observer):
    def update(self, event, ctx):
        rental, db = ctx["rental"], ctx["db"]
        if event == "rental_created":
            db.add(FinanceRecord(rental_id=rental.id, kind="rent", amount=rental.rent_price))
            db.add(FinanceRecord(rental_id=rental.id, kind="deposit_hold", amount=rental.deposit))
        elif event == "rental_closed":
            if rental.fine > 0:
                db.add(FinanceRecord(rental_id=rental.id, kind="fine", amount=rental.fine))
            db.add(FinanceRecord(rental_id=rental.id, kind="deposit_refund", amount=rental.deposit_returned))


class NotificationObserver(Observer):
    def update(self, event, ctx):
        rental, db = ctx["rental"], ctx["db"]
        v = rental.vehicle
        if event == "rental_created":
            msg = (f"Авто {v.brand} {v.model} видано. Повернення до {rental.expected_return:%d.%m.%Y}. "
                   f"Заставу {rental.deposit:.0f} грн внесено.")
        elif event == "rental_closed":
            msg = (f"Авто повернено. Штраф: {rental.fine:.0f} грн. "
                   f"Повернено застави: {rental.deposit_returned:.0f} грн.")
        else:
            return
        db.add(Notification(client_id=rental.client_id, message=msg))
