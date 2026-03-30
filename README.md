# AIoT 轨道交通工具监测系统（项目骨架）

## 1. 项目结构

```text
aiot-demo/
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


停服务：
cd /Users/xiaoba/work/aiot-demo
docker compose down
下次恢复：
docker compose up -d

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

## 6. 默认账号与凭据（开发环境）

前端登录（http://localhost:5173）：

- 管理员：`admin / Admin@123`
- 值班员：`operator / Operator@123`

EMQX 控制台（http://localhost:18083）：

- 默认：`admin / public`

PostgreSQL：

- Host：`localhost`
- Port：`5432`
- Database：`aiot_monitor`
- Username：`aiot_user`
- Password：`aiot_password`

Redis：

- Host：`localhost`
- Port：`6379`
- Password：`(空)`

## 7. 当前已配置能力

- FastAPI 健康检查与统计 API
- WebSocket 告警通道 `/ws/alerts`
- MQTT 客户端订阅检测 Topic
- PostgreSQL JSONB 数据表与索引初始化
- Redis 服务基础可用
- 前端登录页与路由鉴权

## 8. 下一步建议

- 接入 YOLO 边缘端真实上报格式
- 在后端增加规则引擎与告警入库逻辑
- 在前端增加 ECharts 实时图表面板

## 9. 工具管理接口（已对接数据库）

- `GET /api/v1/tools`：分页查询（支持 `tool_code/tool_type/tool_name/stock/page/page_size`）
- `POST /api/v1/tools`：新增工具
- `PUT /api/v1/tools/{tool_id}`：修改工具
- `DELETE /api/v1/tools/{tool_id}`：删除单条
- `POST /api/v1/tools/batch-delete`：批量删除（请求体：`{"ids":[1,2,3]}`）

说明：数据库已新增 `tools` 表。后端启动时会自动建表并在空表时初始化示例数据。

## 10. 工具识别（YOLO 模型）

后端新增接口：`POST /api/v1/tool-count/detect`（`multipart/form-data`，字段名 `image`）。

模型路径配置：

- Docker：`TOOL_COUNT_MODEL_PATH=/app/model/best.pt`（`docker-compose.yml` 已挂载 `./best.pt`）
- 本地开发：`TOOL_COUNT_MODEL_PATH=/Users/xiaoba/work/aiot-demo/best.pt`

页面入口：登录后左侧菜单 `工具识别`，上传“检修前/检修后”两张图后可一键识别并比较数量差异。
