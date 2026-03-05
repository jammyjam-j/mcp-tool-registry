Let's open core/registry.py(we can't actually open but guess). We'll write conftest that imports app.main.app and provides client fixture. Also database fixture to clear tools table before each test. Use SQLAlchemy session from db.py.

We need to seed sample tool maybe via registry.register_tool? Let's look at registry implementation.import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.db import Base, get_db
from app.main import app as fastapi_app
from app.core.registry import ToolRegistry
from app.tools.sample_tool import SampleTool


@pytest.fixture(scope="session")
def db_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture(scope="session")
def engine(db_url):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, class_=Session, expire_on_commit=False)

    def _get_db() -> Session:
        return session_factory()

    yield _get_db

    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    @contextmanager
    def override_get_db():
        try:
            db = db_session()
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = lambda: next(override_get_db())
    with TestClient(fastapi_app) as client_instance:
        yield client_instance
    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def registry(client):
    ToolRegistry.register_tool(SampleTool)
    yield ToolRegistry
    ToolRegistry.unregister_all()
```