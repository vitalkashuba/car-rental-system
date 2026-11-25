"""Template Method: скелет генерації звіту фіксований, кроки collect/columns/summarize - у підкласах."""
from abc import ABC, abstractmethod
from datetime import date
from ..models import Vehicle, Rental


class Report(ABC):
    title = ""

    def generate(self, db) -> dict:                     # шаблонний метод
        rows = self.collect(db)
        return {"title": self.title, "generated": date.today().isoformat(),
                "columns": self.columns(), "rows": rows, "summary": self.summarize(rows)}

    @abstractmethod
    def collect(self, db) -> list[dict]: ...
    @abstractmethod
    def columns(self) -> list[list[str]]: ...
    @abstractmethod
    def summarize(self, rows) -> dict: ...


class OccupancyReport(Report):
    title = "Автопарк у розрізі зайнятості"

    def columns(self):
        return [["car", "Автомобіль"], ["status", "Статус"], ["client", "Орендар"],
                ["due", "Повернення"], ["rentals", "Угод"], ["days", "Діб у прокаті"]]

    def collect(self, db):
        rows = []
        for v in db.query(Vehicle).order_by(Vehicle.id):
            active = next((r for r in v.rentals if r.status == "active"), None)
            rows.append({"car": f"{v.brand} {v.model} ({v.year})", "status": v.status,
                         "client": active.client.full_name if active else "-",
                         "due": active.expected_return.isoformat() if active else "-",
                         "rentals": len(v.rentals), "days": sum(r.days for r in v.rentals)})
        return rows

    def summarize(self, rows):
        n = len(rows) or 1
        busy = sum(1 for r in rows if r["status"] == "rented")
        return {"Всього авто": len(rows), "У прокаті": busy, "Вільні": sum(1 for r in rows if r["status"] == "available"),
                "Завантаженість, %": round(100 * busy / n, 1)}


class FinanceReport(Report):
    title = "Автопарк у розрізі фінансових показників"

    def columns(self):
        return [["car", "Автомобіль"], ["rent", "Дохід від прокату, грн"], ["fines", "Штрафи, грн"],
                ["total", "Разом, грн"], ["avg", "Середній чек, грн"], ["held", "Застава на руках, грн"]]

    def collect(self, db):
        rows = []
        for v in db.query(Vehicle).order_by(Vehicle.id):
            rent = sum(r.rent_price for r in v.rentals)
            fines = sum(r.fine or 0 for r in v.rentals)
            held = sum(r.deposit for r in v.rentals if r.status == "active")
            rows.append({"car": f"{v.brand} {v.model}", "rent": round(rent, 2), "fines": round(fines, 2),
                         "total": round(rent + fines, 2),
                         "avg": round(rent / len(v.rentals), 2) if v.rentals else 0, "held": round(held, 2)})
        return rows

    def summarize(self, rows):
        return {"Дохід від прокату, грн": round(sum(r["rent"] for r in rows), 2),
                "Штрафи, грн": round(sum(r["fines"] for r in rows), 2),
                "Загальний дохід, грн": round(sum(r["total"] for r in rows), 2),
                "Застава на руках, грн": round(sum(r["held"] for r in rows), 2)}


REPORTS = {"occupancy": OccupancyReport(), "finance": FinanceReport()}
