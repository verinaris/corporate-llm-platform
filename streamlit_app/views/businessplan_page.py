"""
📊 Businessplan — Streamlit-Page.

UI-Workflow:
1. Vorlage wählen (KMU Standard / Verinaris-Beispiel / ...)
2. Daten eingeben/bearbeiten (mit Vorbelegung aus Vorlage)
3. Live-Vorschau: Finanzmodell, Härtungs-Checks, Fördermittel, Score
4. Speichern in der DB
5. Word/Excel/PDF exportieren

Nutzt unsere bestehende Plattform-Architektur:
- Auth via Session-State (JWT)
- LLM-Auswahl via dynamisches Modell-Dropdown
- Optional: lokales Modell für 100% Datenschutz
"""

import streamlit as st

from streamlit_app.api_client import APIClient, APIError
from streamlit_app.config import format_eur


def render() -> None:
    st.title("📊 Businessplan-Generator")
    st.caption(
        "Bankentauglicher Businessplan in wenigen Minuten — "
        "branchenübergreifend, mit Härtungs-Checks und Fördermittel-Matching."
    )

    token = st.session_state.get("token")
    client = APIClient(token=token)

    _ensure_state(client)

    tab_editor, tab_saved = st.tabs(["✏️ Neuer / Bearbeiten", "💾 Gespeicherte Pläne"])

    with tab_editor:
        _render_editor(client)

    with tab_saved:
        _render_saved_plans(client)


# ----------------------------------------------------------------------- #
# State-Management
# ----------------------------------------------------------------------- #

def _ensure_state(client: APIClient) -> None:
    """Initialisiert Session-State, holt Default-Werte beim ersten Aufruf."""
    if "bp_input" not in st.session_state:
        try:
            default = client.get_bp_template_default("kmu_default")
        except APIError:
            default = {}
        st.session_state["bp_input"] = default
        st.session_state["bp_current_template"] = "kmu_default"
        st.session_state["bp_loaded_id"] = None  # ID, falls bestehender Plan geladen


def _reload_template(client: APIClient, template_id: str) -> None:
    try:
        default = client.get_bp_template_default(template_id)
        st.session_state["bp_input"] = default
        st.session_state["bp_current_template"] = template_id
        st.session_state["bp_loaded_id"] = None
        st.session_state.pop("bp_result", None)
    except APIError as exc:
        st.error(f"Vorlage konnte nicht geladen werden: {exc.detail}")


# ----------------------------------------------------------------------- #
# Editor-Tab
# ----------------------------------------------------------------------- #

