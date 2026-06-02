"""
Documents-Seite (Phase 3a–3c).

Admin/Compliance-Officer:
- PDFs hochladen (mit Phasen-Status-Anzeige in Echtzeit)
- Sammlungen anlegen mit Beschreibung + Tags
- Dokumente löschen
- Beschreibung nachträglich bearbeiten

Alle anderen User:
- Sammlungen einsehen
- Dokumenten-Liste durchstöbern
"""

import re
from typing import Any

import streamlit as st

from streamlit_app.api_client import APIClient, APIError


# ChromaDB-Limit: 3-63 Zeichen, lowercase, nur Buchstaben/Ziffern/-/_
COLLECTION_NAME_MAX = 63
COLLECTION_NAME_MIN = 3


def normalize_collection_name(raw: str) -> str:
    """
    Macht aus beliebigem User-Input einen ChromaDB-konformen Sammlungs-Namen.

    Beispiele:
      "Modernes Anforderungsmanagement 2024"
        → "modernes-anforderungsmanagement-2024"
      "Mein, Sammlung; mit !!! Sonderzeichen"
        → "mein-sammlung-mit-sonderzeichen"
      "ABC_DEF-123"
        → "abc_def-123"
    """
    if not raw:
        return ""
    name = raw.strip().lower()
    # Alles, was nicht a-z, 0-9, _, - ist → durch - ersetzen
    name = re.sub(r"[^a-z0-9_\-]+", "-", name)
    # Mehrfach-Bindestriche → einer
    name = re.sub(r"-+", "-", name)
    # Trailing/leading -/_ entfernen (ChromaDB verlangt alphanumeric an Rändern)
    name = name.strip("-_")
    # Auf 63 Zeichen kürzen
    name = name[:COLLECTION_NAME_MAX]
    # Falls nach Kürzen ein - am Ende übrig → nochmal cleanup
    name = name.rstrip("-_")
    return name


def render() -> None:
    st.title("📚 Wissensbibliothek")
    st.caption(
        "Lade PDFs hoch. Sie werden in Stücke zerlegt, embedded "
        "und stehen danach für RAG-Anfragen im Chat zur Verfügung."
    )

    user = st.session_state.get("user", {})
    role = user.get("role", "")
    is_privileged = role in ("admin", "compliance-officer")

    if not is_privileged:
        st.warning(
            "🔒 Nur **Admin** und **Compliance-Officer** dürfen Dokumente "
            "hochladen oder löschen. Du kannst weiterhin Sammlungen im Chat nutzen."
        )

    client = APIClient(token=st.session_state.get("token"))

    tab_upload, tab_browse = st.tabs(["⬆️ Upload", "📂 Sammlungen"])

    with tab_upload:
        _render_upload(client, is_privileged)

    with tab_browse:
        _render_collections(client, role)


# ----------------------------------------------------------------------- #
# Upload mit Phasen-Status (Phase 3c)
# ----------------------------------------------------------------------- #

