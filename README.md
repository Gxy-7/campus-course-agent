# 校园课程智能助手

基于 **Vue 3 + FastAPI + MySQL + DeepSeek + 本地 Chroma** 的校园课程 Agent 项目。

学生可以：

- 查看和管理课程
- 查看我的课表
- 选课 / 退课，并检测时间冲突
- 管理学习计划
- 让课程助手查询课表、检索课程资料、保存学习计划

管理员可以：

- 管理课程和课表
- 上传课程资料并建立向量知识库
- 管理用户

## 已实现功能

| 模块 | 功能 |
| --- | --- |
| 认证与用户 | 注册、登录、JWT、角色权限、个人信息、修改密码、用户管理 |
| 课程管理 | 课程增删改查、老师、课程代码唯一、启用/停用 |
| 课表管理 | 星期、节次、周次范围、单双周、教室 |
| 学生课表 | 我的课表、周次切换、选课/退课、时间冲突检测 |
| 学习计划 | 计划增删改查、归属隔离 |
| 课程助手 | DeepSeek 对话、工具调用、SSE 流式输出 |
| 课程资料 | 上传 PDF/Word/Markdown/TXT、文本抽取、切块、入库 |
| RAG | bge-m3 Embedding、本地 Chroma 向量检索、BM25 回退、来源引用 |
| MCP | FastMCP 独立工具服务、JWT 透传鉴权、服务不可用时自动回退进程内执行 |
| 权限与安全 | 管理员接口保护、学生数据隔离、Markdown XSS 过滤 |

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、Element Plus、Vue Router、Axios |
| 后端 | FastAPI、SQLAlchemy、Pydantic |
| 数据库 | MySQL 8 |
| 鉴权 | JWT |
| 大模型 | DeepSeek，OpenAI 兼容接口 |
| Agent | OpenAI SDK Function Calling + 手写工具循环 |
| 工具服务 | FastMCP，streamable-http 独立进程 |
| 流式输出 | SSE |
| Embedding | 硅基流动 `BAAI/bge-m3` |
| 向量库 | Chroma，本地持久化 |
| 文档解析 | pypdf、python-docx |
| 关键词检索 | jieba + rank-bm25 |
| 测试 | pytest + 内存 SQLite |

## 架构

```text
浏览器 / Vue 3
   │
   │ JSON、SSE
   ▼
FastAPI (8000)
   ├─ JWT 鉴权
   ├─ 课程 / 课表 / 选课 / 学习计划 / 资料接口
   ├─ Agent 工具循环
   │    ├─ get_my_schedule
   │    ├─ search_course_docs
   │    └─ save_study_plan
   ├─ DeepSeek Chat API
   ├─ MySQL：业务数据、资料文本块
   ├─ Chroma：本地向量索引
   ├─ uploads：头像和课程资料文件
   └─ MCP Client ──HTTP──► FastMCP 工具服务 (8001)
                             └─ 同样的三个工具，独立进程执行
```

### RAG 流程

```text
上传资料
  → 抽取纯文本
  → 按约 500 字切块，重叠约 50 字
  → MySQL 保存资料和文本块
  → bge-m3 向量化
  → 写入本地 Chroma

用户提问
  → 问题向量化
  → Chroma 检索 top 3
  → 没有命中或向量服务异常时回退 BM25
  → 片段交给 DeepSeek
  → 基于片段回答并标注真实来源文件
```

### MCP 工具服务

Agent 默认在进程内执行工具。配置了 `MCP_SERVER_URL` 且请求带 JWT 时，改为把工具调用发给独立的 FastMCP 进程：

```text
用户提问
  → DeepSeek 返回工具调用请求
  → Agent 把工具名 + 参数 + 原始 JWT 发给 MCP 服务 (8001)
  → MCP 服务解析 JWT 得到用户身份，查自己的数据库
  → 结果回传 Agent，再交回 DeepSeek 生成回答
```

设计要点：

- MCP 服务不重新实现业务，复用 `app/services` 里的同一批 service
- 身份靠透传的 JWT 识别，MCP 侧同样做数据隔离，模型无法伪造 `user_id`
- MCP 进程未启动、超时或返回异常时，自动回退进程内执行，对话不中断
- 不配置 `MCP_SERVER_URL` 时行为和之前完全一致

```powershell
# 单独开一个终端启动工具服务
cd backend
.\.venv\Scripts\Activate.ps1
python mcp_server.py
```

## 目录结构

