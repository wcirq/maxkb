# MaxKB 本地启动与 PyCharm 调试

## 推荐启动顺序

建议严格按这个顺序执行：

1. 创建并启动 PostgreSQL 与 Redis
2. 确认 PostgreSQL 中 `maxkb` 数据库和 `vector` 扩展可用
3. 准备后端本地运行目录 `.runtime`
4. 执行 Django `migrate`
5. 启动 Python 后端，端口 `8080`
6. 启动前端管理端，端口 `3000`
7. 如需聊天页，再启动 chat 前端，端口 `3001`

如果前两步没完成，Python 后端不要启动。

## 基本信息

- Python 解释器：`/media/wcirq/data1/develop/big_model/MaxKB/.venv/bin/python`
- 工作目录：`/media/wcirq/data1/develop/big_model/MaxKB`
- Django 入口：`/media/wcirq/data1/develop/big_model/MaxKB/apps/manage.py`
- 配置文件：项目根目录 `config.yml`
- 前端目录：`/media/wcirq/data1/develop/big_model/MaxKB/ui`

项目已支持通过环境变量覆盖日志目录：

- 代码位置：`apps/maxkb/const.py`
- 环境变量：`MAXKB_LOG_DIR`

首次初始化数据库时还需要这两个配置存在于 `config.yml`：

- `EMBEDDING_MODEL_PATH`
- `EMBEDDING_MODEL_NAME`

## Docker 依赖服务

当前本机上的数据库和 Redis 容器是：

- PostgreSQL: `maxkb-pg`
- Redis: `maxkb-redis`

它们都连接在同一个 Docker 网络：

- Network: `maxkb-net`
- Driver: `bridge`
- Subnet: `172.18.0.0/16`

当前网络内地址：

- `maxkb-redis`: `172.18.0.2`
- `maxkb-pg`: `172.18.0.3`

### maxkb-pg 实际配置

- 镜像：`pgvector/pgvector:pg17`
- 容器名：`maxkb-pg`
- 启动命令：`docker-entrypoint.sh postgres`
- 端口映射：`5432:5432`
- 环境变量：
  - `POSTGRES_USER=root`
  - `POSTGRES_PASSWORD=Password123@postgres`
- 数据卷：
  - `maxkb-pg-data:/var/lib/postgresql/data`
- 只读挂载：
  - `installer/init.sql:/docker-entrypoint-initdb.d/init.sql:ro`
- 重启策略：`no`

`installer/init.sql` 内容：

```sql
CREATE DATABASE "maxkb";

\c "maxkb";

CREATE EXTENSION "vector";
```
docc    
### maxkb-redis 实际配置

- 镜像：`redis:7`
- 容器名：`maxkb-redis`
- 启动命令：

```text
docker-entrypoint.sh redis-server --appendonly yes --requirepass Password123@redis
```

- 端口映射：`6379:6379`
- 数据卷：
  - `maxkb-redis-data:/data`
- 工作目录：`/data`
- 重启策略：`no`

Redis 运行参数：

- AOF 持久化：`--appendonly yes`
- 密码认证：`--requirepass Password123@redis`

### Docker 可复现创建命令

先创建网络：

```bash
docker network create maxkb-net
```

再创建 PostgreSQL：

```bash
docker run -d \
  --name maxkb-pg \
  --network maxkb-net \
  -p 5432:5432 \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=Password123@postgres \
  -v maxkb-pg-data:/var/lib/postgresql/data \
  -v /media/wcirq/data1/develop/big_model/MaxKB/installer/init.sql:/docker-entrypoint-initdb.d/init.sql:ro \
  pgvector/pgvector:pg17
```

再创建 Redis：

```bash
docker run -d \
  --name maxkb-redis \
  --network maxkb-net \
  -p 6379:6379 \
  -v maxkb-redis-data:/data \
  redis:7 \
  redis-server --appendonly yes --requirepass Password123@redis
```

### Docker 启动与检查

启动已有容器：

```bash
docker start maxkb-pg maxkb-redis
```

检查状态：

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

验证 PostgreSQL：

```bash
docker exec -it maxkb-pg psql -U root -d maxkb -c "select 1;"
```

