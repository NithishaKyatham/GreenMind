import os
os.environ["USE_SQLITE"] = "true"
os.environ["SQLITE_PATH"] = "./test_greenmind.db"
os.environ["ALLOW_MODEL_FALLBACK"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_greenmind.db"):
        os.remove("./test_greenmind.db")


@pytest.fixture()
def client():
    return TestClient(app)
