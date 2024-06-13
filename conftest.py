import pytest
from app import app  # Reemplaza 'your_flask_app' con el nombre del módulo donde está definido tu Flask app

@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            yield client
