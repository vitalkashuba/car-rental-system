"""REST API + роздача веб-інтерфейсу (клієнтська частина: /, адмін-частина: /admin)."""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Database, get_db
from .models import Vehicle, Client, Rental, Notification
from .schemas import VehicleIn, VehicleUpdate, ClientIn, QuoteIn, RentalIn, ReturnIn
from .patterns.factory import get_creator
from .patterns.facade import RentalFacade
from .patterns.builder import DomainError
from .patterns.report import REPORTS
from .seed import seed

ADMIN_KEY = os.getenv("ADMIN_KEY", "admin123")
STATIC = Path(__file__).resolve().parent.parent / "static"

@asynccontextmanager
async def lifespan(_app):
    db = Database().session()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Car Rental API", version="1.0", lifespan=lifespan)


def require_admin(x_admin_key: str = Header(default="")):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(403, "Потрібен ключ адміністратора (заголовок X-Admin-Key)")


def vehicle_dict(v: Vehicle):
    return {"id": v.id, "brand": v.brand, "model": v.model, "vtype": v.vtype, "year": v.year,
            "price_per_day": v.price_per_day, "deposit": v.deposit, "status": v.status}


def rental_dict(r: Rental):
    return {"id": r.id, "client": r.client.full_name, "client_id": r.client_id,
            "car": f"{r.vehicle.brand} {r.vehicle.model}", "vehicle_id": r.vehicle_id,
            "issue_date": r.issue_date.isoformat(), "expected_return": r.expected_return.isoformat(),
            "actual_return": r.actual_return.isoformat() if r.actual_return else None,
            "days": r.days, "rent_price": r.rent_price, "deposit": r.deposit, "fine": r.fine,
            "fine_reason": r.fine_reason, "deposit_returned": r.deposit_returned, "status": r.status}


def domain(fn):
    try:
        return fn()
    except (DomainError, ValueError) as e:
        raise HTTPException(400, str(e))


# ---------------- Vehicles ----------------
@app.get("/api/vehicles")
def list_vehicles(vtype: str | None = None, status: str | None = None, db=Depends(get_db)):
    q = db.query(Vehicle)
    if vtype: q = q.filter(Vehicle.vtype == vtype)
    if status: q = q.filter(Vehicle.status == status)
    return [vehicle_dict(v) for v in q.order_by(Vehicle.id)]


@app.post("/api/vehicles", status_code=201, dependencies=[Depends(require_admin)])
def create_vehicle(body: VehicleIn, db=Depends(get_db)):
    v = domain(lambda: get_creator(body.vtype).register(body.brand, body.model, body.year, body.base_price))
    db.add(v); db.commit()
    return vehicle_dict(v)


@app.patch("/api/vehicles/{vid}", dependencies=[Depends(require_admin)])
def update_vehicle(vid: int, body: VehicleUpdate, db=Depends(get_db)):
    v = db.get(Vehicle, vid)
    if not v: raise HTTPException(404, "Не знайдено")
    for k, val in body.model_dump(exclude_none=True).items():
        setattr(v, k, val)
    db.commit()
    return vehicle_dict(v)


@app.delete("/api/vehicles/{vid}", status_code=204, dependencies=[Depends(require_admin)])
def delete_vehicle(vid: int, db=Depends(get_db)):
    v = db.get(Vehicle, vid)
    if not v: raise HTTPException(404, "Не знайдено")
    if v.rentals: raise HTTPException(400, "Є історія прокату - видалення неможливе")
    db.delete(v); db.commit()


# ---------------- Clients ----------------
@app.get("/api/clients")
def list_clients(db=Depends(get_db)):
    return [{"id": c.id, "full_name": c.full_name, "address": c.address, "phone": c.phone,
             "rentals": len(c.rentals)} for c in db.query(Client).order_by(Client.id)]


@app.post("/api/clients", status_code=201)
def register_client(body: ClientIn, db=Depends(get_db)):
    c = Client(**body.model_dump())
    db.add(c); db.commit()
    return {"id": c.id, **body.model_dump()}


# ---------------- Rentals ----------------
@app.post("/api/rentals/quote")
def quote(body: QuoteIn, db=Depends(get_db)):
    return domain(lambda: RentalFacade(db).quote(body.vehicle_id, body.issue_date, body.expected_return, body.client_id))


@app.post("/api/rentals", status_code=201)
def create_rental(body: RentalIn, db=Depends(get_db)):
    return rental_dict(domain(lambda: RentalFacade(db).rent(body.client_id, body.vehicle_id, body.issue_date, body.expected_return)))


@app.post("/api/rentals/{rid}/return", dependencies=[Depends(require_admin)])
def return_rental(rid: int, body: ReturnIn, db=Depends(get_db)):
    return rental_dict(domain(lambda: RentalFacade(db).return_vehicle(rid, body.condition, body.actual_return)))


@app.get("/api/rentals")
def list_rentals(client_id: int | None = None, status: str | None = None, db=Depends(get_db)):
    q = db.query(Rental)
    if client_id: q = q.filter(Rental.client_id == client_id)
    if status: q = q.filter(Rental.status == status)
    return [rental_dict(r) for r in q.order_by(Rental.id.desc())]


@app.get("/api/notifications/{client_id}")
def notifications(client_id: int, db=Depends(get_db)):
    q = db.query(Notification).filter(Notification.client_id == client_id).order_by(Notification.id.desc())
    return [{"message": n.message, "created_at": n.created_at.isoformat(timespec="minutes")} for n in q]


# ---------------- Reports ----------------
@app.get("/api/reports/{name}", dependencies=[Depends(require_admin)])
def report(name: str, db=Depends(get_db)):
    if name not in REPORTS: raise HTTPException(404, "Невідомий звіт")
    return REPORTS[name].generate(db)


# ---------------- Web UI ----------------
@app.get("/", include_in_schema=False)
def index(): return FileResponse(STATIC / "index.html")


@app.get("/admin", include_in_schema=False)
def admin(): return FileResponse(STATIC / "admin.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
