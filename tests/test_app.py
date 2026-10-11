import socket
from unittest.mock import MagicMock

import pytest
import redis

import app as visit_app


@pytest.fixture
def fake_cache(monkeypatch):
    """Remplace le client Redis par un faux : aucun Redis réel n'est nécessaire."""
    cache = MagicMock()
    monkeypatch.setattr(visit_app, "cache", cache)
    monkeypatch.setattr(visit_app.time, "sleep", lambda _s: None)  # pas d'attente
    return cache


@pytest.fixture
def client():
    return visit_app.app.test_client()


def test_page_returns_200(fake_cache, client):
    fake_cache.incr.return_value = 1
    assert client.get("/").status_code == 200


def test_message_contains_counter_and_container_id(fake_cache, client):
    fake_cache.incr.return_value = 7
    body = client.get("/").get_data(as_text=True)
    assert "Bonjour ! Cette page a été vue 7 fois." in body
    assert socket.gethostname() in body


def test_increments_hits_key(fake_cache, client):
    fake_cache.incr.return_value = 1
    client.get("/")
    fake_cache.incr.assert_called_once_with("hits")


def test_retries_then_succeeds(fake_cache):
    fake_cache.incr.side_effect = [redis.exceptions.ConnectionError(), 3]
    assert visit_app.get_hit_count() == 3
    assert fake_cache.incr.call_count == 2


def test_raises_when_redis_stays_down(fake_cache):
    fake_cache.incr.side_effect = redis.exceptions.ConnectionError()
    with pytest.raises(redis.exceptions.ConnectionError):
        visit_app.get_hit_count()
    assert fake_cache.incr.call_count == 6  # 1 essai + 5 reprises
