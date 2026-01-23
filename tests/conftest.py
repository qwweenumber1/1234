import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Mock environment variables for testing
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
os.makedirs(DB_DIR, exist_ok=True)

os.environ["AUTH_DATABASE_URL"] = f"sqlite:///{os.path.join(DB_DIR, 'test_auth.db')}"
os.environ["ORDERS_DATABASE_URL"] = f"sqlite:///{os.path.join(DB_DIR, 'test_orders.db')}"
os.environ["SECRET_KEY"] = "test_secret_key"

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_dbs():
    # Cleanup before and after
    for db_name in ["test_auth.db", "test_orders.db"]:
        path = os.path.join(DB_DIR, db_name)
        if os.path.exists(path):
            os.remove(path)
    yield
    for db_name in ["test_auth.db", "test_orders.db"]:
        path = os.path.join(DB_DIR, db_name)
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

@pytest.fixture(scope="session")
def test_db_auth():
    from services.auth.database import Base, engine
    from services.auth.models import User
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def test_db_orders():
    from services.orders.database import Base, engine
    from services.orders.models import Order
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def auth_client(test_db_auth):
    from services.auth.main import app, get_db
    app.dependency_overrides[get_db] = lambda: test_db_auth
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def orders_client(test_db_orders):
    from services.orders.main import app, get_db
    app.dependency_overrides[get_db] = lambda: test_db_orders
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def gateway_client():
    from gateway.main import app
    with TestClient(app) as client:
        yield client
