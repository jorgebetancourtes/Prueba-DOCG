# python/tests/test_cases.py

from flask import current_app
from sqlalchemy.exc import OperationalError
from sqlalchemy.sql import text

from python.models import db


def test_db_connection():
    """Prueba la conexión a la base de datos."""
    try:
        with current_app.app_context():
            query = text("SELECT 1")
            result = db.session.execute(query).scalar()
            assert result == 1, "La base de datos no devolvió el resultado esperado."
    except OperationalError as e:
        raise AssertionError(f"No se pudo conectar a la base de datos: {e}")
    except Exception as e:
        raise AssertionError(
            f"Error inesperado durante la prueba de la base de datos: {e}"
        )


def test_health():
    """Prueba que la ruta /health devuelva el estado correcto."""
    with current_app.test_client() as client:
        response = client.get("/inicio/health")

        assert response.status_code == 200, (
            "La ruta /health no devolvió un código de estado 200."
        )

        assert response.data.decode("utf-8") == "OK", (
            "El contenido de la respuesta de /health no es 'OK'."
        )