def _render_upload(client: APIClient, is_privileged: bool) -> None:
    if not is_privileged:
        st.info("Upload nur für privilegierte Rollen.")
        return

    st.subheader("PDF hochladen")

    try:
        existing_collections = client.list_collections()
    except APIError:
        existing_collections = []

    collection_names = [c["name"] for c in existing_collections]

    col1, col2 = st.columns([2, 3])
    with col1:
        mode = st.radio(
            "Sammlungs-Wahl",
            ["Existierende Sammlung", "Neue Sammlung"],
            horizontal=False,
        )

    description_for_upload: str | None = None
    raw_collection_input = ""
    collection_normalized = ""

    with col2:
        if mode == "Existierende Sammlung" and collection_names:
            collection_normalized = st.selectbox(
                "Sammlung auswählen",
                collection_names,
            )
        else:
            raw_collection_input = st.text_input(
                "Sammlungs-Name (technischer Container-Name)",
                placeholder="z.B. 'Pharma Fachinfos 2024' oder 'requirements-engineering'",
                help=(
                    f"Wird automatisch in ChromaDB-konformen Namen umgewandelt "
                    f"(max. {COLLECTION_NAME_MAX} Zeichen, lowercase, nur -/_)."
                    f" Lange Bezeichnungen passen in die Beschreibung."
                ),
            )
            collection_normalized = normalize_collection_name(raw_collection_input)

            # Live-Vorschau
            if raw_collection_input and collection_normalized:
                if raw_collection_input.strip().lower() == collection_normalized:
                    st.caption(f"✅ Wird gespeichert als: `{collection_normalized}`")
                else:
                    st.caption(
                        f"ℹ️  Wird automatisch umgewandelt zu: "
                        f"`{collection_normalized}` ({len(collection_normalized)} Zeichen)"
                    )
            elif raw_collection_input and not collection_normalized:
                st.warning(
                    "⚠️  Aus dieser Eingabe lässt sich kein gültiger Sammlungs-Name bilden. "
                    "Bitte mindestens 1 Buchstabe oder Ziffer verwenden."
                )

            description_for_upload = st.text_area(
                "Beschreibung der Sammlung (optional, beliebig lang)",
                placeholder=(
                    "Wofür ist diese Sammlung gedacht? "
                    "Hier kannst du den vollen, langen Titel reinschreiben "
                    "(z.B. 'Moderner Anforderungsmanagement Gesamtskript Q4/2024')."
                ),
                max_chars=2000,
                height=100,
            )

    uploaded_file = st.file_uploader(
        "PDF auswählen",
        type=["pdf"],
        help="Max. 200 MB. Gescannte PDFs ohne Text-Layer können nicht verarbeitet werden.",
    )

    # Hilfreicher Hinweis: Dateinamen-Vorschlag, wenn neue Sammlung + Datei da
    if (
        mode == "Neue Sammlung"
        and uploaded_file is not None
        and not raw_collection_input
    ):
        suggestion = normalize_collection_name(uploaded_file.name.rsplit(".", 1)[0])
        if suggestion and len(suggestion) >= COLLECTION_NAME_MIN:
            st.info(
                f"💡 Vorschlag basierend auf Dateinamen: `{suggestion}`  \n"
                "Du kannst diesen Namen oben ins Feld kopieren oder einen eigenen wählen."
            )

    # Upload-Voraussetzungen
    name_ok = (
        collection_normalized
        and len(collection_normalized) >= COLLECTION_NAME_MIN
    )
    can_upload = bool(name_ok) and uploaded_file is not None

    if st.button("📤 Hochladen", type="primary", disabled=not can_upload):
        _do_upload_with_phases(
            client=client,
            file_bytes=uploaded_file.getvalue(),
            filename=uploaded_file.name,
            collection=collection_normalized,
            description=description_for_upload,
        )


