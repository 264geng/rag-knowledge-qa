# RAG 智能知识问答系统

基于 RAG（Retrieval-Augmented Generation，检索增强生成）技术的智能知识问答系统。用户可以上传文档建立知识库，系统基于混合检索（向量检索 + BM25）准确回答问题，支持 SSE 流式输出、多知识库问答、风格化 Prompt 模板等特性。

## 测试账号

系统启动后自动创建以下测试账号：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| admin1 | user123 | 普通用户 |
| zhangsan | user123 | 普通用户 |
| lisi | user123 | 普通用户 |
| wangwu | user123 | 普通用户 |
| 一只鱼 | user123 | 普通用户 |
| 两只鱼 | user123 | 普通用户 |

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/264geng/rag-knowledge-qa.git
cd rag-knowledge-qa
```

### 2. 一键启动（推荐）

**Windows**：双击 `start_all.bat`

**Mac/Linux**：
```bash
python run.py
```

### 3. 访问系统

- 前端地址：http://localhost:5173
- API 文档：http://localhost:8000/docs

### 4. 登录测试

使用测试账号登录，系统会自动创建 7 个用户和 14 个知识库。

## 项目结构

```
rag-knowledge-qa/
├── backend/                        # FastAPI 后端
│   ├── .env                        # 环境变量配置（已包含API密钥）
│   ├── requirements.txt            # Python 依赖
│   ├── run.py                      # 后端启动脚本
│   └── app/
│       ├── main.py                 # FastAPI 入口（含自动初始化）
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
├── data/                           # 运行时数据（自动生成）
├── run.py                          # 一键启动脚本
├── start_all.bat                   # Windows 启动脚本
├── stop_all.bat                    # Windows 停止脚本
└── 课程报告/                       # 课程报告文档
```

## 环境要求

- Python 3.9+
- Node.js 16+

## 功能特性

- **混合检索**：向量语义检索 + BM25 关键词检索，可配置权重
- **SSE 流式输出**：实时流式返回回答，提升交互体验
- **多知识库问答**：单次对话支持跨多个知识库检索
- **风格化 Prompt 模板**：内置通用助手、客服助手、文档专家等模板
- **知识库分享**：用户间共享知识库，支持查看分享者
- **内容审核**：管理员审核公开申请、处理举报
- **管理后台**：用户管理、系统统计、操作日志
- **多格式文档**：支持 PDF、TXT、Markdown、DOCX、XLSX、PPTX、HTML、CSV

## 技术架构

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| LLM | DeepSeek |
| Embedding | 火山方舟 API |
| 向量数据库 | ChromaDB |
| 混合检索 | BM25 + 向量检索 |
| RAG 框架 | LangChain |
| 前端框架 | Vue.js 3 + Element Plus |
| 构建工具 | Vite |
| 数据库 | SQLite |
| 用户认证 | JWT |

## 使用流程

1. **登录系统** → 使用测试账号登录
2. **知识库管理** → 查看、创建、编辑知识库
3. **文档管理** → 上传文档到知识库
4. **智能问答** → 选择知识库进行问答
5. **管理后台** → 用户管理、审核、日志查看

## 课程报告

课程报告文档位于 `课程报告/` 目录下。

## 许可证

MIT License
