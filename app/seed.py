"""Початкові дані для демонстрації."""
from datetime import date, timedelta
from .models import Vehicle, Client
from .patterns.factory import get_creator
from .patterns.facade import RentalFacade


def seed(db):
    if db.query(Vehicle).count():
        return
    cars = [("economy", "Skoda", "Fabia", 2022, 700), ("economy", "Renault", "Logan", 2015, 600),
            ("economy", "Hyundai", "Accent", 2020, 650), ("suv", "Toyota", "RAV4", 2021, 900),
            ("suv", "Kia", "Sportage", 2024, 950), ("minivan", "VW", "Caravelle", 2018, 1000),
            ("premium", "BMW", "530i", 2023, 1200), ("premium", "Mercedes", "E-Class", 2016, 1100)]
    for t, b, m, y, p in cars:
        db.add(get_creator(t).register(b, m, y, p))
    db.add_all([Client(full_name="Коваленко Іван Петрович", address="м. Львів, вул. Стрийська 12", phone="+380501112233"),
                Client(full_name="Шевчук Олена Миколаївна", address="м. Київ, вул. Хрещатик 5", phone="+380671234567"),
                Client(full_name="Бондар Андрій Олегович", address="м. Одеса, вул. Дерибасівська 8", phone="+380931000200")])
    db.commit()
    f = RentalFacade(db)
    t = date.today()
    f.rent(1, 1, t - timedelta(days=10), t - timedelta(days=5)); f.return_vehicle(1, "ok", t - timedelta(days=5))
    f.rent(2, 4, t - timedelta(days=20), t - timedelta(days=10)); f.return_vehicle(2, "dirty", t - timedelta(days=8))
    f.rent(1, 7, t - timedelta(days=3), t + timedelta(days=4))
    f.rent(3, 3, t - timedelta(days=1), t + timedelta(days=2))
