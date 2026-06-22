"""Thin async client for the ChurchSuite API v2."""

from __future__ import annotations

import httpx

from .auth import TokenManager

API_BASE_URL = "https://api.churchsuite.com/v2"


class ChurchSuiteAPIError(RuntimeError):
    """Raised for non-2xx responses from the ChurchSuite API."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class ChurchSuiteClient:
    """Authenticated wrapper around the ChurchSuite API."""

    def __init__(
        self,
        token_manager: TokenManager,
        base_url: str = API_BASE_URL,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._token_manager = token_manager
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.AsyncClient()
        self._owns_http_client = http_client is None

    async def get(self, path: str, params: dict | None = None) -> dict:
        token = await self._token_manager.get_token()
        response = await self._request(path, params, token)

        if response.status_code == 401:
            # Token may have been revoked or expired early server-side; refresh once and retry.
            token = await self._token_manager.force_refresh()
            response = await self._request(path, params, token)

        if response.status_code == 429:
            raise ChurchSuiteAPIError(
                429, "ChurchSuite API rate limit exceeded. Please retry later."
            )
        if response.status_code >= 400:
            raise ChurchSuiteAPIError(
                response.status_code,
                f"ChurchSuite API request to {path} failed: {response.text}",
            )

        return response.json()

    async def _request(self, path: str, params: dict | None, token: str) -> httpx.Response:
        return await self._http_client.get(
            f"{self._base_url}{path}",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
        )

    async def aclose(self) -> None:
        if self._owns_http_client:
            await self._http_client.aclose()
        await self._token_manager.aclose()
