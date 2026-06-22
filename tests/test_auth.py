import httpx
import pytest

from churchsuite_mcp.auth import AuthError, TokenManager


def _mock_transport(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_fetches_and_caches_token():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"access_token": "abc123", "expires_in": 3600})

    http_client = _mock_transport(handler)
    manager = TokenManager("id", "secret", http_client=http_client)

    token1 = await manager.get_token()
    token2 = await manager.get_token()

    assert token1 == "abc123"
    assert token2 == "abc123"
    assert len(calls) == 1  # second call used the cached token


@pytest.mark.asyncio
async def test_refetches_when_expired():
    responses = iter(
        [
            httpx.Response(200, json={"access_token": "first", "expires_in": -1}),
            httpx.Response(200, json={"access_token": "second", "expires_in": 3600}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    http_client = _mock_transport(handler)
    manager = TokenManager("id", "secret", http_client=http_client)

    token1 = await manager.get_token()
    token2 = await manager.get_token()

    assert token1 == "first"
    assert token2 == "second"


@pytest.mark.asyncio
async def test_force_refresh_bypasses_cache():
    responses = iter(
        [
            httpx.Response(200, json={"access_token": "first", "expires_in": 3600}),
            httpx.Response(200, json={"access_token": "second", "expires_in": 3600}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    http_client = _mock_transport(handler)
    manager = TokenManager("id", "secret", http_client=http_client)

    await manager.get_token()
    refreshed = await manager.force_refresh()

    assert refreshed == "second"


@pytest.mark.asyncio
async def test_raises_auth_error_on_failure():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, text="invalid_client")

    http_client = _mock_transport(handler)
    manager = TokenManager("id", "wrong-secret", http_client=http_client)

    with pytest.raises(AuthError):
        await manager.get_token()
