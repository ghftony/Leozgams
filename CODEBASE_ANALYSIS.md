# Codebase Analysis — Leozgams / gohifun

## Overview

This is a Django 5.2 web application serving browser-based games, deployed at
`https://parkour.lovesupplychain.com`. The project is called **gohifun** and
currently hosts two games: **Parkour** and **Fishing**.

---

## Repository Structure

```
Leozgams/
├── core/                   # Django app (views, URLs, models)
│   ├── views.py
│   ├── urls.py
│   ├── models.py           # empty (no DB models)
│   ├── admin.py
│   └── migrations/
├── portal/                 # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── templates/
│   ├── base.html           # shared layout with header + game launcher
│   └── core/
│       ├── parkour.html    # parkour game (canvas, ~1008 lines)
│       ├── fishing.html    # fishing game (standalone, ~3467 lines)
│       └── fishing_portal.html  # iframe wrapper for fishing game
├── static/                 # frontend assets (CSS/JS bundles, Metronic UI)
├── manage.py
├── requirements.txt
└── deploy.sh               # VPS deployment script
```

---

## Backend

### Framework & Dependencies
- **Django 5.2.11** — primary framework
- **psycopg2-binary 2.9.11** — PostgreSQL adapter
- **Database**: PostgreSQL (`gohifun` db, localhost:5432, user `postgres`)
- No ORM models are defined; the app is purely view-based

### URL Routing
| URL | View | Name |
|-----|------|------|
| `/` | `home` — redirects to `/parkour/` | `home` |
| `/parkour/` | `parkour_game` | `parkour_game` |
| `/fishing/` | `fishing_game` (xframe exempt) | `fishing_game` |
| `/fishing-portal/` | `fishing_portal` | `fishing_portal` |

### Views
- `home`: simple redirect to `parkour_game`
- `parkour_game`: renders `core/parkour.html`
- `fishing_game`: renders `core/fishing.html` with `@xframe_options_exempt` so
  it can be embedded in an iframe
- `fishing_portal`: renders `core/fishing_portal.html` which iframes
  `fishing_game`

### Settings highlights
- `DEBUG = True` (should be `False` in production)
- `ALLOWED_HOSTS = ['*']` (open — acceptable behind Cloudflare/Nginx proxy)
- `SECRET_KEY` is hardcoded (insecure for production; should be env var)
- `CSRF_TRUSTED_ORIGINS` includes the production domain
- Static files collected to `staticfiles/`, served via `STATIC_URL = "static/"`
- `MEDIA_ROOT` configured but unused (no file uploads)

---

## Frontend / Templates

### `base.html`
- Extends nothing; is the root layout
- Loads **Metronic** UI framework (Bootstrap-based)
- Fixed header with:
  - 3×3 dots **game launcher button** (popup with Parkour + Fishing SVG icons)
  - "Parkour" logo link
- `{% block content %}` for page body
- `{% block extra_css %}` / `{% block extra_js %}` extension points
- Inline JS handles the launcher popup open/close

### `parkour.html` (~1008 lines)
A self-contained **browser parkour platformer** built on the HTML5 Canvas API.

**Game features:**
- Player movement: WASD / arrow keys, double jump, wall-slide, wall-jump
- Procedurally generated platforms (static, moving, crumble, spring types)
- Obstacles: spikes on platforms
- Power-ups: shield, magnet, boost, extra life
- Collectibles: coins
- HUD: distance (score), personal best, lives, coin count
- Difficulty scales with distance
- Save system: multiple named save slots stored in `localStorage`, with
  import-from-code string feature
- Web Audio API for sound effects (jump, double-jump, wall-jump, land, coin,
  spring, power-up, shield, death, pause)
- Procedural background: stars, mountains, city buildings with lit windows
- Fullscreen support

**Architecture:** All game logic is in a single IIFE inside the template's
`{% block extra_js %}`. State is managed via plain JS objects.

### `fishing_portal.html` (~104 lines)
- Extends `base.html`
- Renders `fishing_game` in a full-height `<iframe>`
- Fullscreen toggle button overlaid on iframe
- JS dynamically sizes iframe to fill viewport minus header height

### `fishing.html` (~3467 lines)
- Standalone HTML (does **not** extend `base.html`)
- Served at `/fishing/` with `X-Frame-Options` exempt so it can be iframed
- Full fishing game implemented in vanilla JS / Canvas

---

## Deployment

### `deploy.sh`
Intended to be run on the VPS after a `git pull`:
1. Activates Python venv
2. Runs `python manage.py migrate`
3. Runs `python manage.py collectstatic --noinput`
4. Restarts `gohifun` systemd/gunicorn service
5. Optionally purges Cloudflare cache (requires `CF_ZONE_ID` + `CF_API_TOKEN`
   env vars)

### Infrastructure (inferred)
- VPS running gunicorn + systemd service named `gohifun`
- Cloudflare in front for CDN/cache
- Domain: `parkour.lovesupplychain.com`
- Git remote: `ghftony/Leozgams` on GitHub, production tracks `main`

---

## Known Issues / Observations

1. **Hardcoded secret key** in `settings.py` — should be moved to an env var
   (e.g. via `python-decouple` or `os.environ`)
2. **`DEBUG = True`** should be `False` in production; a separate
   `settings_prod.py` or env-var override is recommended
3. **No authentication** — all game pages are publicly accessible (intentional
   for this use-case)
4. **No models** — `core/models.py` is empty; high scores and save data are
   stored client-side in `localStorage`, not persisted server-side
5. **Fishing game is very large** (3467 lines in one template) — candidate for
   being moved to a static JS file
6. **Static assets** include the full Metronic UI bundle (`style.bundle.css`,
   `plugins.bundle.js`, `scripts.bundle.js`) which adds significant page weight
   for simple game pages
7. **`MEDIA_ROOT`** is configured but never used; can be removed if file uploads
   are not planned
