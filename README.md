# AIoT 轨道交通工具监测系统（项目骨架）

## 1. 项目结构

```text
demo/
├── backend/                # FastAPI 后端
├── frontend/               # Vue3 + Vite 前端
├── infra/database/init/    # PostgreSQL 初始化 SQL
└── docker-compose.yml      # 一键启动编排
```

## 2. 环境准备

- Docker Desktop
- Node.js 20+（如果你本地直接跑前端）
- Python 3.11+（如果你本地直接跑后端）

## 3. 首次配置

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

如果你用 Docker Compose，`backend/.env` 里建议改为：

```env
POSTGRES_HOST=postgres
REDIS_HOST=redis
MQTT_HOST=mqtt
```

## 4. 一键启动（推荐）

```bash
docker compose up -d --build
```

启动后访问：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端 Swagger：[http://localhost:8000/docs](http://localhost:8000/docs)
- EMQX 控制台：[http://localhost:18083](http://localhost:18083)

## 5. 本地开发（非 Docker）

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 6. 当前已配置能力

- FastAPI 健康检查与统计 API
- WebSocket 告警通道 `/ws/alerts`
- MQTT 客户端订阅检测 Topic
- PostgreSQL JSONB 数据表与索引初始化
- Redis 服务基础可用

## 7. 下一步建议

- 接入 YOLO 边缘端真实上报格式
- 在后端增加规则引擎与告警入库逻辑
- 在前端增加 ECharts 实时图表面板
