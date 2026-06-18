# AI Chat Web — 个人专属对话助手

轻量级 AI 可视化 Web 聊天页面，替代终端 CLI 交互模式，通过浏览器提供对话管理、历史回顾、项目上下文挂载等功能。

---

## 一、快速开始

### 环境要求

| 条件 | 最低版本 | 检查命令 |
|------|----------|----------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| 操作系统 | Windows / macOS / Linux | — |

> **不需要安装数据库**，SQLite 是 Python 内置的文件型数据库，零配置。

### 安装 & 启动

```bash
# 1. 进入项目目录
cd AI-agent

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 安装前端依赖
cd ../frontend
npm install

# 4. 回到根目录，双击 start.bat 启动
#    或分别启动：
#    终端1: cd backend && python run.py    → 后端 http://localhost:8176
#    终端2: cd frontend && npm run dev     → 前端 http://localhost:1420
```

启动后浏览器打开 **http://localhost:1420** 即可使用。

### 首次配置

#### 步骤一：确保 ccswitch 已配置 API

本项目的 API 调用基于你本地的 ccswitch 配置。请先确认 ccswitch 已正常工作：

```bash
# 检查 ccswitch 配置
ccswitch list

# 如果没有配置，先添加
ccswitch add <provider> --key sk-xxxxxxxx --model <model-name>
```

> ccswitch 是你的 API 网关切换工具，本项目不重复实现模型切换功能，直接复用它。

#### 步骤二：在 Web 设置页填写 API 信息

1. 点击侧边栏 **「API 设置」** → **「新增配置」**
2. 填写你的大模型 API 信息：
   - **配置名称**：随便填，如 `DeepSeek`
   - **Base URL**：`https://api.deepseek.com/v1`（兼容 OpenAI 格式即可）
   - **API Key**：`sk-xxxxxxxx`（与 ccswitch 中配置的 Key 一致）
   - **默认模型**：`deepseek-chat`
   - 打开 **「设为默认使用」** 开关
3. 回到聊天页，**「新建对话」**，开始聊天

> 如果你用 ccswitch 切换了模型，只需在 Web 设置页对应的修改 Base URL 和 API Key 即可同步。

---

## 二、功能说明

### 对话管理

| 操作 | 方式 |
|------|------|
| 新建对话 | 侧边栏 **「+ 新建对话」** |
| 切换对话 | 点击侧边栏列表中的会话 |
| 删除对话 | 右键会话 → **「删除」** |
| 设置标签 | 右键会话 → **「设置标签」** |
| 筛选对话 | 侧边栏下拉菜单按标签过滤 |

### 项目上下文挂载

在输入框下方工具栏：

- **「项目目录」** → 弹出原生目录选择器 → AI 自动感知项目结构
- **「选择文件」** → 弹出文件多选 → 文件内容作为对话上下文

已选文件以标签形式显示在输入框上方，可单独移除。挂载的文件内容会在发送消息时一并传给大模型。

### 上下文策略

- 模型上下文窗口上限 **~950KB**（1MB 模型，留 50KB 冗余）
- 打开历史会话后发送新消息，**完整历史 + 挂载内容** 一并传给模型
- 超出限制时从最早消息开始截断，保留最新消息
- 截断仅影响 API 调用，页面显示完整历史不受影响

### API 配置

- 支持多套 API 配置共存
- Key 以脱敏形式展示（`sk-****xxxx`），编辑时留空不更新
- 「启用」开关控制新对话默认使用哪个配置
- 所有 API 调用走后端代理，前端不暴露 Key

---

## 三、技术架构

```
浏览器 (Vue 3) ──HTTP/SSE──▶ FastAPI ──API──▶ 大模型 (DeepSeek 等)
                                   │
                                   ▼
                              SQLite 文件数据库
```

