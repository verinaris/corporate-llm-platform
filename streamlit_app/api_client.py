"""
API-Client.

Dünner Wrapper um httpx, der mit dem FastAPI-Backend spricht.

Analogie: Wie der Übersetzer am Schalter — du sagst "Login mit X und Y",
er kümmert sich um das genaue Protokoll im Hintergrund.
"""

from typing import Any, Optional

import httpx

from streamlit_app.config import BACKEND_URL


class APIError(Exception):
    """Geworfen bei Fehlern aus dem Backend."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


class APIClient:
    """Spricht mit dem FastAPI-Backend."""

    def __init__(self, token: Optional[str] = None, base_url: str = BACKEND_URL):
        self.token = token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #
    def login(self, email: str, password: str) -> dict[str, Any]:
        """OAuth2-Password-Flow. Liefert Dict mit access_token + user."""
        try:
            r = httpx.post(
                f"{self.base_url}/auth/login",
                data={"username": email, "password": password},
                timeout=10,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e

        if r.status_code != 200:
            detail = _extract_detail(r)
            raise APIError(r.status_code, detail)
        return r.json()

    def me(self) -> dict[str, Any]:
        return self._get("/auth/me")

    # ------------------------------------------------------------------ #
    # Chat
    # ------------------------------------------------------------------ #
    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"messages": messages}
        if model:
            payload["model"] = model
        if max_tokens:
            payload["max_tokens"] = max_tokens
        return self._post("/chat", payload, timeout=60)

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #
    def stats(self) -> dict[str, Any]:
        return self._get("/stats")

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _get(self, path: str, timeout: int = 10) -> dict[str, Any]:
        try:
            r = httpx.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
                timeout=timeout,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code != 200:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        timeout: int = 30,
    ) -> dict[str, Any]:
        try:
            r = httpx.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=self._headers(),
                timeout=timeout,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code not in (200, 201):
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()


def _extract_detail(response: httpx.Response) -> str:
    """Best-effort: holt eine sinnvolle Fehlermeldung aus der Antwort."""
    try:
        data = response.json()
        if isinstance(data, dict) and "detail" in data:
            return str(data["detail"])
        return str(data)
    except Exception:
        return response.text or f"HTTP {response.status_code}"
