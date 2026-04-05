<div align="center">

# 🔋 RippleStorage

**Industrial & Commercial Energy Storage Intelligence — Predict Revenue, Optimize Dispatch, Visualize Assets**

工商业储能智能决策与收益推演系统  
*让储能投资在数字孪生中预演，助运营决策在百战模拟后胜出*

[![GitHub Stars](https://img.shields.io/github/stars/xuegangwu/RippleStorage?style=flat-square&color=DAA520)](https://github.com/xuegangwu/RippleStorage/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/xuegangwu/RippleStorage?style=flat-square)](https://github.com/xuegangwu/RippleStorage/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://github.com/xuegangwu/RippleStorage/pkgs/container/ripplestorage)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-Python-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

[English](./README.md) | [中文](./README-ZH.md)

</div>

---

## ⚡ Overview

**RippleStorage** is an AI-driven decision support platform for industrial and commercial (C&I) energy storage systems. It replaces guesswork with digital-twin simulation:

1. **Graph Build** — Construct the knowledge graph of your energy assets and market environment.
2. **Env Setup** — Configure system parameters (capacity, tariff, load profile, cooling).
3. **Simulation** — Run peak-valley arbitrage and demand-management dispatch algorithms.
4. **Report** — Generate revenue forecasts, IRR analysis, and risk assessments.
5. **Interaction** — Chat with an AI agent that understands the simulation context.

> You only need: upload a load & tariff dataset, and describe your investment scenario in natural language.  
> RippleStorage returns: a detailed earnings report, an actionable dispatch schedule, and an interactive 3D product showcase.

### 🎯 Vision

- **For Investors** — Pre-rehearse ROI under multiple tariff and load scenarios before capex commitment.
- **For Operators** — Optimize daily charge/discharge schedules to maximize arbitrage revenue and peak-shaving savings.
- **For Sales** — Showcase containerized battery internals (racks, PCS, BMS, HVAC, fire suppression) in a photorealistic, explodable 3D viewer.

---

## 🖼️ Screenshots & Demo

| 3D Product Showcase | Simulation Dashboard |
|---|---|
| Interactive explosion view, section (X-ray) mode, auto-tour, HDR environment | Real-time SOC, power, temperature with animated energy-flow particles |

Try the 3D showcase locally at: `http://localhost:8765/showcase`

---

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+
- **Python** 3.12
- **uv** (Python package manager)

### 1. Clone & enter the project

```bash
git clone https://github.com/xuegangwu/RippleStorage.git
cd RippleStorage
```

### 2. Backend

```bash
cd backend
source .venv/bin/activate   # or create it first with uv venv
uv pip install -r requirements.txt
FLASK_PORT=8766 python run.py
```

Backend will be available at `http://localhost:8766`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev -- --port 8765
```

Frontend will be available at `http://localhost:8765`.

> The Vite dev server proxies `/api` to `http://localhost:8766` automatically.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3 + Vite + Tailwind CSS |
| 3D Viewer | Three.js (WebGL) + EffectComposer (Bloom) + CSS2DRenderer |
| Backend | Flask + Python 3.12 |
| Simulation | Custom energy-dispatch engine (no external OASIS dependency) |
| AI / LLM | Kimi API + Zep Cloud memory |
| Container | Docker + Docker Compose (optional) |

---

## 📂 Project Structure

```
RippleStorage/
├── backend/              # Flask application
│   ├── app/              # API routes, services, config
│   ├── scripts/          # Simulation runners
│   └── run.py            # Entry point
├── frontend/             # Vue 3 + Vite
│   ├── src/              # Components, views, router
│   └── public/           # 3d-showcase.html, static assets
├── locales/              # i18n JSON (zh, en)
├── static/               # Logos and images
├── Dockerfile
└── docker-compose.yml
```

---

## 🤝 Contributing

Issues and PRs are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License

This project is licensed under the MIT License.
