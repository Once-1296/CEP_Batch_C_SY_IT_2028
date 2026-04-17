import pytest
from fastapi.testclient import TestClient

from main import app
from app.config.data import initialize_csv_data

# Ensure models are loaded before running tests
@pytest.fixture(scope="session", autouse=True)
def setup_models():
    initialize_csv_data()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
