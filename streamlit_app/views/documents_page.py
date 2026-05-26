"""
Documents-Seite (Phase 3b).

Hier können Admins und Compliance-Officers:
- PDFs hochladen
- Sammlungen einsehen
- Dokumente löschen
"""

from typing import Any

import streamlit as st

from streamlit_app.api_client import APIClient, APIError


def render() -> None:
    st.title("📚 Wissensbibliothek")
    st.caption(
        "Lade PDFs hoch. Sie werden automatisch in Stücke zerlegt, "
        "embedded und stehen danach für RAG-Anfragen im Chat zur Verfügung."
    )

    user = st.session_state.get("user", {})
    role = user.get("role", "")

    if role not in ("admin", "compliance-officer"):
        st.warning(
            "🔒 Nur **Admin** und **Compliance-Officer** dürfen Dokumente "
            "hochladen oder löschen. Du kannst weiterhin Sammlungen im Chat nutzen."
        )

    client = APIClient(token=st.session_state.get("token"))

    tab_upload, tab_browse = st.tabs(["⬆️ Upload", "📂 Sammlungen"])

    with tab_upload:
        _render_upload(client, is_privileged=role in ("admin", "compliance-officer"))

    with tab_browse:
        _render_collections(client, role)


# ----------------------------------------------------------------------- #
# Upload
# ----------------------------------------------------------------------- #

def _render_upload(client: APIClient, is_privileged: bool) -> None:
    if not is_privileged:
        st.info("Upload nur für privilegierte Rollen.")
        return

    st.subheader("PDF hochladen")

    collection = st.text_input(
        "Sammlungs-Name",
        placeholder="z.B. pharma-fachinfos, hr-handbuch, tech-doku",
        help=(
            "Kleinbuchstaben, Ziffern, '-' oder '_'. 3–64 Zeichen. "
            "Wird automatisch angelegt, wenn nicht vorhanden."
        ),
    )

    uploaded_file = st.file_uploader(
        "PDF auswählen",
        type=["pdf"],
        help="Max. 200 MB. Gescannte PDFs ohne Text-Layer können nicht verarbeitet werden.",
    )

    if st.button("📤 Hochladen", type="primary", disabled=not (collection and uploaded_file)):
        with st.spinner(
            "Datei wird hochgeladen, gechunkt und embedded… "
            "(beim allerersten Upload dauert der Modell-Download 1-3 Min)"
        ):
            try:
                result = client.upload_document(
                    file_bytes=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    collection=collection.strip().lower(),
                )
            except APIError as exc:
                st.error(f"Upload fehlgeschlagen: {exc.detail}")
                return

        st.success(
            f"✅ Dokument hochgeladen: **{result['original_filename']}** "
            f"({result['page_count']} Seiten · {result['chunk_count']} Chunks)"
        )
        st.caption(f"Sammlung: `{result['collection']}`  ·  ID: {result['id']}")


# ----------------------------------------------------------------------- #
# Sammlungen + Dokumente
# ----------------------------------------------------------------------- #

def _render_collections(client: APIClient, role: str) -> None:
    st.subheader("Sammlungen")

    try:
        collections = client.list_collections()
    except APIError as exc:
        st.error(f"Sammlungen konnten nicht geladen werden: {exc.detail}")
        return

    if not collections:
        st.info("Noch keine Sammlungen vorhanden. Lade zuerst ein PDF hoch.")
        return

    # Übersicht als Cards
    for coll in collections:
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 1])
            cols[0].markdown(f"### 📁 `{coll['name']}`")
            cols[1].metric("Dokumente", coll["document_count"])
            cols[2].metric("Chunks", coll["chunk_count"])
            cols[3].metric(
                "Größe",
                f"{coll['total_size_bytes'] / (1024 * 1024):.1f} MB",
            )

            with st.expander("Dokumente anzeigen"):
                _render_documents_in_collection(client, coll["name"], role)


def _render_documents_in_collection(
    client: APIClient, collection: str, role: str
) -> None:
    try:
        docs = client.list_documents(collection=collection)
    except APIError as exc:
        st.error(f"Liste konnte nicht geladen werden: {exc.detail}")
        return

    if not docs:
        st.caption("Keine Dokumente in dieser Sammlung.")
        return

    can_delete = role in ("admin", "compliance-officer")

    for doc in docs:
        cols = st.columns([4, 2, 2, 1])
        cols[0].markdown(f"**{doc['original_filename']}**")
        cols[1].caption(
            f"{doc['page_count']} Seiten · {doc['chunk_count']} Chunks"
        )
        cols[2].caption(f"von {doc['uploaded_by']}")
        if can_delete:
            if cols[3].button("🗑", key=f"del-{doc['id']}", help="Löschen"):
                _delete_with_confirmation(client, doc)


def _delete_with_confirmation(client: APIClient, doc: dict[str, Any]) -> None:
    try:
        client.delete_document(doc["id"])
        st.success(f"🗑 Gelöscht: {doc['original_filename']}")
        st.rerun()
    except APIError as exc:
        st.error(f"Löschen fehlgeschlagen: {exc.detail}")
