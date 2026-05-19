# GitHub-Setup

Da ich keinen direkten Netzwerkzugriff habe, übernimmst du den Push selbst. Hier ist der **komplette Ablauf**.

## 1. Repo auf GitHub anlegen

1. Auf https://github.com/new gehen
2. Repository-Name: `corporate-llm-platform`
3. **Privat** wählen (wegen API-Keys)
4. **WICHTIG:** NICHT "Initialize with README" anhaken — wir haben schon eins
5. "Create repository" klicken

## 2. Lokal in Git initialisieren

Nachdem du das Projekt heruntergeladen und entpackt hast:

```bash
cd corporate-llm-platform

# Git initialisieren
git init
git branch -M main

# Identität setzen (einmalig, falls noch nie gemacht)
git config user.name "Dein Name"
git config user.email "deine@email.com"

# Erste Commit
git add .
git commit -m "Phase 0 + 1: Setup, FastAPI-Gateway, Token-Logging"

# Mit GitHub-Repo verbinden (URL anpassen)
git remote add origin https://github.com/DEIN-USER/corporate-llm-platform.git

# Pushen
git push -u origin main
```

## 3. Authentifizierung

GitHub akzeptiert seit 2021 **kein Passwort** mehr beim Push. Du brauchst entweder:

### Variante A: Personal Access Token (einfach)
1. https://github.com/settings/tokens → "Generate new token (classic)"
2. Scope: `repo` (Vollzugriff auf deine Repos)
3. Token kopieren → als "Passwort" beim Push einfügen

### Variante B: SSH-Key (einmal Aufwand, dann komfortabel)
```bash
ssh-keygen -t ed25519 -C "deine@email.com"
cat ~/.ssh/id_ed25519.pub
# Inhalt kopieren → https://github.com/settings/keys → "New SSH key" → einfügen
```
Dann statt HTTPS die SSH-URL nutzen:
```bash
git remote set-url origin git@github.com:DEIN-USER/corporate-llm-platform.git
```

## 4. Verifikation

Nach `git push` sollte das Repo auf GitHub komplett sichtbar sein — **außer `.env`** (die ist via `.gitignore` ausgeschlossen, dein API-Key bleibt geheim).

## Folge-Commits

Nach Änderungen:
```bash
git add .
git commit -m "Phase 2: Streamlit-Frontend"
git push
```

## Troubleshooting

**"fatal: not a git repository"** → Du bist im falschen Ordner, mit `cd` korrigieren.

**"Permission denied (publickey)"** → SSH-Key wurde nicht hinterlegt, siehe Variante B.

**".env wurde mitgepusht!"** → Sofort handeln:
```bash
git rm --cached .env
git commit -m "Remove .env"
git push
```
Und **API-Key bei Anthropic rotieren!** (Console → API Keys → revoke)
