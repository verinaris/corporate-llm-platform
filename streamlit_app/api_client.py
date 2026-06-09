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

    def list_available_models(self) -> dict[str, Any]:
        """Liefert die Provider/Modelle vom Backend (inkl. lokales Ollama)."""
        return self._get("/models/available", timeout=15)

    # ------------------------------------------------------------------ #
    # Profile (Branchen-Profil)
    # ------------------------------------------------------------------ #
    def list_industries(self) -> list[dict[str, Any]]:
        """Verfügbare Branchen-Profile."""
        return self._get("/profile/industries")  # type: ignore[return-value]

    def get_my_profile(self) -> dict[str, Any]:
        """Eigenes Profil mit aktiver Branche."""
        return self._get("/profile/me")

    def update_my_branch(self, branch: str) -> dict[str, Any]:
        """Wechselt das eigene Branchen-Profil."""
        try:
            r = httpx.put(
                f"{self.base_url}/profile/me/branch",
                headers=self._headers(),
                json={"branch": branch},
                timeout=10,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    # ------------------------------------------------------------------ #
    # Admin / Audit (Phase 6a)
    # ------------------------------------------------------------------ #
    def list_audit_log(
        self,
        user_email: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params = {"limit": str(limit)}
        if user_email:
            params["user_email"] = user_email
        if action:
            params["action"] = action
        try:
            r = httpx.get(
                f"{self.base_url}/admin/audit-log",
                headers=self._headers(),
                params=params, timeout=30,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def list_audit_actions(self) -> list[str]:
        return self._get("/admin/audit-log/actions")  # type: ignore[return-value]

    def dsgvo_full_delete(self, user_id: int) -> dict[str, Any]:
        try:
            r = httpx.delete(
                f"{self.base_url}/admin/users/{user_id}/dsgvo-delete",
                headers=self._headers(), timeout=30,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def dsgvo_export(self, user_id: int) -> dict[str, Any]:
        return self._get(f"/admin/users/{user_id}/dsgvo-export")

    # ------------------------------------------------------------------ #
    # Chat
    # ------------------------------------------------------------------ #
    def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        collection: Optional[str] = None,
        top_k: int = 4,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"messages": messages}
        if model:
            payload["model"] = model
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if collection:
            payload["collection"] = collection
            payload["top_k"] = top_k
        # 300s, weil lokale Modelle (Ollama) beim ersten Aufruf erst in den
        # RAM geladen werden müssen (kann je nach Modell 30-60s dauern)
        return self._post("/chat", payload, timeout=300)

    # ------------------------------------------------------------------ #
    # Documents (Phase 3a/b)
    # ------------------------------------------------------------------ #
    def list_collections(self) -> list[dict[str, Any]]:
        return self._get("/documents/collections")  # type: ignore[return-value]

    def get_collection(self, name: str) -> dict[str, Any]:
        return self._get(f"/documents/collections/{name}")

    def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Sammlung mit Beschreibung anlegen (Phase 3c)."""
        data: dict[str, Any] = {"name": name}
        if description:
            data["description"] = description
        if tags:
            data["tags"] = ",".join(tags)
        try:
            r = httpx.post(
                f"{self.base_url}/documents/collections",
                headers=self._headers(),
                data=data,
                timeout=15,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code not in (200, 201):
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def update_collection(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if description is not None:
            payload["description"] = description
        if tags is not None:
            payload["tags"] = tags
        try:
            r = httpx.put(
                f"{self.base_url}/documents/collections/{name}",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code != 200:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def list_documents(self, collection: Optional[str] = None) -> list[dict[str, Any]]:
        path = "/documents"
        if collection:
            path += f"?collection={collection}"
        return self._get(path)  # type: ignore[return-value]

    def upload_document(
        self, file_bytes: bytes, filename: str, collection: str,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """PDF hochladen (klassisch, ohne Phasen-Status)."""
        data: dict[str, Any] = {"collection": collection}
        if description:
            data["description"] = description
        try:
            r = httpx.post(
                f"{self.base_url}/documents",
                headers=self._headers(),
                files={"file": (filename, file_bytes, "application/pdf")},
                data=data,
                timeout=600,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code not in (200, 201):
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def upload_document_stream(
        self, file_bytes: bytes, filename: str, collection: str,
        description: Optional[str] = None,
    ):
        """
        PDF hochladen mit NDJSON-Phasen-Status (Phase 3c).

        Liefert einen Generator über JSON-Events. Jedes Event ist ein dict
        mit Feldern 'phase' und 'status', plus phase-spezifische Daten.
        """
        import json as _json

        data: dict[str, Any] = {"collection": collection}
        if description:
            data["description"] = description

        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/documents/stream",
                headers=self._headers(),
                files={"file": (filename, file_bytes, "application/pdf")},
                data=data,
                timeout=600,
            ) as r:
                if r.status_code >= 400:
                    # Bei sofortigen Fehlern (400/413 etc.) sammeln wir den Body
                    body = b"".join(r.iter_bytes())
                    try:
                        err = _json.loads(body.decode("utf-8"))
                        detail = err.get("detail", body.decode("utf-8"))
                    except Exception:
                        detail = body.decode("utf-8", errors="replace")
                    raise APIError(r.status_code, detail)

                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        yield _json.loads(line)
                    except _json.JSONDecodeError:
                        continue
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e

    def get_document_file(self, document_id: int) -> tuple[bytes, str]:
        """Lädt die Original-PDF eines Dokuments. Liefert (bytes, filename)."""
        try:
            r = httpx.get(
                f"{self.base_url}/documents/{document_id}/file",
                headers=self._headers(),
                timeout=120,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code != 200:
            raise APIError(r.status_code, _extract_detail(r))
        # Filename aus Content-Disposition extrahieren
        cd = r.headers.get("content-disposition", "")
        filename = "dokument.pdf"
        if "filename=" in cd:
            filename = cd.split("filename=", 1)[1].strip('"').strip("'")
        return r.content, filename

    def delete_document(self, document_id: int) -> dict[str, Any]:
        try:
            r = httpx.delete(
                f"{self.base_url}/documents/{document_id}",
                headers=self._headers(),
                timeout=30,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code != 200:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    # ------------------------------------------------------------------ #
    # Stats
    # ------------------------------------------------------------------ #
    def stats(self) -> dict[str, Any]:
        return self._get("/stats")

    # ------------------------------------------------------------------ #
    # Businessplan (Phase 5+)
    # ------------------------------------------------------------------ #
    def list_bp_templates(self) -> list[dict[str, Any]]:
        return self._get("/businessplan/templates")  # type: ignore[return-value]

    def get_bp_template_default(self, template_id: str) -> dict[str, Any]:
        return self._get(f"/businessplan/templates/{template_id}/default")

    def generate_businessplan(
        self,
        input_payload: dict[str, Any],
        llm_model: Optional[str] = None,
    ) -> dict[str, Any]:
        """Berechnet einen Plan ohne ihn zu speichern (Live-Vorschau)."""
        url = f"{self.base_url}/businessplan/generate"
        if llm_model:
            url += f"?llm_model={llm_model}"
        try:
            r = httpx.post(
                url, headers=self._headers(),
                json=input_payload, timeout=300,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        return r.json()

    def save_businessplan(
        self,
        input_payload: dict[str, Any],
        last_score: int = 0,
    ) -> int:
        try:
            r = httpx.post(
                f"{self.base_url}/businessplan?last_score={last_score}",
                headers=self._headers(),
                json=input_payload,
                timeout=30,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        return int(r.json())

    def list_businessplans(self) -> list[dict[str, Any]]:
        return self._get("/businessplan")  # type: ignore[return-value]

    def get_businessplan(self, plan_id: int) -> dict[str, Any]:
        return self._get(f"/businessplan/{plan_id}")

    def update_businessplan(
        self,
        plan_id: int,
        input_payload: dict[str, Any],
        last_score: int = 0,
    ) -> int:
        try:
            r = httpx.put(
                f"{self.base_url}/businessplan/{plan_id}?last_score={last_score}",
                headers=self._headers(),
                json=input_payload,
                timeout=30,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        return int(r.json())

    def delete_businessplan(self, plan_id: int) -> None:
        try:
            r = httpx.delete(
                f"{self.base_url}/businessplan/{plan_id}",
                headers=self._headers(),
                timeout=10,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))

    def export_businessplan(
        self,
        fmt: str,
        input_payload: dict[str, Any],
        llm_model: Optional[str] = None,
    ) -> tuple[bytes, str]:
        """Generiert Plan + liefert direkt das File. (bytes, filename)"""
        url = f"{self.base_url}/businessplan/export/{fmt}"
        if llm_model:
            url += f"?llm_model={llm_model}"
        try:
            r = httpx.post(
                url, headers=self._headers(),
                json=input_payload, timeout=300,
            )
        except httpx.RequestError as e:
            raise APIError(0, f"Backend nicht erreichbar: {e}") from e
        if r.status_code >= 400:
            raise APIError(r.status_code, _extract_detail(r))
        cd = r.headers.get("content-disposition", "")
        filename = f"businessplan.{fmt}"
        if "filename=" in cd:
            filename = cd.split("filename=", 1)[1].strip('"').strip("'")
        return r.content, filename

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
