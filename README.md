# AIoT 轨道交通检修工具监测平台

> 当前文档基于仓库现状（2026-05-03）更新，覆盖后端 FastAPI、前端 Vue3、Docker Compose 一键部署与核心业务能力。

## 1. 项目概览

本项目用于轨道交通检修场景的工具数字化管理与识别，当前已落地：

- 用户登录与基于角色/权限的访问控制
- 工具台账管理（增删改查、分页、筛选、批量删除、CSV 导出）
- YOLO 工具识别（单图识别、检修前后数量对比）
- 系统设置（密码策略、告警阈值、工具类型字典）
- 关键操作日志记录与查询

## 2. 技术栈

- 前端：Vue 3 + Vite + Element Plus + Vue Router + Axios
- 后端：FastAPI + SQLAlchemy(Async) + Pydantic
- 数据层：PostgreSQL
- 中间件：Redis、EMQX（MQTT）
- AI 模型：Ultralytics YOLO（`best_tools.pt`）
- 部署：Docker Compose

## 3. 目录结构

```text
aiot-demo/
├── backend/                    # FastAPI 服务
├── frontend/                   # Vue 前端
├── infra/database/init/        # PostgreSQL 初始化脚本
├── docs/                       # 项目文档
├── best_tools.pt               # 工具识别模型文件（当前 Compose 挂载）
└── docker-compose.yml
```

## 4. 快速启动（推荐）

### 4.1 首次准备

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

如果通过 Docker Compose 启动，请确保 `backend/.env` 使用容器内服务名：

```env
POSTGRES_HOST=postgres
REDIS_HOST=redis
MQTT_HOST=mqtt
```

### 4.2 一键启动

```bash
docker compose up -d --build
```

访问地址：

- 前端：[http://localhost:5173](http://localhost:5173)
- 后端 Swagger：[http://localhost:8000/docs](http://localhost:8000/docs)
- EMQX 控制台：[http://localhost:18083](http://localhost:18083)

停止服务：

```bash
docker compose down
```

## 5. 本地开发启动（非 Docker）

### 5.1 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

本地运行时可在 `backend/.env` 指定模型路径，例如：

```env
TOOL_COUNT_MODEL_PATH=/Users/xiaoba/work/aiot-demo/best_tools.pt
```

### 5.2 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 6. 默认账号（仅空库首启时自动种子）

后端会在数据库为空时自动写入默认用户：

- 管理员：`admin / Admin@123`
- 员工：`operator / Operator@123`

说明：

- 登录是后端接口鉴权（`POST /api/v1/auth/login`），不是前端硬编码登录。
- 默认员工账号初始权限为 `工具管理`，如需使用“工具识别”等模块，请由管理员在权限管理页分配。

## 7. 当前核心接口

### 7.1 认证与基础

- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/stats`

### 7.2 工具管理

- `GET /api/v1/tools`
- `POST /api/v1/tools`
- `PUT /api/v1/tools/{tool_id}`
- `DELETE /api/v1/tools/{tool_id}`
- `POST /api/v1/tools/batch-delete`

### 7.3 工具识别

- `POST /api/v1/tool-count/detect`（`multipart/form-data`，字段名 `image`）
- `GET /api/v1/settings/operation-logs`（可筛选查看“工具识别”日志）

### 7.4 权限管理

- `GET /api/v1/permissions/options`
- `GET /api/v1/users`
- `POST /api/v1/users`
- `PUT /api/v1/users/{user_id}`
- `PUT /api/v1/users/{user_id}/permissions`
- `DELETE /api/v1/users/{user_id}`
- `GET /api/v1/users/me`
- `GET /api/v1/users/me/permissions`

### 7.5 系统设置

- `GET/PUT /api/v1/settings/password-policy`
- `GET/PUT /api/v1/settings/alert-threshold`
- `GET /api/v1/settings/tool-types`
- `GET /api/v1/settings/tool-types/options`
- `POST /api/v1/settings/tool-types`
- `PUT /api/v1/settings/tool-types/{tool_type_id}`
- `DELETE /api/v1/settings/tool-types/{tool_type_id}`
- `GET /api/v1/settings/operation-logs`

## 8. 已知运行要点

- `docker-compose.yml` 当前挂载模型文件为 `./best_tools.pt:/app/model/best.pt:ro`。
- 后端启动时会自动建表并执行种子初始化（工具、用户、系统配置）。
- WebSocket 告警通道为 `/ws/alerts`，当前保持基础连通能力（`pong` 响应）。

## 9. 下一步建议

- 将登录态升级为 JWT（替代 query 参数传 `requester_username`）
- 补齐工具识别结果落库与告警闭环
- 增加自动化测试（接口权限、识别流程、关键设置项）
