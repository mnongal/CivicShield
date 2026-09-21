from app.hosting import allowed_hosts
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import TrustedHostMiddleware


def test_render_host_allowed_but_unrelated_host_rejected(monkeypatch):
    monkeypatch.setenv('RENDER_EXTERNAL_HOSTNAME', 'civicshield-example.onrender.com')
    monkeypatch.setenv('ALLOWED_HOSTS', 'example.org')
    app = FastAPI()
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts())
    @app.get('/')
    def home():
        return {'ok': True}
    with TestClient(app) as client:
        assert client.get('/', headers={'Host': 'civicshield-example.onrender.com'}).status_code == 200
        assert client.get('/', headers={'Host': 'example.org'}).status_code == 200
        assert client.get('/', headers={'Host': 'unrelated.onrender.com'}).status_code == 400
