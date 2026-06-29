# Phase 2a — Auth-Backend

**Ziel:** Login mit E-Mail + Passwort, JWT-basierte Sessions, Rollen, geschützte Endpoints.

## Was wurde gebaut?

### Neue Pakete & Dateien
```
app/auth/                       ← NEU
├── __init__.py
├── passwords.py                Passwort-Hashing (bcrypt)
├── jwt.py                      Token erstellen/verifizieren
└── dependencies.py             FastAPI-Dependencies (current_user)

app/api/auth.py                 ← NEU   /auth/login, /auth/me
app/api/users.py                ← NEU   /users CRUD (nur Admin)
app/schemas_auth.py             ← NEU   Auth-Schemas

tests/conftest.py               ← NEU   Test-Fixtures (admin, user, tokens)
tests/test_auth.py              ← NEU
tests/test_users.py             ← NEU
docs/phase-2a-auth.md           ← NEU   (diese Datei)
```

### Geänderte Dateien
```
app/models.py        + User-Tabelle, UserRole-Enum, UserBranch-Enum
app/config.py        + JWT-Secret, JWT-Expire, Bootstrap-Admin
app/main.py          + Bootstrap-Admin beim Start, neue Router
app/api/chat.py      + Login erforderlich, user_id aus Token
app/api/stats.py     + Login erforderlich, gefiltert für Non-Admin
app/schemas.py       - user_id aus ChatRequest entfernt
app/services/...     + user_filter in get_summary()
.env.example         + JWT-Secret, Bootstrap-Admin-Credentials
requirements.txt     + bcrypt, pyjwt, email-validator, python-multipart
```

## Rollen-Modell

Vier vordefinierte Rollen (Enum `UserRole`):

| Rolle | Beschreibung | Darf was? |
|-------|--------------|-----------|
| `admin` | System-Administrator | Alles, inkl. User-Verwaltung |
| `compliance-officer` | Beauftragte:r für Compliance (Phase 2c) | Alle Logs lesen, nichts schreiben |
| `pharma-referent` | Pharma-Außendienst | Chat mit Pharma-Plugin (Phase 2c) |
| `user` | Standard-User | Chat, eigene Stats |

Plus eine separate **Branchenzuordnung** (`UserBranch`): aktuell `generic` oder `pharma` (weitere kommen mit den Branchenmodulen).

> **Wichtig:** Rolle und Branche sind orthogonal. Ein Admin kann Branche `generic` haben, ein User kann Branche `pharma` haben.

## Ablauf eines geschützten Requests

```
1. Client: POST /auth/login mit E-Mail + Passwort
2. Server: bcrypt-Check → bei Erfolg: JWT erstellen + zurücksenden
3. Client: speichert Token, fügt ihn in jeden weiteren Request:
           Header: Authorization: Bearer <token>
4. Server: validiert Token, lädt User aus DB → an Endpoint übergeben
5. Endpoint: kann via `current_user` auf User-Daten zugreifen
```

**Analogie:** Bei der Einlasskontrolle bekommst du ein Eintrittsband (JWT).
Ab dann zeigst du es nur noch vor — keine erneute Personenkontrolle.
Nach 24h verfällt es (`JWT_EXPIRE_HOURS`).

## Bootstrap-Admin

Beim ersten App-Start wird ein Admin-User automatisch angelegt:
- E-Mail aus `BOOTSTRAP_ADMIN_EMAIL`
- Passwort aus `BOOTSTRAP_ADMIN_PASSWORD`

**Idempotent:** Wenn der User schon existiert, passiert nichts.

> **Sicherheitshinweis:** Passwort nach dem ersten Login in Produktion ändern!

## Testen in der Swagger-UI

1. `uvicorn app.main:app --reload` starten
2. Browser auf `http://localhost:8000/docs`
3. Oben rechts auf **"Authorize"** klicken
4. **username** = E-Mail, **password** = Passwort
5. **Authorize** klicken → Token wird in alle Requests gehängt
6. Jetzt funktioniert `/chat`, `/stats`, `/auth/me`

### Erster Test
1. Authorize mit deinem Bootstrap-Admin (z.B. `s_mkern@t-online.de` + Passwort aus `.env`)
2. `GET /auth/me` → du siehst dein Profil
3. `POST /chat` → wie gewohnt, aber jetzt ist `user_id` automatisch deine E-Mail

## API-Übersicht

| Methode | Pfad | Wer darf? | Was macht's |
|---------|------|-----------|-------------|
| POST | `/auth/login` | Jeder | Login → liefert Token |
| GET | `/auth/me` | Eingeloggt | Eigenes Profil |
| GET | `/users` | Admin | Alle User auflisten |
| POST | `/users` | Admin | Neuen User anlegen |
| GET | `/users/{id}` | Admin | Einzelnen User holen |
| PATCH | `/users/{id}` | Admin | Rolle/Branche/Aktiv ändern |
| DELETE | `/users/{id}` | Admin | User deaktivieren (soft) |
| POST | `/chat` | Eingeloggt | Chat mit LLM |
| GET | `/stats` | Eingeloggt | Stats (Admin: alle, sonst: eigene) |
| GET | `/health` | Jeder | Liveness-Check |

## Tests laufen lassen

```bash
pytest -v
```

Erwartet: alle Tests grün (Health, Branches, Auth, Users, Stats).

## Was Phase 2a NICHT bringt

Bewusst noch offen für Phase 2b/c:
- ❌ Hübsches Frontend (kommt mit Streamlit in 2b)
- ❌ Passwort-Reset per E-Mail
- ❌ 2-Faktor-Authentifizierung
- ❌ Pharma-Plugin lebendig (kommt in 2c)
- ❌ Rate-Limiting pro User
- ❌ Audit-Log für Login/Passwort-Änderungen

## Sicherheitshinweise

- **JWT_SECRET** in Produktion **MUSS** zufällig & lang sein. Generieren:
  ```bash
  openssl rand -hex 32
  ```
- Passwörter mindestens 8 Zeichen (in Phase 2b/c verschärfen wir das)
- Token-Ablauf: 24h. Für sensible Anwendungen ggf. kürzer (4h/8h)
- Bei Produktivbetrieb: HTTPS Pflicht — sonst lecken Tokens im Klartext