def _render_editor(client: APIClient) -> None:
    # --- Vorlage wählen ---
    st.subheader("1. Vorlage")
    try:
        templates = client.list_bp_templates()
    except APIError as exc:
        st.error(f"Vorlagen konnten nicht geladen werden: {exc.detail}")
        return

    options = {t["id"]: t for t in templates}
    labels = [f"{t['name']}  ({t['industry']})" for t in templates]
    ids = [t["id"] for t in templates]
    current_id = st.session_state.get("bp_current_template", "kmu_default")
    current_idx = ids.index(current_id) if current_id in ids else 0

    col_a, col_b = st.columns([3, 1])
    with col_a:
        chosen_label = st.selectbox(
            "Branchen-Vorlage",
            labels,
            index=current_idx,
            help="Vorlage wechseln befüllt das Formular mit Beispieldaten.",
        )
        chosen_id = ids[labels.index(chosen_label)]
    with col_b:
        st.write("")  # Spacer
        if st.button("🔄 Vorlage laden", use_container_width=True):
            _reload_template(client, chosen_id)
            st.rerun()

    info = options.get(chosen_id, {})
    if info.get("description"):
        st.caption(f"_{info['description']}_")

    bp = st.session_state["bp_input"]

    # --- Eingabe-Formular ---
    st.subheader("2. Daten")
    col1, col2 = st.columns(2)

    with col1:
        bp["startup_name"] = st.text_input(
            "Unternehmen", bp.get("startup_name", ""), max_chars=200
        )
        bp["legal_form"] = st.text_input("Rechtsform", bp.get("legal_form", ""))
        bp["founder_name"] = st.text_input("Gründer", bp.get("founder_name", ""))
        bp["location"] = st.text_input("Standort", bp.get("location", ""))
        bp["region"] = st.selectbox(
            "Bundesland (für Fördermittel)",
            ["DE", "RP", "BY", "BW", "NRW", "HE", "NI", "SN", "BE", "HH", "BR"],
            index=_safe_index(
                ["DE", "RP", "BY", "BW", "NRW", "HE", "NI", "SN", "BE", "HH", "BR"],
                bp.get("region", "DE"),
            ),
            help="RP = Rheinland-Pfalz aktiviert ISB-Förderung etc.",
        )
        bp["mission"] = st.text_area("Mission", bp.get("mission", ""), height=80)
        bp["problem"] = st.text_area("Problem", bp.get("problem", ""), height=100)
        bp["solution"] = st.text_area("Lösung", bp.get("solution", ""), height=100)
        bp["usp"] = st.text_area("USP", bp.get("usp", ""), height=80)

    with col2:
        bp["target_customers"] = st.text_area(
            "Zielkunden", bp.get("target_customers", ""), height=100
        )
        bp["revenue_model"] = st.text_area(
            "Umsatzmodell", bp.get("revenue_model", ""), height=80
        )
        bp["sales_channels"] = st.text_area(
            "Vertriebskanäle", bp.get("sales_channels", ""), height=100
        )
        bp["compliance_status"] = st.text_area(
            "Compliance-Status", bp.get("compliance_status", ""), height=80
        )
        bp["risks"] = st.text_area("Risiken", bp.get("risks", ""), height=100)

    # --- Finanzen ---
    st.subheader("3. Finanzannahmen")
    c1, c2, c3 = st.columns(3)
    with c1:
        bp["pricing_basic"] = st.number_input(
            "Basic €/Monat", value=float(bp.get("pricing_basic", 99)),
            min_value=0.0, step=50.0,
        )
        bp["expected_customers_year1"] = st.number_input(
            "Kunden Jahr 1", value=int(bp.get("expected_customers_year1", 10)),
            min_value=0, step=1,
        )
        bp["founder_equity"] = st.number_input(
            "Eigenkapital €", value=float(bp.get("founder_equity", 15000)),
            min_value=0.0, step=1000.0,
        )
    with c2:
        bp["pricing_pro"] = st.number_input(
            "Professional €/Monat", value=float(bp.get("pricing_pro", 299)),
            min_value=0.0, step=50.0,
        )
        bp["expected_customers_year2"] = st.number_input(
            "Kunden Jahr 2", value=int(bp.get("expected_customers_year2", 25)),
            min_value=0, step=1,
        )
        bp["required_capital"] = st.number_input(
            "Kapitalbedarf €", value=float(bp.get("required_capital", 50000)),
            min_value=0.0, step=5000.0,
        )
    with c3:
        bp["pricing_enterprise"] = st.number_input(
            "Enterprise €/Monat", value=float(bp.get("pricing_enterprise", 999)),
            min_value=0.0, step=50.0,
        )
        bp["expected_customers_year3"] = st.number_input(
            "Kunden Jahr 3", value=int(bp.get("expected_customers_year3", 60)),
            min_value=0, step=1,
        )
        bp["average_monthly_revenue_per_customer"] = st.number_input(
            "Ø Umsatz/Kunde/Monat €",
            value=float(bp.get("average_monthly_revenue_per_customer", 400)),
            min_value=0.0, step=50.0,
        )

    c4, c5, c6 = st.columns(3)
    with c4:
        bp["setup_fee_average"] = st.number_input(
            "Ø Setup-Fee €", value=float(bp.get("setup_fee_average", 1500)),
            min_value=0.0, step=250.0,
        )
    with c5:
        bp["monthly_fixed_costs"] = st.number_input(
            "Monatliche Fixkosten €",
            value=float(bp.get("monthly_fixed_costs", 3500)),
            min_value=0.0, step=250.0,
        )
    with c6:
        bp["marketing_budget_year1"] = st.number_input(
            "Marketing Jahr 1 €",
            value=float(bp.get("marketing_budget_year1", 10000)),
            min_value=0.0, step=1000.0,
        )

    bp["development_budget_year1"] = st.number_input(
        "Entwicklung Jahr 1 €",
        value=float(bp.get("development_budget_year1", 20000)),
        min_value=0.0, step=1000.0,
    )

    # Sicherstellen, dass template_id korrekt gesetzt ist
    bp["template_id"] = chosen_id

    # --- LLM für Summary ---
    st.subheader("4. LLM für Executive Summary")
    selected_model_id = st.session_state.get("selected_model_id")
    use_llm = st.toggle(
        "LLM-generierte Summary nutzen",
        value=bool(selected_model_id),
        help=(
            "Wenn aktiv: Verwendet das in der Sidebar gewählte Modell. "
            "Sonst: regelbasierter Fallback-Text. "
            "Tipp: Für sensible Daten lokales Modell wählen."
        ),
    )
    llm_model = selected_model_id if use_llm else None
    if use_llm and llm_model:
        st.caption(f"🤖 Aktives Modell: `{llm_model}`")

    # --- Aktionen ---
    st.subheader("5. Berechnen & Anzeigen")
    if st.button("🔢 Berechnen / Vorschau", type="primary"):
        with st.spinner("Berechne Plan…"):
            try:
                result = client.generate_businessplan(bp, llm_model=llm_model)
                st.session_state["bp_result"] = result
            except APIError as exc:
                st.error(f"Fehler: {exc.detail}")
                return

    # --- Ergebnis-Anzeige ---
    result = st.session_state.get("bp_result")
    if result:
        _render_result(result)

        st.divider()
        _render_save_and_export(client, bp, result, llm_model)


