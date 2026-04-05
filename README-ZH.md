<div align="center">

# 🔋 RippleStorage

**工商业储能智能决策与收益推演系统**

*让储能投资在数字孪生中预演，助运营决策在百战模拟后胜出*

[![GitHub Stars](https://img.shields.io/github/stars/xuegangwu/RippleStorage?style=flat-square&color=DAA520)](https://github.com/xuegangwu/RippleStorage/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/xuegangwu/RippleStorage?style=flat-square)](https://github.com/xuegangwu/RippleStorage/network)
[![Docker](https://img.shields.io/badge/Docker-Build-2496ED?style=flat-square&logo=docker&logoColor=white)](https://github.com/xuegangwu/RippleStorage/pkgs/container/ripplestorage)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?style=flat-square&logo=vue.js&logoColor=white)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-Python-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)

[English](./README.md) | [中文](./README-ZH.md)

</div>

---

## ⚡ 项目概述

**RippleStorage** 是一款面向工商业储能的 AI 决策支持平台。通过数字孪生仿真替代经验拍脑袋：

1. **图谱构建** — 建立资产知识图谱与市场环境节点。
2. **环境配置** — 设定容量、电价策略、负荷曲线、温控方式等参数。
3. **运行推演** — 执行峰谷套利与需量管理的充放电调度算法。
4. **报告生成** — 输出收益预测、IRR 测算与风险评估。
5. **智能交互** — 与理解上下文的 AI Agent 对话，深入解读结果。

> 你只需：上传负荷与电价数据，用自然语言描述投资场景。  
> RippleStorage 将返回：详细的收益报告、可执行的调度方案，以及可交互的 3D 产品结构展示。

### 🎯 愿景

- **面向投资方** — 在资本支出前，预演多种电价与负荷场景下的投资回报。
- **面向运营商** — 优化每日充放电策略，最大化套利收益与削峰填谷节约。
- **面向销售方** — 以照片级、可爆炸剖分的 3D Viewer 展示集装箱储能内部构造（电池簇、PCS、BMS、液冷、消防）。

---

## 🖼️ 截图与演示

| 3D 产品结构展示 | 仿真运行仪表盘 |
|---|---|
| 支持爆炸图、剖面透视、自动导览、HDR 环境光照 | 实时 SOC、功率、温度，动态能量流粒子 |

本地体验 3D 展示：`http://localhost:8765/showcase`

---

## 🚀 快速开始

### 环境要求

- **Node.js** 18+
- **Python** 3.12
- **uv**（Python 包管理器）

### 1. 克隆项目

```bash
git clone https://github.com/xuegangwu/RippleStorage.git
cd RippleStorage
```

### 2. 启动后端

```bash
cd backend
source .venv/bin/activate   # 若未创建，先用 uv venv 创建
uv pip install -r requirements.txt
FLASK_PORT=8766 python run.py
```

后端地址：`http://localhost:8766`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev -- --port 8765
```

前端地址：`http://localhost:8765`

> Vite 开发服务器已将 `/api` 代理至 `http://localhost:8766`。

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS |
| 3D 展示 | Three.js (WebGL) + EffectComposer (辉光) + CSS2DRenderer |
| 后端 | Flask + Python 3.12 |
| 仿真引擎 | 自研能量调度算法（无需外部 OASIS 依赖） |
| AI / 大模型 | Kimi API + Zep Cloud 记忆 |
| 容器化 | Docker + Docker Compose（可选） |

---

## 📂 项目结构

```
RippleStorage/
├── backend/              # Flask 应用
│   ├── app/              # 路由、服务、配置
│   ├── scripts/          # 仿真脚本
│   └── run.py            # 启动入口
├── frontend/             # Vue 3 + Vite
│   ├── src/              # 组件、页面、路由
│   └── public/           # 3d-showcase.html、静态资源
├── locales/              # 国际化 JSON（中/英）
├── static/               # Logo 与图片
├── Dockerfile
└── docker-compose.yml
```

---

## 🤝 贡献

欢迎提交 Issue 和 PR。如有重大改动，请先开 Issue 讨论。

---

## 📜 许可证

本项目基于 MIT 许可证开源。
