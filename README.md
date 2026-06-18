# AI Chat Web — Claude Code 可视化聊天界面

将 Claude Code CLI 终端交互替换为现代化的 Web 聊天界面，保留 Claude Code 全部能力（文件读写、代码生成、工具调用等），通过 ccswitch 使用 DeepSeek v4-pro 模型。

---

## 架构

```
浏览器 (Vue 3) ──HTTP/SSE──▶ FastAPI ──spawn──▶ Claude Code CLI ──ccswitch──▶ DeepSeek v4-pro
                                   │
                                   ▼
                              SQLite 历史记录
```

**核心设计**：Web 端不直接调用大模型 API，而是启动 Claude Code CLI 子进程。Claude Code 负责所有 AI 能力，Web 端只是交互层。

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Claude Code CLI 已安装
- ccswitch 已配置

### 安装

```bash
cd AI-agent

# 后端
cd backend
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

### 启动

```bash
# Windows: 双击 start.bat
# 或手动分别启动：

# 终端 1 — 后端 (端口 8176)
cd backend
python run.py

# 终端 2 — 前端 (端口 1420)
cd frontend
npm run dev
```

浏览器打开 **http://localhost:1420**

### API 配置

本项目通过 Claude Code CLI + ccswitch 工作，**无需在 Web 端配置 API**。ccswitch 切换模型后重启 Backend 即可自动跟随。

---

## 功能

| 功能 | 说明 |
|------|------|
| 流式对话 | SSE 逐字输出，打字机效果 |
| 对话管理 | 新建、切换、删除、标签分组、筛选 |
| Markdown 渲染 | 代码高亮、表格、引用 |
| 深色主题 | 现代化暗色 UI，侧边栏和输入框可拖拽缩放 |
| 历史持久化 | SQLite 单文件存储，关闭后数据不丢失 |

---

## 目录结构

```
AI-agent/
├── frontend/               # Vue 3 + Vite + Ant Design Vue
│   ├── src/
│   │   ├── components/     # Sidebar / ChatWindow / MessageBubble
│   │   ├── views/          # ChatView
│   │   ├── stores/         # Pinia
│   │   ├── api/            # HTTP + SSE 封装
│   │   └── router/
│   └── package.json
├── backend/                # Python FastAPI
│   ├── app/
│   │   ├── main.py         # 入口 + CORS + 事件循环
│   │   ├── database.py     # SQLAlchemy + aiosqlite
│   │   ├── models.py       # Conversation / Message
│   │   ├── schemas.py      # Pydantic
│   │   ├── routers/        # chat / conversations / context
│   │   └── services/       # llm (Claude Code CLI 调用)
│   ├── data/               # SQLite 数据库 (gitignore)
│   ├── requirements.txt
│   └── run.py
├── start.bat               # Windows 一键启动
├── start.sh                # Linux/macOS 一键启动
└── .gitignore
```

---

## 端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 1420 | 避开 3000/5173 等常见端口 |
| 后端 | 8176 | 避开 3306/6379/8080/8000/5000 |
| SQLite | 无 | 文件数据库，不占用网络端口 |

---

## 数据管理

数据库文件：`backend/data/ai_chat.db`

- **备份**：复制该文件
- **清空**：删除该文件，重启自动重建
- **查看**：VS Code 安装 `SQLite Viewer` 插件双击打开

---

## 分享给他人

对方 clone 后：

```bash
cd AI-agent
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
# 双击 start.bat
```

对方需要有自己的 Claude Code + ccswitch 配置，Web 端自动读取环境变量。

---

## 常见问题

**Q: 切换 ccswitch 模型后 Web 端要做什么？**
A: 重启 Backend 即可，环境变量会自动跟随。

**Q: API Key 存在哪？**
A: 由 ccswitch 管理，Web 端不存储任何 API Key。

**Q: 对话历史在哪？**
A: `backend/data/ai_chat.db`，SQLite 单文件。

**Q: 支持哪些大模型？**
A: ccswitch 支持的任何模型都可使用。

---

## 许可

MIT License
