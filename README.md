# ✂️ Snip — URL Shortener

A minimal, production-ready URL shortener built with **FastAPI + Python**, containerized with **Docker**, and deployed via a full **CI/CD pipeline** on GitHub Actions → Render.

![CI/CD](https://github.com/jimsidi/snip-url-shortener/actions/workflows/ci-cd.yml/badge.svg)

---

## 🧱 Architecture

Browser
│
▼
[ Render (FastAPI) ]  ◄──── GitHub Actions deploys on push to main
│
├── POST /api/shorten      → generate short code, store in SQLite
├── GET  /{code}           → look up and redirect
├── GET  /api/stats/{code} → click analytics
└── GET  /health           → uptime check

---

## 🚀 Features

- 🔗 Shorten any URL instantly
- ✏️ Optional custom short codes
- 📊 Click analytics per link
- 🐳 Fully Dockerized
- ⚙️ CI/CD via GitHub Actions (test → build → deploy)
- 🏥 Health check endpoint for uptime monitoring

---

## 🛠️ Tech Stack

| Layer      | Tech                        |
|------------|-----------------------------|
| Backend    | Python 3.12, FastAPI        |
| Database   | SQLite (via aiosqlite)      |
| Container  | Docker (multi-stage build)  |
| CI/CD      | GitHub Actions              |
| Hosting    | Render (free tier)          |
| Registry   | Docker Hub                  |

---

## 📦 Local Development

### Run directly

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Visit: http://localhost:8000

### Run with Docker

```bash
docker compose up --build
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## ⚙️ CI/CD Pipeline

Every push to `main` triggers the GitHub Actions workflow:

push to main
│
▼
[🧪] pytest tests/           ← runs all 8 tests
│
▼
[🐳] docker build & push     ← builds image, pushes to Docker Hub
│
▼
[🌐] curl Render deploy hook ← triggers auto-deploy on Render

---

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `RENDER_DEPLOY_HOOK_URL` | Webhook URL from Render dashboard |

---

## 🌐 Deploy to Render

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect repo
3. Render auto-detects `render.yaml` and configures the service
4. Copy the **Deploy Hook URL** from Render dashboard → add as GitHub secret

*Built by [@jimsidi](https://jimsidi.github.io) — learning DevOps one pipeline at a time.*