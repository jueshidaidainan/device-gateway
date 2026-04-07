# Ops Agent Service

`ops-agent-service` is a LangGraph-powered diagnostic service for the device gateway project.

## What it does

- Analyzes whether traffic fluctuations look normal or abnormal
- Explains alerts using metrics, logs, and gateway connection state
- Exposes Swagger-friendly HTTP APIs for interview demos and integration
- Persists every run into SQLite for replay and auditing

## Stack

- Python 3.11+
- FastAPI
- LangGraph
- Pydantic
- Prometheus HTTP API
- Loki HTTP API
- OpenAI-compatible chat model

## Endpoints

- `POST /agent/analyze`
- `POST /agent/explain-alert`
- `GET /agent/health`
- `GET /docs`

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
uvicorn app.main:app --reload --port 8010
```

## Notes

- The service uses `LangGraph` for stateful orchestration but keeps the graph intentionally lightweight.
- The model layer supports OpenAI-compatible endpoints so you can point it at OpenAI or compatible gateways later.
- If the model is unavailable, the service degrades to deterministic analysis instead of returning fabricated results.

## Interview Guide

- 中文项目说明与面试指南：`项目说明与面试指南.md`
- 中文三分钟面试讲稿：`三分钟面试讲稿.md`
- 中文架构与流程图：`架构与流程图.md`
- 中文简历项目描述：`简历项目描述.md`
- 中文模拟面试问答：`模拟面试问答.md`