| 层级 | 技术 | 端口 |
|------|------|------|
| 前端 | Vue 3 + Vite + Ant Design Vue 4 | 1420 |
| 后端 | Python FastAPI + SSE 流式响应 | 8176 |
| 数据库 | SQLite（文件：`backend/data/ai_chat.db`） | 无端口 |

---

## 四、目录结构

```
AI-agent/
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── components/       # Sidebar / ChatWindow / MessageBubble / SettingsModal
│   │   ├── views/            # ChatView
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── api/              # HTTP + SSE 封装
│   │   └── router/           # 路由
│   └── package.json
├── backend/                  # Python FastAPI 后端
│   ├── app/
│   │   ├── main.py           # 入口 + CORS
│   │   ├── database.py       # SQLAlchemy 异步引擎
│   │   ├── models.py         # ORM 模型
│   │   ├── schemas.py        # Pydantic 校验
│   │   ├── routers/          # 配置 / 会话 / 聊天 / 上下文
│   │   └── services/         # LLM 调用 / 文件读取
│   ├── requirements.txt
│   └── run.py
├── start.bat                 # Windows 一键启动
├── start.sh                  # Linux/macOS 一键启动
├── .gitignore
└── README.md
```

---

## 五、分享与部署

### 源码分享

对方 clone 项目后：

```bash
cd AI-agent
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
# 双击 start.bat 或分别启动
```

**对方需要有：**
- Python 3.10+ / Node.js 18+
- 自己的 API Key（在 Web 设置页配置）
- ccswitch 已配置好（或直接用 Web 设置页管理 API）

**对方不需要：**
- 安装数据库
- 配置端口
- 修改任何代码

### 命令行直接启动（Windows / Linux / macOS）

```bash
# Windows: 双击 start.bat
# 或终端执行
./start.bat     # Windows
./start.sh      # macOS / Linux
```

---

## 六、数据管理

### 数据文件位置

```
backend/data/ai_chat.db
```

### 查看数据

**VS Code（推荐）：** 安装 `SQLite Viewer` 插件，双击 `.db` 文件。

**命令行：**

```bash
cd backend/data
sqlite3 ai_chat.db

.tables
SELECT * FROM api_configs;
SELECT * FROM conversations;
SELECT * FROM messages LIMIT 10;
.quit
```

### 备份 & 清空

- **备份**：复制 `backend/data/ai_chat.db`
- **清空**：删除 `backend/data/ai_chat.db`，重启后端自动重建

---

## 七、端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | **1420** | 避开 3000/5173 等常见端口 |
| 后端 | **8176** | 避开 3306/6379/8080/8000/5000 |
| SQLite | **无** | 文件数据库，不占用网络端口 |

不会与 MySQL、PostgreSQL、Redis、Tomcat、Nginx 等开发环境冲突。

---

## 八、常见问题

**Q: ccswitch 切换模型后 Web 端要做什么？**  
A: 打开「API 设置」→ 编辑配置，把 Base URL 和 API Key 改成新模型的对应值即可。ccswitch 负责本地终端切换，Web 端手动同步一下配置。

**Q: 为什么 API Key 显示为 `sk-****xxxx`？**  
A: 安全脱敏。Key 已正确保存，编辑时留空不会覆盖已有 Key。

**Q: 关闭窗口后对话历史还在吗？**  
A: 在。所有数据存储在 SQLite 文件中，持久保存。

**Q: API Key 存在哪？安全吗？**  
A: 明文存储在本地 SQLite 文件中。仅后端使用，前端代码不包含 Key，Key 通过后端代理转发给大模型 API。

**Q: 支持哪些大模型？**  
A: 所有兼容 OpenAI API 格式的模型：DeepSeek、OpenAI、Moonshot、零一万物、通义千问等。

**Q: 端口被占用怎么办？**  
A: 修改 `backend/run.py`（`port=8176`）和 `frontend/vite.config.ts`（`port: 1420`）。

---

## 九、开源许可

MIT License
