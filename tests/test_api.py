import os, tempfile
os.environ["CARRENTAL_DB"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "t.db")
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.patterns.pricing import calculate_price, select_tariff
from app.patterns.factory import get_creator

H = {"X-Admin-Key": "admin123"}
t = date.today()


def test_flow():
    with TestClient(app) as c:
        cars = c.get("/api/vehicles").json()
        assert len(cars) == 8
        cl = c.post("/api/clients", json={"full_name": "Тест Тестович", "address": "Львів", "phone": "+380000000"}).json()
        free = next(v for v in c.get("/api/vehicles?status=available").json())
        q = c.post("/api/rentals/quote", json={"vehicle_id": free["id"], "issue_date": str(t), "expected_return": str(t + timedelta(days=8))}).json()
        assert q["days"] == 8 and q["total"] > 0
        r = c.post("/api/rentals", json={"client_id": cl["id"], "vehicle_id": free["id"], "issue_date": str(t), "expected_return": str(t + timedelta(days=8))})
        assert r.status_code == 201
        assert c.post("/api/rentals", json={"client_id": cl["id"], "vehicle_id": free["id"], "issue_date": str(t), "expected_return": str(t + timedelta(days=2))}).status_code == 400
        ret = c.post(f"/api/rentals/{r.json()['id']}/return", headers=H, json={"condition": "minor", "actual_return": str(t + timedelta(days=10))}).json()
        assert ret["fine"] > 0 and ret["deposit_returned"] == max(0, ret["deposit"] - ret["fine"])
        assert c.get(f"/api/notifications/{cl['id']}").json()
        assert c.get("/api/reports/finance").status_code == 403
        assert c.get("/api/reports/finance", headers=H).json()["summary"]["Загальний дохід, грн"] > 0
        assert c.get("/api/reports/occupancy", headers=H).status_code == 200


def test_patterns():
    assert select_tariff(3).discount(3) == 0 and select_tariff(7).discount(7) == 0.1 and select_tariff(30).discount(30) == 0.2
    v = get_creator("premium").register("A", "B", 2024, 1000)
    assert v.price_per_day == 2200 and v.deposit == 22000
    p = calculate_price(v, 2, 0, t)
    assert round(p["total"], 2) == round(2200 * 2 * 1.10, 2)
