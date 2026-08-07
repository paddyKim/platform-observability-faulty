from fastapi.testclient import TestClient

import faulty_service.main as service


client = TestClient(service.app)


def test_health_remains_ready_during_runtime_failure():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_order_request_exposes_runtime_error_to_metrics(monkeypatch):
    monkeypatch.setattr(service, "FAILURE_DELAY_SECONDS", 0)

    response = client.get("/api/orders/501")
    output = client.get("/metrics").text

    assert response.status_code == 500
    assert response.json()["error"] == "DEPENDENCY_TIMEOUT"
    assert 'application="platform-observability-faulty"' in output
    assert 'route="/api/orders/{order_id}",status="500"' in output