```text
campus-course-agent/
├─ backend/
│  ├─ app/
│  │  ├─ api/                 # 路由
│  │  ├─ services/            # 业务、Agent、RAG、向量服务
│  │  ├─ models/              # ORM 模型
│  │  ├─ schemas/             # Pydantic 模型
│  │  ├─ dependencies/        # JWT、角色依赖
│  │  ├─ common/              # 统一返回、异常
│  │  └─ utils/
│  ├─ tests/                  # pytest 测试
│  ├─ uploads/                # 上传文件（不提交）
│  ├─ chroma_data/            # 本地向量库（不提交）
│  ├─ mcp_server.py           # FastMCP 工具服务入口
│  ├─ .env.example
│  ├─ requirements.txt
│  ├─ requirements-dev.txt
│  └─ pytest.ini
├─ frontend/
│  └─ src/
│     ├─ api/
│     ├─ views/
│     ├─ layouts/
│     ├─ router/
│     └─ utils/
├─ sql/
│  ├─ backend.sql             # 用户表 + 演示账号
│  ├─ 002_course.sql          # 课程表 + 演示课程
│  ├─ 003_schedule.sql        # 课表 + 演示课表
│  ├─ 004_enrollment.sql      # 选课关系 + 演示选课
│  ├─ 005_study_plan.sql      # 学习计划 + 演示计划
│  └─ 007_course_docs.sql     # 课程资料和文本块
├─ docs/
│  └─ course-materials/       # 课程资料样例
└─ README.md
```

## 快速开始

### 1. 环境要求

- Python 3.12+
- Node.js 22 LTS 或 24+
- MySQL 8.0+
- DeepSeek API Key
- 硅基流动 Embedding API Key（可选，不配置时使用 BM25）

### 2. 创建数据库

```sql
CREATE DATABASE backend DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 导入 SQL

在项目根目录执行：

```powershell
mysql -u root -p backend < sql/backend.sql
mysql -u root -p backend < sql/002_course.sql
mysql -u root -p backend < sql/003_schedule.sql
mysql -u root -p backend < sql/004_enrollment.sql
mysql -u root -p backend < sql/005_study_plan.sql
mysql -u root -p backend < sql/007_course_docs.sql
```

注意：

- `sql/backend.sql` 会 `DROP TABLE users`，不要在有正式数据的库上重复执行。
- `sql/002_course.sql` 包含课程建表和演示课程。
- 课程资料表只建结构，不自动插入资料；资料需要管理员在页面中上传。

### 4. 配置后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

编辑 `backend/.env`：

```env
DATABASE_URL=mysql+pymysql://root:你的密码@127.0.0.1:3306/backend
JWT_SECRET_KEY=换成长随机字符串
JWT_EXPIRE_HOURS=24
JWT_ALGORITHM=HS256

LLM_API_KEY=你的DeepSeekKey
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

EMBEDDING_API_KEY=你的硅基流动Key
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
EMBEDDING_DIM=1024

# 可选：留空或不写则 Agent 只在进程内执行工具
MCP_SERVER_URL=http://127.0.0.1:8001/mcp
```

启动：

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

接口文档：<http://127.0.0.1:8000/docs>

### 5. 启动 MCP 工具服务（可选）

只有想让工具在独立进程里执行时才需要。另开一个终端：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python mcp_server.py
```

