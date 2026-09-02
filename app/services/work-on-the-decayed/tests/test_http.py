"""Focused checks for the Flask request and response boundary."""

from flask.testing import FlaskClient
import pytest

from work_on_the_decayed.http import create_app


@pytest.fixture
def client() -> FlaskClient:
    return create_app().test_client()


def test_http_boundary_returns_the_exact_success_shape(client: FlaskClient) -> None:
    response = client.post(
        "/v1/rotate-symbol",
        json={"action": "rotate-symbol"},
    )

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.get_json() == {"quarterTurns": 1}


def test_http_boundary_rejects_an_invalid_operation(client: FlaskClient) -> None:
    response = client.post(
        "/v1/rotate-symbol",
        json={"action": "unknown"},
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": {"code": "invalid-request"}}


def test_http_boundary_rejects_malformed_json(client: FlaskClient) -> None:
    response = client.post(
        "/v1/rotate-symbol",
        data="{",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": {"code": "invalid-json"}}


def test_http_boundary_requires_json_content_type(client: FlaskClient) -> None:
    response = client.post("/v1/rotate-symbol", data="action=rotate-symbol")

    assert response.status_code == 415
    assert response.get_json() == {"error": {"code": "unsupported-media-type"}}
