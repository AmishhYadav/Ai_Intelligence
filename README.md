# Ai_Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3670A0?style=flat&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)](https://kubernetes.io/)

A state-of-the-art Real-Time AI Intelligence Platform designed for high scalability, autonomous reasoning, and event-driven processing.

## 🚀 Overview

The **Real-Time AI Intelligence Platform** is a distributed microservice architecture designed to handle high-volume event streams and provide autonomous reasoning via LLMs. It bridges the gap between raw data ingestion and intelligent action through a decoupled, event-driven mesh.

### Core Pillars
- **Distributed Intelligence**: Decoupled agents coordinating via Kafka.
- **Semantic Memory**: High-performance RAG using Qdrant vector space.
- **Tool Orchestration**: First-class support for the Model Context Protocol (MCP).
- **Enterprise Grade**: Built for Kubernetes with structured JSON logging and native health probes.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white) |
| **API Gateway** | ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi) / ![Uvicorn](https://img.shields.io/badge/Uvicorn-4051b5?style=flat-square) |
| **Event Bus** | ![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-000?style=flat-square&logo=apachekafka) |
| **Vector DB** | ![Qdrant](https://img.shields.io/badge/Qdrant-f33f3e?style=flat-square) |
| **State/Cache** | ![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat-square&logo=redis&logoColor=white) |
| **AI Models** | Google Gemini (Pro/Flash), Anthropic Claude (Sonnet/Haiku) |
| **Orchestration** | ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat-square&logo=docker&logoColor=white) / ![Kubernetes](https://img.shields.io/badge/kubernetes-%23326ce5.svg?style=flat-square&logo=kubernetes&logoColor=white) |

---

## 🔱 Getting Started

### 1. Forking Instructions

To contribute or customize the platform, please follow these forking guidelines:

1.  **Fork the Repository**: Click the 'Fork' button at the top right of the GitHub page.
2.  **Clone your Fork**:
    ```bash
    git clone https://github.com/YOUR_USERNAME/Ai_Intelligence.git
    cd Ai_Intelligence
    ```
3.  **Configure Upstream Remotes**:
    ```bash
    git remote add upstream https://github.com/AmishhYadav/Ai_Intelligence.git
    ```
4.  **Syncing with Upstream**:
    ```bash
    git fetch upstream
    git checkout main
    git merge upstream/main
    ```

### 2. Local Setup (Quick Start)

The platform is fully containerized. To spin up the entire architecture:

1.  **Configure Environment**:
    ```bash
    cp ai-platform/.env.example ai-platform/.env
    # Edit .env with your Google Gemini / Anthropic API keys
    ```
2.  **Launch Services**:
    ```bash
    cd ai-platform
    docker-compose up --build -d
    ```
3.  **Access the Dashboard**: Open `http://localhost:8501` to access the Nova UI.

---

## 🏗 System Architecture

The platform follows a **Clean Architecture** pattern, separating the business logic (Agents/Reasoning) from the infrastructure (Kafka/Redis/Qdrant).

```mermaid
graph LR
    A[UI / External] -->|API| B(Gateway)
    B -->|Events| C{Kafka}
    C --> D[Ingestion]
    D --> E[Embedding]
    E -->|Vectors| F[(Qdrant)]
    C --> G[Reasoning Agent]
    G -->|Context| F
    G -->|Session| H[(Redis)]
    G -->|Tools| I[MCP Server]
```

Detailed documentation for each component is available in the **[ai-platform/](file:///Users/amish/Ai_Intelligence/ai-platform)** directory.

---

## 📜 Coding Standards & Contributing

We maintain high code quality standards:
- **Linting**: All Python code must pass `flake8` or `ruff` linting.
- **Type Safety**: Strictly enforced type hints (`mypy`).
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

### How to Contribute
1. Create a feature branch (`git checkout -b feat/amazing-feature`).
2. Commit your changes.
3. Push to the branch (`git push origin feat/amazing-feature`).
4. Open a Pull Request.

---

## 🔒 Security & Privacy

- **Data Encryption**: All PII is encrypted at rest in Redis/Qdrant.
- **Authentication**: JWT-based stateless authentication at the Gateway level.
- **Reporting Vulnerabilities**: Please email `security@example.com` for vulnerability reports.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Built with ❤️ for the future of Autonomous Intelligence.
