import io
import json
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
from fastapi.testclient import TestClient


def make_jpeg(size=(200, 200)) -> bytes:
    img = Image.new("RGB", size, (120, 80, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# Mockar ML-modellerna så de inte laddas vid import
@pytest.fixture(scope="module")
def client():
    with (
        patch("api.models.MTCNN"),
        patch("api.models.InceptionResnetV1"),
        patch("api.models.tf.keras.models.load_model"),
        patch("api.models._load_blocklist_embeddings", return_value=[]),
    ):
        from api.main import app
        with TestClient(app) as c:
            yield c


def upload(client, image_bytes, filename="test.jpg", content_type="image/jpeg"):
    return client.post(
        "/analyze",
        files={"file": (filename, image_bytes, content_type)},
    )


class TestAnalyzeEndpoint:
    def test_no_face_returns_422(self, client):
        with patch("api.main.predict", return_value=None):
            res = upload(client, make_jpeg())
        assert res.status_code == 422

    def test_blocked_returns_403(self, client):
        with (
            patch("api.main.is_blocked", return_value=True),
        ):
            res = upload(client, make_jpeg())
        assert res.status_code == 403

    def test_no_mustache_returns_score_0(self, client):
        with (
            patch("api.main.is_blocked", return_value=False),
            patch("api.main.predict", return_value={"mustache": False}),
        ):
            res = upload(client, make_jpeg())
        assert res.status_code == 200
        data = res.json()
        assert data["mustache"] is False
        assert data["score"] == 0

    def test_mustache_returns_score_and_title(self, client):
        with (
            patch("api.main.is_blocked", return_value=False),
            patch("api.main.predict", return_value={
                "mustache": True,
                "p_epic": 0.8,
                "p_medium": 0.1,
                "p_medium_thin": 0.05,
                "p_thin": 0.05,
            }),
        ):
            res = upload(client, make_jpeg())
        assert res.status_code == 200
        data = res.json()
        assert data["mustache"] is True
        assert 0 <= data["score"] <= 100
        assert isinstance(data["title"], str)
        assert isinstance(data["description"], str)

    def test_file_too_large_returns_413(self, client):
        big = b"x" * (21 * 1024 * 1024)
        res = upload(client, big)
        assert res.status_code == 413

    def test_invalid_file_returns_400(self, client):
        res = upload(client, b"detta ar inte en bild")
        assert res.status_code == 400

    def test_score_formula_with_pure_epic(self, client):
        with (
            patch("api.main.is_blocked", return_value=False),
            patch("api.main.predict", return_value={
                "mustache": True,
                "p_epic": 1.0,
                "p_medium": 0.0,
                "p_medium_thin": 0.0,
                "p_thin": 0.0,
            }),
        ):
            res = upload(client, make_jpeg())
        assert res.status_code == 200
        assert res.json()["score"] == 100


class TestLogSwishEndpoint:
    def test_log_swish_returns_ok(self, client):
        with patch("api.main.logger.log_swish_click"):
            res = client.post("/log/swish")
        assert res.status_code == 200
        assert res.json() == {"ok": True}
