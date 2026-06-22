import httpx
import pytest

from churchsuite_mcp.auth import TokenManager
from churchsuite_mcp.client import ChurchSuiteAPIError, ChurchSuiteClient


class StubTokenManager(TokenManager):
    def __init__(self, token="abc123"):
        self._token = token
        self.force_refresh_calls = 0

    async def get_token(self):
        return self._token

    async def force_refresh(self):
        self.force_refresh_calls += 1
        self._token = "refreshed"
        return self._token

    async def aclose(self):
        pass


@pytest.mark.asyncio
async def test_get_sends_bearer_token_and_params():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["url"] = request.url
        return httpx.Response(200, json={"data": []})

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = ChurchSuiteClient(StubTokenManager(), http_client=http_client)

    result = await client.get("/bookings/bookings", params={"status": "confirmed"})

    assert result == {"data": []}
    assert captured["headers"]["authorization"] == "Bearer abc123"
    assert "status=confirmed" in str(captured["url"])


@pytest.mark.asyncio
async def test_retries_once_on_401_then_succeeds():
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return httpx.Response(401)
        return httpx.Response(200, json={"data": "ok"})

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_manager = StubTokenManager()
    client = ChurchSuiteClient(token_manager, http_client=http_client)

    result = await client.get("/bookings/bookings/1")

    assert result == {"data": "ok"}
    assert token_manager.force_refresh_calls == 1


@pytest.mark.asyncio
async def test_raises_on_429():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429)

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = ChurchSuiteClient(StubTokenManager(), http_client=http_client)

    with pytest.raises(ChurchSuiteAPIError) as exc_info:
        await client.get("/bookings/bookings")

    assert exc_info.value.status_code == 429