验证 Redis：

```bash
docker exec -it maxkb-redis redis-cli -a 'Password123@redis' ping
```

## 数据库初始化要求

当前项目默认连接参数来自 `config.yml`：

- PostgreSQL: `127.0.0.1:5432`
- DB Name: `maxkb`
- DB User: `root`
- DB Password: `Password123@postgres`
- Redis: `127.0.0.1:6379`
- Redis Password: `Password123@redis`

首次初始化空数据库时，需要先确认 `pgvector` 扩展存在，否则迁移到 `embedding` 表时会报错：

```text
type "vector" does not exist
```

执行：

```bash
docker exec -it maxkb-pg psql -U root -d maxkb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

验证：

```bash
docker exec -it maxkb-pg psql -U root -d maxkb -c "\dx"
```

输出里包含 `vector` 即可。

## 后端运行前准备

### 必须的环境变量

```bash
MAXKB_CONFIG=1
MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs
HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home
TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp
TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken
DJANGO_SETTINGS_MODULE=maxkb.settings
SERVER_NAME=web
PYTHONUNBUFFERED=1
```

说明：

- `MAXKB_CONFIG=1`
  让项目读取仓库根目录的 `config.yml`，不去读 `/opt/maxkb/conf`
- `MAXKB_LOG_DIR`
  覆盖日志目录，避免写 `/opt/maxkb/logs`
- `HF_HOME`
  HuggingFace 缓存目录
- `TMPDIR`
  运行期临时目录
- `TIKTOKEN_CACHE_DIR`
  tokenizer 缓存目录
- `DJANGO_SETTINGS_MODULE=maxkb.settings`
  Django 设置模块
- `SERVER_NAME=web`
  指定当前是 Web 服务
- `PYTHONUNBUFFERED=1`
  方便在终端和 PyCharm 实时看日志

### 首次准备目录

```bash
mkdir -p .runtime/logs .runtime/hf_home .runtime/tmp .runtime/tiktoken .runtime/embedding/shibing624_text2vec-base-chinese
```

### 执行迁移

在启动 Python 后端前，先跑：

```bash
MAXKB_CONFIG=1 \
MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs \
HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home \
TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp \
TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken \
./.venv/bin/python apps/manage.py migrate
```

如果迁移失败，先修迁移问题，不要继续启动后端。

## Python 后端启动

推荐直接用 Django 方式启动，调试最稳：

```bash
MAXKB_CONFIG=1 \
MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs \
HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home \
TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp \
TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken \
DJANGO_SETTINGS_MODULE=maxkb.settings \
SERVER_NAME=web \
PYTHONUNBUFFERED=1 \
./.venv/bin/python apps/manage.py runserver 0.0.0.0:8080 --noreload
```

访问地址：

```text
http://127.0.0.1:8080
```

## Local Model 服务启动

知识库检索、向量化和部分本地模型能力，不走上面的 `8080` Web 服务，而是单独请求本地模型服务：

- Host: `127.0.0.1`
- Port: `11636`
- 配置来源：根目录 `config.yml` 中的 `LOCAL_MODEL_HOST`、`LOCAL_MODEL_PORT`

如果只启动了 `SERVER_NAME=web` 的 Django，而没有启动本地模型服务，知识库相关操作会报类似错误：

```text
HTTPConnectionPool(host='127.0.0.1', port=11636): Max retries exceeded
```

### 推荐启动方式

```bash
MAXKB_CONFIG=1 \
MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs \
HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home \
TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp \
TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken \
SERVER_NAME=local_model \
PYTHONUNBUFFERED=1 \
./.venv/bin/python main.py dev local_model
```

访问地址：

```text
http://127.0.0.1:11636/admin/api/
```

### PyCharm Local Model 配置

新建第二个 `Python` 运行配置，填写：

- Name: `MaxKB Local Model`
- Script path: `/media/wcirq/data1/develop/big_model/MaxKB/main.py`
- Parameters: `dev local_model`
- Python interpreter: `/media/wcirq/data1/develop/big_model/MaxKB/.venv/bin/python`
- Working directory: `/media/wcirq/data1/develop/big_model/MaxKB`

Environment variables：

```text
MAXKB_CONFIG=1;MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs;HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home;TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp;TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken;SERVER_NAME=local_model;PYTHONUNBUFFERED=1
```

本地联调知识库时，通常至少要同时启动这四部分：

- PostgreSQL
- Redis
- Web 服务 `8080`
- Local Model 服务 `11636`

### 可选启动方式

如果你想走项目原生入口，也可以使用：

```bash
MAXKB_CONFIG=1 \
MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs \
HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home \
TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp \
TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken \
SERVER_NAME=web \
./.venv/bin/python main.py dev web
```

但调试时仍建议优先使用 `manage.py runserver --noreload`。

### PyCharm 后端配置

新建一个 `Python` 运行配置，填写：

- Name: `MaxKB Backend`
- Script path: `/media/wcirq/data1/develop/big_model/MaxKB/apps/manage.py`
- Parameters: `runserver 0.0.0.0:8080 --noreload`
- Python interpreter: `/media/wcirq/data1/develop/big_model/MaxKB/.venv/bin/python`
- Working directory: `/media/wcirq/data1/develop/big_model/MaxKB`

Environment variables：

```text
MAXKB_CONFIG=1;MAXKB_LOG_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/logs;HF_HOME=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/hf_home;TMPDIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tmp;TIKTOKEN_CACHE_DIR=/media/wcirq/data1/develop/big_model/MaxKB/.runtime/tiktoken;DJANGO_SETTINGS_MODULE=maxkb.settings;SERVER_NAME=web;PYTHONUNBUFFERED=1
```

## 前端启动

技术栈：

- Vue 3
- Vite
- TypeScript

前端不是由 Python 后端带起来的，开发时需要单独启动一个 Vite dev server。

### 前端脚本

定义在 `ui/package.json`：

- `npm run dev`
  启动管理端
- `npm run chat`
  启动聊天页
- `npm run build`
  构建管理端
- `npm run build-chat`
  构建聊天页

### 环境文件

管理端环境文件：`ui/env/.env`

```text
VITE_APP_NAME=admin
VITE_BASE_PATH=/admin/
VITE_APP_PORT=3000
VITE_ENTRY="admin.html"
```

聊天页环境文件：`ui/env/.env.chat`

```text
VITE_APP_NAME=chat
VITE_BASE_PATH=/chat/
VITE_APP_PORT=3001
VITE_ENTRY="chat.html"
```

### Vite 代理

Vite 配置在 `ui/vite.config.ts`，开发时会把这些请求代理到后端：

- `/admin/api` -> `http://127.0.0.1:8080`
- `/chat/api` -> `http://127.0.0.1:8080`
- `/static` -> `http://127.0.0.1:8080`
- `/doc` -> `http://127.0.0.1:8080`
- `/schema` -> `http://127.0.0.1:8080`
- `oss` 相关资源 -> `http://127.0.0.1:8080`

所以前端联调前，必须先启动后端。

### 安装依赖

```bash
cd /media/wcirq/data1/develop/big_model/MaxKB/ui
npm install
```

本机当前环境：

- Node.js: `v22.22.0`
- npm: `10.9.4`

### 启动管理端

```bash
cd /media/wcirq/data1/develop/big_model/MaxKB/ui
npm run dev
```

访问地址：

```text
http://127.0.0.1:3000/admin/
```

### 启动聊天页

```bash
cd /media/wcirq/data1/develop/big_model/MaxKB/ui
npm run chat
```

访问地址：

```text
http://127.0.0.1:3001/chat/
```

### PyCharm / WebStorm 前端运行方式

如果你想在 JetBrains 系列 IDE 里跑前端，可以新建一个 `npm` 运行配置：

- `package.json`: `/media/wcirq/data1/develop/big_model/MaxKB/ui/package.json`
- Command: `run`
- Scripts:
  - 管理端：`dev`
  - 聊天页：`chat`
- Working directory: `/media/wcirq/data1/develop/big_model/MaxKB/ui`

常见组合：

- 后端 PyCharm 配置跑 `8080`
- 前端 npm 配置跑 `3000`
- 浏览器打开 `http://127.0.0.1:3000/admin/`
