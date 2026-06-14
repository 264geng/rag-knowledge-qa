# RAG 智能知识问答系统

基于 RAG（Retrieval-Augmented Generation，检索增强生成）技术的智能知识问答系统。用户可以上传文档建立知识库，系统基于混合检索（向量检索 + BM25）准确回答问题，支持 SSE 流式输出、多知识库问答、风格化 Prompt 模板等特性。

## 项目结构

```
rag-knowledge-qa/
├── backend/                        # FastAPI 后端
│   ├── .env                        # 环境变量配置
│   ├── .env.example                # 环境变量模板
│   ├── requirements.txt            # Python 依赖
│   ├── run.py                      # 后端启动脚本
│   └── app/
│       ├── main.py                 # FastAPI 入口
│       ├── config.py               # 配置管理
│       ├── database.py             # SQLite 数据库
│       ├── models/
│       │   └── schemas.py          # 数据模型
│       ├── routers/
│       │   ├── auth.py             # 认证路由
│       │   ├── knowledge.py        # 知识库路由
│       │   ├── chat.py             # 对话路由（SSE 流式 + 同步）
│       │   ├── admin.py            # 管理后台路由
│       │   └── interact.py         # 互动路由（分享/点赞/举报/收藏）
│       └── services/
│           ├── auth_service.py     # 认证服务
│           ├── document_parser.py  # 文档解析
│           ├── vector_store.py     # 向量存储 + 混合检索
│           ├── rag_engine.py       # RAG 引擎
│           └── logger_service.py   # 操作日志服务
├── frontend/                       # Vue.js 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── api/index.js            # API 层
│       ├── router/index.js         # 路由
│       └── views/
│           ├── Login.vue           # 登录页
│           ├── Layout.vue          # 布局
│           ├── Chat.vue            # 智能问答
│           ├── Documents.vue       # 文档管理
│           ├── KnowledgeBases.vue  # 知识库管理
│           ├── UserSettings.vue    # 个人设置
│           ├── ContentReview.vue   # 内容审核
│           └── Admin.vue           # 管理后台
├── data/                           # 运行时数据
├── run.py                          # 一键启动脚本（Python）
├── start_all.bat                   # 一键启动脚本（Windows）
└── stop_all.bat                    # 一键停止脚本（Windows）
```

## 环境要求

- Python 3.9+
- Node.js 16+
- OpenAI API Key（或兼容的 API 服务）

## 安装与运行

### 1. 克隆项目

```bash
cd rag-knowledge-qa
```

### 2. 后端

```bash
# 创建 Python 虚拟环境
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，填入你的 OpenAI API Key
# OPENAI_API_KEY=sk-your-api-key-here
```

启动后端：

```bash
python -m uvicorn app.main:app --reload --port 8000
```

后端启动后访问 http://localhost:8000/docs 查看 API 文档。

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

前端启动后访问 http://localhost:5173。

### 4. 一键启动（推荐）

Windows 用户可直接双击 `start_all.bat` 一键启动前后端服务，`stop_all.bat` 停止服务。

也可以运行 Python 一键启动脚本：

```bash
python run.py
```

## 使用流程

1. **注册账号** → 在登录页面点击"注册"标签创建新账号
2. **登录系统** → 使用账号密码登录（默认管理员：`admin / admin123`）
3. **创建知识库** → 点击侧边栏"知识库管理"，创建一个新的知识库
4. **上传文档** → 点击"文档管理"，选择知识库后上传文档
5. **开始问答** → 点击"智能问答"，选择知识库后在聊天框输入问题
6. **个人设置** → 修改 Prompt 模板、调整检索参数
7. **互动功能** → 知识库分享、点赞/踩、文档举报、收藏

## 功能特性

- **混合检索**：向量语义检索 + BM25 关键词检索，可配置权重，提升召回率
- **Query 改写**：自动优化用户查询，提升检索效果
- **Rerank 重排序**：支持 Cross-Encoder 模型对检索结果重排序（可选）
- **SSE 流式输出**：实时流式返回回答，提升交互体验
- **多知识库问答**：单次对话支持跨多个知识库检索
- **风格化 Prompt 模板**：内置通用助手、客服助手、文档专家等模板
- **对话管理**：对话历史、自动标题、消息反馈（点赞/踩）
- **知识库分享**：用户间共享知识库
- **文档收藏与举报**：支持收藏文档、举报不当内容
- **管理后台**：用户管理、系统统计、操作日志查看
- **操作日志**：自动记录关键操作，便于审计
- **多格式文档**：支持 PDF、TXT、Markdown、DOCX、XLSX、PPTX、HTML、CSV

## 技术架构

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| LLM | OpenAI GPT-3.5-turbo（可自定义） |
| Embedding | OpenAI text-embedding-3-small / HuggingFace（可切换） |
| 向量数据库 | ChromaDB |
| 混合检索 | BM25 + 向量检索（rank_bm25） |
| RAG 框架 | LangChain |
| 前端框架 | Vue.js 3 + Element Plus |
| 构建工具 | Vite 8 |
| 流式输出 | SSE（sse-starlette） |
| 数据库 | SQLite |
| 用户认证 | JWT |
| 中文分词 | jieba |