def _do_upload_with_phases(
    client: APIClient,
    file_bytes: bytes,
    filename: str,
    collection: str,
    description: str | None,
) -> None:
    """Führt den Streaming-Upload aus und zeigt Live-Phasen-Status."""

    PHASE_LABELS = {
        "upload": "1️⃣  Datei wird empfangen",
        "read_pdf": "2️⃣  PDF wird gelesen",
        "chunk": "3️⃣  Chunks werden erstellt",
        "embed": "4️⃣  Embeddings werden generiert",
        "complete": "5️⃣  Indexierung abgeschlossen",
    }

    final_doc: dict | None = None
    duplicate_info: dict | None = None
    had_error = False

    with st.status("Verarbeite Upload…", expanded=True) as status_box:
        try:
            for event in client.upload_document_stream(
                file_bytes=file_bytes,
                filename=filename,
                collection=collection,
                description=description,
            ):
                phase = event.get("phase", "")
                ev_status = event.get("status", "")

                if phase == "duplicate":
                    existing = event.get("existing", {})
                    status_box.update(
                        label="⚠️ Datei bereits vorhanden",
                        state="error",
                    )
                    duplicate_info = existing
                    had_error = True
                    break

                if phase == "error":
                    status_box.update(
                        label=f"❌ Fehler: {event.get('detail', 'Unbekannter Fehler')}",
                        state="error",
                    )
                    st.error(event.get("detail", "Unbekannter Fehler"))
                    had_error = True
                    break

                label_base = PHASE_LABELS.get(phase, phase)

                if phase == "upload" and ev_status == "done":
                    st.write(f"✅ {label_base} — {event.get('msg', '')}")

                elif phase == "read_pdf":
                    if ev_status == "start":
                        st.write(f"⏳ {label_base}…")
                    elif ev_status == "done":
                        pages = event.get("pages", "?")
                        ms = event.get("elapsed_ms", 0)
                        st.write(f"✅ {label_base} — {pages} Seiten ({ms} ms)")

                elif phase == "chunk" and ev_status == "done":
                    chunks = event.get("chunks", "?")
                    st.write(f"✅ {label_base} — {chunks} Stück")

                elif phase == "embed":
                    if ev_status == "start":
                        st.write(f"⏳ {label_base} — {event.get('msg', '')}")
                    elif ev_status == "done":
                        ms = event.get("elapsed_ms", 0)
                        st.write(f"✅ {label_base} — fertig ({ms} ms)")

                elif phase == "complete" and ev_status == "done":
                    final_doc = event.get("document")
                    status_box.update(
                        label="✅ Upload erfolgreich",
                        state="complete",
                    )

        except APIError as exc:
            status_box.update(
                label=f"❌ Upload fehlgeschlagen: {exc.detail}",
                state="error",
            )
            st.error(f"Upload fehlgeschlagen: {exc.detail}")
            return

    if duplicate_info:
        uploaded_iso = duplicate_info.get("uploaded_at", "")
        # ISO → deutsches Format
        uploaded_pretty = uploaded_iso
        try:
            from datetime import datetime as _dt
            uploaded_pretty = _dt.fromisoformat(
                uploaded_iso.replace("Z", "+00:00")
            ).strftime("%d.%m.%Y um %H:%M Uhr")
        except Exception:
            pass

        st.warning(
            f"⚠️ **Diese Datei wurde bereits in die Sammlung "
            f"`{duplicate_info.get('collection', collection)}` hochgeladen.**\n\n"
            f"- **Dateiname (gespeichert):** {duplicate_info.get('filename', '?')}\n"
            f"- **Hochgeladen am:** {uploaded_pretty}\n"
            f"- **Von:** {duplicate_info.get('uploaded_by', '?')}\n\n"
            f"Tipp: Wähle eine andere Sammlung oder lösche die bestehende "
            f"Datei zuerst (Tab → 📂 Sammlungen)."
        )
        return

    if final_doc and not had_error:
        st.success(
            f"📄 **{final_doc['original_filename']}** wurde indexiert "
            f"({final_doc['page_count']} Seiten · {final_doc['chunk_count']} Chunks)"
        )
        st.caption(f"Sammlung: `{final_doc['collection']}`  ·  Dokument-ID: {final_doc['id']}")
        st.session_state.pop("_collections_cache", None)


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

    is_privileged = role in ("admin", "compliance-officer")

    for coll in collections:
        with st.container(border=True):
            top = st.columns([3, 1, 1, 1])
            top[0].markdown(f"### 📁 `{coll['name']}`")
            top[1].metric("Dokumente", coll["document_count"])
            top[2].metric("Chunks", coll["chunk_count"])
            top[3].metric(
                "Größe",
                f"{coll['total_size_bytes'] / (1024 * 1024):.1f} MB",
            )

            description = coll.get("description")
            tags = coll.get("tags") or []

            if description:
                st.markdown(f"_{description}_")
            if tags:
                st.markdown(" ".join(f"`#{t}`" for t in tags))

            if is_privileged:
                with st.expander("✏️ Beschreibung & Tags bearbeiten"):
                    _render_collection_editor(client, coll)

            with st.expander("Dokumente anzeigen"):
                _render_documents_in_collection(client, coll["name"], role)


def _render_collection_editor(client: APIClient, coll: dict[str, Any]) -> None:
    """Inline-Editor für Beschreibung + Tags einer Sammlung."""
    name = coll["name"]
    current_desc = coll.get("description") or ""
    current_tags = ", ".join(coll.get("tags") or [])

    new_desc = st.text_area(
        "Beschreibung",
        value=current_desc,
        max_chars=2000,
        height=80,
        key=f"desc-{name}",
    )
    new_tags = st.text_input(
        "Tags (komma-getrennt)",
        value=current_tags,
        key=f"tags-{name}",
        help="Beispiel: pharma, fachinfo, vertraulich",
    )

    if st.button("💾 Speichern", key=f"save-{name}"):
        tag_list = [t.strip() for t in new_tags.split(",") if t.strip()]
        try:
            client.update_collection(name, description=new_desc, tags=tag_list)
            st.success("Gespeichert.")
            st.session_state.pop("_collections_cache", None)
            st.rerun()
        except APIError as exc:
            st.error(f"Speichern fehlgeschlagen: {exc.detail}")


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
                _delete_document(client, doc)


def _delete_document(client: APIClient, doc: dict[str, Any]) -> None:
    try:
        client.delete_document(doc["id"])
        st.success(f"🗑 Gelöscht: {doc['original_filename']}")
        st.session_state.pop("_collections_cache", None)
        st.rerun()
    except APIError as exc:
        st.error(f"Löschen fehlgeschlagen: {exc.detail}")
