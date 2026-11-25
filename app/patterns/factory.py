"""Factory Method: кожен тип авто створюється власним creator-ом зі своїми коефіцієнтами."""
from abc import ABC, abstractmethod
from ..models import Vehicle


class VehicleCreator(ABC):
    vtype: str
    class_coeff: float      # множник до базової ціни класу
    deposit_days: int       # застава = ціна доби * deposit_days

    @abstractmethod
    def make_vehicle(self, brand: str, model: str, year: int, base_price: float) -> Vehicle:
        """Фабричний метод - підкласи визначають, який продукт створюється."""

    def register(self, brand, model, year, base_price) -> Vehicle:
        if base_price <= 0:
            raise ValueError("Ціна має бути додатною")
        return self.make_vehicle(brand, model, year, base_price)

    def _build(self, brand, model, year, base_price) -> Vehicle:
        price = round(base_price * self.class_coeff, 2)
        return Vehicle(brand=brand, model=model, vtype=self.vtype, year=year,
                       price_per_day=price, deposit=round(price * self.deposit_days, 2),
                       status="available")


class EconomyCreator(VehicleCreator):
    vtype, class_coeff, deposit_days = "economy", 1.0, 5
    def make_vehicle(self, *a): return self._build(*a)


class SuvCreator(VehicleCreator):
    vtype, class_coeff, deposit_days = "suv", 1.4, 7
    def make_vehicle(self, *a): return self._build(*a)


class MinivanCreator(VehicleCreator):
    vtype, class_coeff, deposit_days = "minivan", 1.25, 6
    def make_vehicle(self, *a): return self._build(*a)


class PremiumCreator(VehicleCreator):
    vtype, class_coeff, deposit_days = "premium", 2.2, 10
    def make_vehicle(self, *a): return self._build(*a)


CREATORS = {c.vtype: c() for c in (EconomyCreator, SuvCreator, MinivanCreator, PremiumCreator)}


def get_creator(vtype: str) -> VehicleCreator:
    try:
        return CREATORS[vtype]
    except KeyError:
        raise ValueError(f"Невідомий тип авто: {vtype}")
