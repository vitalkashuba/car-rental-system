"""Strategy (тариф за терміном, штрафи за стан авто) + Decorator (надбавки/знижки до ціни)."""
from abc import ABC, abstractmethod
from datetime import date


# ---------- Strategy: тариф залежно від терміну прокату ----------
class TariffStrategy(ABC):
    name = ""
    @abstractmethod
    def discount(self, days: int) -> float: ...


class DailyTariff(TariffStrategy):
    name = "Добовий (1-6 діб)"
    def discount(self, days): return 0.0


class WeeklyTariff(TariffStrategy):
    name = "Тижневий (7-29 діб)"
    def discount(self, days): return 0.10


class MonthlyTariff(TariffStrategy):
    name = "Місячний (30+ діб)"
    def discount(self, days): return 0.20


def select_tariff(days: int) -> TariffStrategy:
    if days >= 30: return MonthlyTariff()
    if days >= 7: return WeeklyTariff()
    return DailyTariff()


# ---------- Decorator: ціна прокату ----------
class PriceComponent(ABC):
    @abstractmethod
    def cost(self) -> float: ...
    @abstractmethod
    def describe(self) -> list[str]: ...


class BasePrice(PriceComponent):
    def __init__(self, price_per_day: float, days: int, tariff: TariffStrategy):
        self.price, self.days, self.tariff = price_per_day, days, tariff

    def cost(self):
        return self.price * self.days * (1 - self.tariff.discount(self.days))

    def describe(self):
        d = int(self.tariff.discount(self.days) * 100)
        return [f"{self.price:.2f} грн x {self.days} діб, тариф «{self.tariff.name}» (знижка {d}%)"]


class PriceDecorator(PriceComponent):
    def __init__(self, wrapped: PriceComponent):
        self.wrapped = wrapped
    def cost(self): return self.wrapped.cost()
    def describe(self): return self.wrapped.describe()


class YearSurchargeDecorator(PriceDecorator):
    """Вартість залежить від року випуску: нове авто дорожче, старе дешевше."""
    def __init__(self, wrapped, year: int, today: date | None = None):
        super().__init__(wrapped)
        age = (today or date.today()).year - year
        self.k = 1.10 if age <= 2 else (0.90 if age >= 9 else 1.0)

    def cost(self): return self.wrapped.cost() * self.k

    def describe(self):
        note = {1.10: "надбавка +10% (авто до 2 років)", 0.90: "знижка -10% (авто від 9 років)"}.get(self.k)
        return self.wrapped.describe() + ([note] if note else [])


class LoyaltyDiscountDecorator(PriceDecorator):
    """Постійним клієнтам (3+ завершені прокати) - знижка 5%."""
    def __init__(self, wrapped, completed_rentals: int):
        super().__init__(wrapped)
        self.k = 0.95 if completed_rentals >= 3 else 1.0

    def cost(self): return self.wrapped.cost() * self.k

    def describe(self):
        return self.wrapped.describe() + (["знижка постійного клієнта -5%"] if self.k < 1 else [])


def calculate_price(vehicle, days: int, completed_rentals: int = 0, today: date | None = None) -> dict:
    tariff = select_tariff(days)
    price: PriceComponent = BasePrice(vehicle.price_per_day, days, tariff)
    price = YearSurchargeDecorator(price, vehicle.year, today)
    price = LoyaltyDiscountDecorator(price, completed_rentals)
    return {"total": round(price.cost(), 2), "deposit": vehicle.deposit,
            "tariff": tariff.name, "breakdown": price.describe()}


# ---------- Strategy: штраф за стан авто при поверненні ----------
class DamageFineStrategy(ABC):
    label = ""
    @abstractmethod
    def fine(self, vehicle) -> float: ...


class NoDamage(DamageFineStrategy):
    label = "без пошкоджень"
    def fine(self, vehicle): return 0.0


class DirtyInterior(DamageFineStrategy):
    label = "брудний салон/кузов"
    def fine(self, vehicle): return 300.0


class MinorDamage(DamageFineStrategy):
    label = "незначні пошкодження"
    def fine(self, vehicle): return round(vehicle.deposit * 0.25, 2)


class MajorDamage(DamageFineStrategy):
    label = "серйозні пошкодження"
    def fine(self, vehicle): return round(vehicle.deposit * 0.75, 2)


FINE_STRATEGIES = {"ok": NoDamage(), "dirty": DirtyInterior(), "minor": MinorDamage(), "major": MajorDamage()}
LATE_FEE_COEFF = 1.5   # прострочення: 150% добової ціни за кожну добу
