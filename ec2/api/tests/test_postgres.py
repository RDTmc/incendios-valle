import pytest
from database_pg import is_pg_configured, HAS_PSYCOPG2, get_pg_connection, init_pg_schema, query_pg_first

pytestmark = pytest.mark.e2e

PG_CONFIGURED = is_pg_configured() and HAS_PSYCOPG2


@pytest.fixture(scope="module")
def pg_fixture():
    if not PG_CONFIGURED:
        pytest.skip("PostgreSQL not configured")
    init_pg_schema()


@pytest.fixture(autouse=True)
def _skip_if_no_pg():
    if not PG_CONFIGURED:
        pytest.skip("PostgreSQL not configured")


class TestPostgresMigration:

    def test_connection_and_schema(self, pg_fixture):
        with get_pg_connection() as conn:
            assert conn is not None
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public' ORDER BY table_name
                """)
                tables = [r[0] for r in cur.fetchall()]
        expected = {'users', 'reports', 'external_reports', 'firms_hotspots',
                    'weather_readings', 'incident_resources', 'alerts',
                    'audit_log', 'notifications', 'admin_2fa'}
        for t in expected:
            assert t in tables, f"Missing table: {t}"
        assert len(tables) >= len(expected)

    def test_insert_and_select_reports(self, pg_fixture):
        test_id = "test-pg-999999"
        try:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO reports (report_id, user_id, tipo, latitud, longitud, estado, created_at) "
                        "VALUES (%s, %s, %s, %s, %s, %s, NOW()::text) "
                        "ON CONFLICT (report_id) DO UPDATE SET estado = EXCLUDED.estado",
                        (test_id, "test-user", "FORESTAL", "-33.0", "-70.0", "PENDIENTE")
                    )
                    conn.commit()

            row = query_pg_first(
                "SELECT report_id, tipo, estado FROM reports WHERE report_id = %s",
                (test_id,), fetch='one'
            )
            assert row is not None, "Inserted row not found"
            assert row[0] == test_id
            assert row[1] == "FORESTAL"
            assert row[2] == "PENDIENTE"
        finally:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM reports WHERE report_id = %s", (test_id,))
                    conn.commit()

    def test_public_endpoint_returns_data(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        response = client.get("/public/dashboard-stats")
        assert response.status_code == 200
        data = response.json()
        assert "focos_activos" in data
        assert "estado_pendiente" in data
        assert "estado_activo" in data
        assert isinstance(data.get("focos_activos"), int)
        assert data["focos_activos"] >= 0
