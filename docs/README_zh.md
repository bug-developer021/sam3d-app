# SAM3D 应用仓库说明

本仓库提供一个将照片转成 3D 网格的端到端系统，前端触发 SAM 分割，后台通过 SAM 3D Objects 与多视角几何处理生成可下载的三维模型，并通过浏览器进行渲染预览。

## 目录与组件
- **Backend (FastAPI)**：处理上传、任务调度、模型生成与结果下载。
- **Worker (Celery)**：在后台运行重建与优化任务，复用与 API 相同的代码基。
- **Frontend (Next.js/React)**：提供上传、任务列表和 3D/Mask 预览界面。
- **storage/**：持久化上传图片、生成的网格及掩码结果。

## 环境要求
- Python 3.10+（建议使用虚拟环境）
- Node.js 18+ 与 pnpm（前端构建）
- PostgreSQL 与 Redis（生产部署必需；本地开发可使用 docker-compose 内置服务）
- 可选：NVIDIA GPU 与 CUDA 驱动，以加速重建；无 GPU 时可使用模型跳过模式做轻量验证。

## 本地快速运行
### 1) 克隆与初始化
```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2)（可选）跳过模型初始化
仅做接口或流程验证时，可避免下载大模型：
```bash
export FORMA3D_SKIP_MODEL_INIT=true
```

### 3) 下载推理权重
需要真实重建时，先拉取 SAM 与 SAM 3D Objects 权重（SAM ~2.4GB，SAM3D 需 Hugging Face Token）：
```bash
python scripts/download_checkpoints.py
python scripts/download_sam3d_checkpoints.py
```

### 4) 启动后台 API
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Swagger 文档默认位于 `http://localhost:8000/docs`，ReDoc 位于 `/redoc`。

### 5) 启动前端
```bash
cd frontend
pnpm install
pnpm dev  # 生产环境可用 pnpm build && pnpm start
```
将浏览器指向 `http://localhost:3000` 即可体验上传、预览和下载。

## 使用 Docker Compose 运行全栈
仓库内置 `docker-compose.yml`，包含 PostgreSQL、Redis、后端、Worker 与前端：
```bash
docker compose build
docker compose up -d postgres redis
# 初始化数据库
docker compose run --rm backend alembic upgrade head
# 启动 API、Worker 与前端
docker compose up -d backend worker frontend
```
确保 `storage/` 目录作为共享卷被持久化，以保留上传与生成结果。

## 核心环境变量
- `AUTH_MODE`：`disabled|optional|required`，控制鉴权策略。
- `POSTGRES_SERVER`、`POSTGRES_PORT`、`POSTGRES_USER`、`POSTGRES_PASSWORD`、`POSTGRES_DB`：数据库配置。
- `REDIS_URL`：Celery 与限流使用的 Redis 连接串，例如 `redis://redis:6379/0`。
- `NEXT_PUBLIC_API_URL`：前端调用的后端地址（生产环境务必设置）。
- `FORMA3D_SKIP_MODEL_INIT`：设为 `true` 时跳过权重加载，适合无 GPU 的功能验证。

## API 概览
基址默认 `http://localhost:8000/api/v1`（完整 OpenAPI 见 `/openapi.json`）：
- `POST /jobs/upload`：上传 1~20 张图片触发重建，默认限流 30 次/60 秒。
- `GET /jobs/status/{job_id}`：轮询任务状态（`queued|processing|completed|completed_partial|failed`）。
- `GET /jobs`：列出当前用户的任务。
- `GET /jobs/download/{job_id}?format=obj|stl|gltf|glb|ply`：下载生成的网格。
- `POST /jobs/{job_id}/scale`：按 X/Y/Z 轴将完成的网格缩放到目标尺寸。
- `GET /health` 与 `GET /ready`：用于探针与监控。

## 开发与验证
- 轻量级检查（跳过模型时适用）：
  ```bash
  python test_multiview.py
  python test_optimization.py
  ```
- API 流程验证（需后端运行）：
  ```bash
  python test_api.py
  ```
- 代码语法快速检查：
  ```bash
  python -m compileall app frontend/components frontend/src/services pipeline.py
  ```

## 常见问题
- **运行缓慢或显存不足**：确保 GPU 驱动可用，或开启 `FORMA3D_SKIP_MODEL_INIT` 进行流程验证。
- **上传限制**：默认单张 50MB、总计 200MB，可通过环境变量 `RATE_LIMIT_UPLOAD_*` 和 `MAX_UPLOAD_*` 进行调整。
- **结果缺失**：确认 API 与 Worker 共享同一 `storage/` 挂载，且 Redis/数据库配置正确。
