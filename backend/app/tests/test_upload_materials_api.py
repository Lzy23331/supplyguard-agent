from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def unwrap(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_upload_txt_material_parses():
    response = client.post(
        "/api/uploads/materials",
        files={"file": ("risk.txt", "供应商存在疑似制裁名单关联和黑名单风险提示。", "text/plain")},
    )

    assert response.status_code == 200
    data = unwrap(response)
    assert data["upload_id"]
    assert data["status"] == "parsed"
    assert data["text_length"] > 0

    detail = unwrap(client.get(f"/api/uploads/{data['upload_id']}"))
    assert detail["status"] == "parsed"


def test_upload_rejects_unsupported_extension():
    response = client.post(
        "/api/uploads/materials",
        files={"file": ("material.docx", b"fake", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False
