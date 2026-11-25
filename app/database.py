"""Singleton: єдине з'єднання з БД на весь застосунок."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


class Database:
    _instance = None

    def __new__(cls, url: str | None = None):
        if cls._instance is None:
            url = url or os.getenv("CARRENTAL_DB", "sqlite:///./carrental.db")
            inst = super().__new__(cls)
            inst.engine = create_engine(url, connect_args={"check_same_thread": False})
            inst._session_factory = sessionmaker(bind=inst.engine, autoflush=False)
            Base.metadata.create_all(inst.engine)
            cls._instance = inst
        return cls._instance

    def session(self):
        return self._session_factory()


def get_db():
    """FastAPI-залежність (Dependency Injection): сесія на кожен запит."""
    db = Database().session()
    try:
        yield db
    finally:
        db.close()