# ----------------------------------------------------------------------- #
# Ergebnis-Anzeige
# ----------------------------------------------------------------------- #

def _render_result(result: dict) -> None:
    st.subheader("📈 Ergebnis-Vorschau")

    # Score-Cards
    scores = result["scores"]
    s_cols = st.columns(4)
    s_cols[0].metric("Reifegrad", f"{scores['business_plan_maturity']}/100")
    s_cols[1].metric("Bankenfähig", f"{scores['bankability']}/100")
    s_cols[2].metric("Förderfähig", f"{scores['fundability']}/100")
    s_cols[3].metric("Investorenfähig", f"{scores['investability']}/100")

    # Executive Summary
    st.markdown("#### Executive Summary")
    st.write(result["summary"])
    if result.get("llm_used"):
        st.caption(f"🤖 Erzeugt mit: `{result['llm_used']}`")

    # Finanzmodell
    st.markdown("#### Finanzmodell (3 Jahre)")
    fin_rows = []
    for f in result["financials"]:
        fin_rows.append({
            "Jahr": f["year"],
            "Kunden": f["customers"],
            "Umsatz": f"{f['total_revenue']:,.0f} €".replace(",", "."),
            "Kosten": f"{f['total_costs']:,.0f} €".replace(",", "."),
            "Ergebnis v. St.": f"{f['profit_before_tax']:,.0f} €".replace(",", "."),
        })
    st.dataframe(fin_rows, use_container_width=True, hide_index=True)

    # Härtungs-Checks
    st.markdown("#### Härtungs-Checks")
    chk_rows = []
    for c in result["checks"]:
        icon = "✅" if c["status"] == "OK" else "🟡" if c["status"] == "Nachschärfen" else "🔴"
        chk_rows.append({
            "Bereich": c["area"],
            "Status": f"{icon} {c['status']}",
            "Befund": c["finding"],
            "Empfehlung": c["recommendation"],
        })
    st.dataframe(chk_rows, use_container_width=True, hide_index=True)

    # Fördermittel
    st.markdown("#### Fördermittel-Kandidaten")
    fund_rows = []
    for fm in result["funding"]:
        fund_rows.append({
            "Programm": fm["name"],
            "Passung": fm["fit"],
            "Warum": fm["why"],
            "Region": fm.get("region", ""),
        })
    st.dataframe(fund_rows, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------- #
# Speichern & Export
# ----------------------------------------------------------------------- #

def _render_save_and_export(
    client: APIClient,
    bp: dict,
    result: dict,
    llm_model: str | None,
) -> None:
    st.subheader("💾 Speichern & 📤 Export")
    score = int(result["scores"]["business_plan_maturity"])
    loaded_id = st.session_state.get("bp_loaded_id")

    cols = st.columns(4)

    with cols[0]:
        if loaded_id is None:
            if st.button("💾 Neu speichern", use_container_width=True):
                try:
                    new_id = client.save_businessplan(bp, last_score=score)
                    st.session_state["bp_loaded_id"] = new_id
                    st.success(f"Plan gespeichert (ID {new_id})")
                except APIError as exc:
                    st.error(f"Speichern fehlgeschlagen: {exc.detail}")
        else:
            if st.button("💾 Aktualisieren", use_container_width=True):
                try:
                    client.update_businessplan(loaded_id, bp, last_score=score)
                    st.success(f"Plan #{loaded_id} aktualisiert.")
                except APIError as exc:
                    st.error(f"Update fehlgeschlagen: {exc.detail}")

    with cols[1]:
        if st.button("📄 Word", use_container_width=True):
            _download(client, "docx", bp, llm_model)

    with cols[2]:
        if st.button("📊 Excel", use_container_width=True):
            _download(client, "xlsx", bp, llm_model)

    with cols[3]:
        if st.button("📑 PDF", use_container_width=True):
            _download(client, "pdf", bp, llm_model)


def _download(
    client: APIClient,
    fmt: str,
    bp: dict,
    llm_model: str | None,
) -> None:
    try:
        with st.spinner(f"Erzeuge {fmt.upper()}…"):
            data, filename = client.export_businessplan(fmt, bp, llm_model=llm_model)
        st.session_state[f"bp_export_{fmt}"] = {"bytes": data, "filename": filename}
        st.success(f"✓ {filename} bereit")
    except APIError as exc:
        st.error(f"Export fehlgeschlagen: {exc.detail}")

    # Download-Button anzeigen falls vorhanden
    if f"bp_export_{fmt}" in st.session_state:
        info = st.session_state[f"bp_export_{fmt}"]
        st.download_button(
            f"⬇️ {fmt.upper()} herunterladen",
            data=info["bytes"],
            file_name=info["filename"],
            mime=_mime_for(fmt),
            key=f"dl-{fmt}",
        )


# ----------------------------------------------------------------------- #
# Gespeicherte Pläne
# ----------------------------------------------------------------------- #

def _render_saved_plans(client: APIClient) -> None:
    try:
        plans = client.list_businessplans()
    except APIError as exc:
        st.error(f"Pläne konnten nicht geladen werden: {exc.detail}")
        return

    if not plans:
        st.info("Noch keine gespeicherten Pläne. Erstelle einen im Tab '✏️ Neuer'.")
        return

    for p in plans:
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 1, 1])
            cols[0].markdown(f"**{p['name']}**  \n`{p['template_id']}`")
            cols[1].metric("Score", f"{p['last_score']}/100")
            cols[2].caption(p["updated_at"][:10])
            with cols[3]:
                if st.button("📂 Laden", key=f"load-bp-{p['id']}"):
                    _load_plan_to_editor(client, p["id"])
                    st.rerun()
            with cols[4]:
                if st.button("🗑", key=f"del-bp-{p['id']}", help="Löschen"):
                    try:
                        client.delete_businessplan(p["id"])
                        st.success(f"Plan {p['id']} gelöscht.")
                        st.rerun()
                    except APIError as exc:
                        st.error(f"Löschen fehlgeschlagen: {exc.detail}")


def _load_plan_to_editor(client: APIClient, plan_id: int) -> None:
    try:
        data = client.get_businessplan(plan_id)
        st.session_state["bp_input"] = data
        st.session_state["bp_current_template"] = data.get("template_id", "kmu_default")
        st.session_state["bp_loaded_id"] = plan_id
        st.session_state.pop("bp_result", None)
    except APIError as exc:
        st.error(f"Plan konnte nicht geladen werden: {exc.detail}")


# ----------------------------------------------------------------------- #
# Helpers
# ----------------------------------------------------------------------- #

def _safe_index(options: list, value) -> int:
    try:
        return options.index(value)
    except (ValueError, TypeError):
        return 0


def _mime_for(fmt: str) -> str:
    return {
        "docx": (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        "xlsx": (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        "pdf": "application/pdf",
    }.get(fmt, "application/octet-stream")
