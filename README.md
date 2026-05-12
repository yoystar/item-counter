# 物品计数标注工具

基于 OpenCV 模板匹配与 Fabric.js 的图片标注计数工具。上传图片后可通过自动识别或手动点击添加编号标注，支持导出标注结果。

## 功能

- 图片上传（支持 PNG / JPG / JPEG / GIF / BMP / WEBP，单文件最大 128 MB）
- 自适应阈值轮廓检测（`/detect`）
- 多角度 × 多尺度模板匹配识别（`/match`）
- 手动点击 / 框选识别 / 标注拖拽移动
- Ctrl+Z 撤销、标注重排序、重叠警告
- 画布直接导出为 PNG（完整保留标注样式）
- 深色 / 蓝白双主题

---

## 本地开发

### 环境要求

- Python 3.10+
- pip

### 安装与启动

```bash
# 进入代码目录
cd item-counter

# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器（debug 模式默认开启）
python3 app.py
```

访问 [http://localhost:5000](http://localhost:5000)

开发服务器启动参数可通过环境变量覆盖：

```bash
HOST=0.0.0.0 PORT=8000 FLASK_DEBUG=1 python3 app.py
```

### 运行测试

```bash
# 全部测试
pytest

# 单个文件
pytest tests/test_detector.py
pytest tests/test_app.py

# 单个用例
pytest tests/test_detector.py::test_detect_three_items

# 显示详细输出
pytest -v
```

---

## Docker 部署

### 本地验证

```bash
# 构建并在本地启动
docker compose up --build

# 后台运行
docker compose up --build -d

# 访问 http://localhost:5000

# 查看日志
docker compose logs -f

# 停止
docker compose down
```

默认对外端口为 `5000`，可通过环境变量修改：

```bash
APP_PORT=9000 docker compose up -d
```

---

### 部署到远程服务器

#### 方式一：服务器上直接构建（推荐）

适合服务器可以访问代码仓库的情况。

```bash
# 1. SSH 登录服务器
ssh user@your-server-ip

# 2. 拉取代码（或 git clone）
git clone <仓库地址> /docker/item-counter
cd /docker/item-counter

# 3. 启动服务
docker compose up --build -d

# 4. 查看运行状态
docker compose ps
docker compose logs -f
```

#### 方式二：本地打包后传输

适合服务器无法访问代码仓库，或希望在本地构建镜像后上传的情况。

```bash
# ── 本地操作 ──────────────────────────────

# 1. 构建镜像
docker build -t item-counter:latest .

# 2. 打包为文件
docker save item-counter:latest | gzip > item-counter.tar.gz

# 3. 传输到服务器
scp item-counter.tar.gz user@your-server-ip:/docker/item-counter/
scp docker-compose.yml  user@your-server-ip:/docker/item-counter/

# ── 服务器操作 ────────────────────────────

ssh user@your-server-ip
cd /docker/item-counter

# 4. 导入镜像
docker load < item-counter.tar.gz

# 5. 修改 docker-compose.yml，将 build: . 替换为 image: item-counter:latest
# 或直接指定镜像名启动
docker compose up -d
```

---

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_PORT` | `5000` | 对外暴露的宿主机端口 |
| `FLASK_DEBUG` | `0` | 设为 `1` 开启调试模式（仅限本地开发） |
| `HOST` | `127.0.0.1` | 直接运行 `python3 app.py` 时的监听地址 |
| `PORT` | `5000` | 直接运行 `python3 app.py` 时的监听端口 |

> `FLASK_DEBUG=1` 会开启 Werkzeug 交互式调试器，**严禁在生产环境使用**。

---

### 常用运维命令

```bash
# 查看容器状态
docker compose ps

# 实时查看日志（含 access log）
docker compose logs -f

# 重启服务（不重新构建）
docker compose restart

# 更新代码后重新构建并重启
docker compose up --build -d

# 查看 uploads 卷占用
docker volume inspect item-counter_uploads

# 进入容器排查问题
docker compose exec app sh
```

---

## 项目结构

```
item-counter/
├── app.py              # Flask 应用，5 个路由
├── detector.py         # OpenCV 检测引擎（轮廓检测 + 模板匹配）
├── static/
│   └── index.html      # 单文件前端（Fabric.js Canvas）
├── uploads/            # 上传图片存储目录（最多 100 张，30 天自动清理）
├── tests/
│   ├── conftest.py
│   ├── test_app.py
│   └── test_detector.py
├── requirements.txt    # 开发依赖（含测试库）
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```