不启动也没关系，Agent 会自动回退到进程内执行。详见 [MCP 工具服务](#mcp-工具服务)。

### 6. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

访问：<http://127.0.0.1:5173>

## 演示账号

导入 SQL 后可用：

| 账号 | 密码 | 角色 | 说明 |
| --- | --- | --- | --- |
| `admin` | `admin` | 管理员 | 课程、课表、资料、用户管理 |
| `aaa` | `123` | 学生 | 已选 CS101、CS102 等演示课程 |
| `bbb` | `123` | 学生 | 用于验证数据隔离 |

注册的新用户默认是 `student`。

## 演示流程

### 管理员

1. 使用 `admin / admin` 登录。
2. 进入“课程管理”，查看或新增课程。
3. 进入“课表管理”，为课程新增星期、节次、周次和教室。
4. 进入“资料管理”，选择课程并上传 `docs/course-materials` 中的资料。
5. 修改 Embedding Key 或模型后，点击“重新入库”。

### 学生

1. 使用 `aaa / 123` 登录。
2. 进入“课程列表”，选课或退课。
3. 进入“我的课表”，切换周次查看课表。
4. 进入“课程助手”：
   - 问“我有什么课？”
   - 问“数据结构实验报告迟交会怎么处理？”
   - 说“帮我制定一份期末复习计划并保存”
5. 进入“学习计划”，查看 Agent 保存的计划。

## Agent 工具

| 工具 | 作用 |
| --- | --- |
| `get_my_schedule` | 查询当前登录学生的课表 |
| `search_course_docs` | 检索已上传的课程资料 |
| `save_study_plan` | 保存当前用户的学习计划 |

设计约束：

- 用户身份从 JWT 获取，模型不能填写 `user_id`
- 一次对话最多执行 5 轮工具调用
- 只有用户明确要求保存时才调用 `save_study_plan`
- 同一轮最多成功保存一份计划
- 回答资料问题时必须基于检索片段并标注来源
- 检索为空时明确说没有找到，不编造
- 三个工具同时提供进程内实现和 MCP 远程实现，走哪条路对用户透明

## 接口速览

| 模块 | 主要接口 |
| --- | --- |
| 认证 | `POST /api/auth/login`、`POST /api/auth/register` |
| 用户 | `GET /api/user/me`、`GET /api/user/list` |
| 课程 | `GET /api/course/list`、`POST /api/course` |
| 课表 | `GET /api/schedule/my`、`POST /api/schedule` |
| 选课 | `GET /api/enrollment/my`、`POST /api/enrollment/{course_id}` |
| 学习计划 | `GET /api/study-plan/list`、`POST /api/study-plan` |
| 课程助手 | `POST /api/chat`、`POST /api/chat/stream` |
| 课程资料 | `POST /api/course-doc/upload`、`POST /api/course-doc/reindex` |

完整参数见 `/docs`。

## 测试

测试使用内存 SQLite，不连接 MySQL，不调用 DeepSeek / Embedding。

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pytest
```

当前覆盖：

- 登录、401、角色权限
- 课程 CRUD、重复代码、学生课程过滤
- 课表、选课、时间冲突
- 学习计划 CRUD、越权隔离、日期校验
- 资料上传、检索、来源文件名、删除级联

当前结果：

```text
13 passed
```

## 安全与设计要点

- JWT 鉴权，学生只能访问自己的课表、选课和学习计划
- 资料上传、重新入库、删除只有管理员可以操作
- 模型不能决定 `user_id`，工具执行时使用 JWT 当前用户
- MCP 服务只接受携带 JWT 的调用，自己解析身份，不信任模型传入的用户参数
- Markdown 回答经过 DOMPurify，避免 XSS
- RAG 检索失败和“没有检索到”区分处理
- 回答资料问题时强制标注真实来源文件
- 管理端删除资料时同步删除文本块和向量

## 已知限制

- 对话历史暂不持久化，切换页面后会清空
- 不支持扫描版 PDF 的 OCR
- 向量检索使用本地 Chroma，当前没有拆独立向量服务
- MCP 工具服务和 FastAPI 仍共用同一套 service 和数据库，没有做独立的工具权限模型
- 还没有 Docker Compose 和 CI
- 资料检索默认取 top 3，适合演示，生产环境需要调优

## 常见问题

### 后端 401

确认后端已启动，浏览器里有有效 token；过期后重新登录。

### 修改 `.env` 不生效

`.env` 不会触发热重载，必须重启后端进程。

### 上传资料后 Agent 说没有找到

- 确认资料已上传成功
- 确认 Embedding Key 已配置
- 到“资料管理”点击“重新入库”
- 查看后端日志是否有 Embedding 或 Chroma 错误

### 扫描版 PDF 没有文本

当前不支持 OCR。请上传带文字层的 PDF、Word、Markdown 或 TXT。

### 向量检索效果不好

可以调整：

- 切块大小与重叠长度
- top-k
- Embedding 模型
- 是否增加 BM25 混合检索

修改 Embedding 模型后必须重新入库。

### MCP 服务启动报 `KeyError: 'websockets-sansio'`

FastMCP 2.13 启动 HTTP 时默认向 uvicorn 请求 `websockets-sansio` 协议，而项目锁定的 uvicorn 0.34.0 只支持 `auto / none / websockets / wsproto`。`mcp_server.py` 已通过 `uvicorn_config={"ws": "none"}` 关闭 WebSocket（MCP 的 streamable-http 不需要它）。如果升级依赖后仍出现该错误，检查是否改动了这段配置。

### 对话里工具步骤显示但结果像旧的

`MCP_SERVER_URL` 配置了但 MCP 进程没启动时，Agent 会静默回退到进程内工具，表现完全一致。确认是否真的走了 MCP，可以看工具服务日志里有没有对应的 `POST /mcp`。
