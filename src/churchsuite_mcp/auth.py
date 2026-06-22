"""OAuth2 client-credentials auth for the ChurchSuite API."""

from __future__ import annotations

import time

import anyio
import httpx

TOKEN_URL = "https://login.churchsuite.com/oauth2/token"

# Refresh this many seconds before actual expiry to avoid races against in-flight requests.
_EXPIRY_MARGIN_SECONDS = 30


class AuthError(RuntimeError):
    """Raised when the ChurchSuite token endpoint rejects the credentials."""


class TokenManager:
    """Fetches and caches an OAuth2 access token via the client_credentials grant."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: str = "bookings.read",
        token_url: str = TOKEN_URL,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token_url = token_url
        self._http_client = http_client or httpx.AsyncClient()
        self._owns_http_client = http_client is None

        self._access_token: str | None = None
        self._expires_at: float = 0.0
        self._lock = anyio.Lock()

    async def get_token(self) -> str:
        async with self._lock:
            if self._access_token is None or time.monotonic() >= self._expires_at:
                await self._fetch_token()
            return self._access_token  # type: ignore[return-value]

    async def force_refresh(self) -> str:
        async with self._lock:
            await self._fetch_token()
            return self._access_token  # type: ignore[return-value]

    async def _fetch_token(self) -> None:
        response = await self._http_client.post(
            self._token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": self._scope,
            },
        )
        if response.status_code >= 400:
            raise AuthError(
                f"ChurchSuite token request failed ({response.status_code}): {response.text}"
            )

        payload = response.json()
        self._access_token = payload["access_token"]
        expires_in = payload.get("expires_in", 3600)
        self._expires_at = time.monotonic() + expires_in - _EXPIRY_MARGIN_SECONDS

    async def aclose(self) -> None:
        if self._owns_http_client:
            await self._http_client.aclose()
