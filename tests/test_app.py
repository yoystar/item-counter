# tests/test_app.py
import io
import json
import os
import pytest
from app import app as flask_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr('app.UPLOAD_FOLDER', str(tmp_path))
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def test_upload_returns_image_url(client, test_image_3_items):
    with open(test_image_3_items, 'rb') as f:
        data = {'file': (f, 'test.png')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert 'image_url' in body
    assert 'width' in body
    assert 'height' in body


def test_upload_rejects_non_image(client):
    data = {'file': (io.BytesIO(b'not an image'), 'file.txt')}
    resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert resp.status_code == 400


def test_detect_returns_items(client, test_image_3_items):
    resp = client.post('/detect', json={'image_path': test_image_3_items})
    assert resp.status_code == 200
    body = resp.get_json()
    assert 'items' in body
    assert isinstance(body['items'], list)


def test_export_returns_png(client, test_image_3_items):
    labels = [
        {"x": 80, "y": 80, "number": 1},
        {"x": 250, "y": 110, "number": 2},
    ]
    resp = client.post('/export', json={
        'image_path': test_image_3_items,
        'labels': labels
    })
    assert resp.status_code == 200
    assert resp.content_type == 'image/png'


def test_export_empty_labels_rejected(client, test_image_3_items):
    resp = client.post('/export', json={
        'image_path': test_image_3_items,
        'labels': []
    })
    assert resp.status_code == 400


def test_detect_invalid_path_returns_400(client):
    resp = client.post('/detect', json={'image_path': 'nonexistent.png'})
    assert resp.status_code == 400


def test_upload_response_includes_image_path(client, test_image_3_items):
    with open(test_image_3_items, 'rb') as f:
        data = {'file': (f, 'test.png')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
    body = resp.get_json()
    assert 'image_path' in body


def test_detect_rejects_path_traversal(client):
    resp = client.post('/detect', json={'image_path': '/etc/passwd'})
    assert resp.status_code == 400


def test_export_rejects_path_traversal(client, test_image_3_items):
    resp = client.post('/export', json={
        'image_path': '/etc/passwd',
        'labels': [{"x": 80, "y": 80, "number": 1}]
    })
    assert resp.status_code == 400


def test_detect_accepts_new_params(client, test_image_3_items):
    resp = client.post('/detect', json={
        'image_path': test_image_3_items,
        'block_size': 51,
        'c_value': 10,
        'morph_iterations': 2,
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert 'items' in body
