"""
FastAPI 应用入口
初始化应用、注册路由、配置 CORS 中间件、创建默认管理员
"""

import os
import sys

# 确保 backend 目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import db
from .config import settings
from .routers import auth, knowledge, chat, admin, interact
from .services.auth_service import hash_password

app = FastAPI(
    title="RAG 智能知识问答系统",
    description="基于 RAG（检索增强生成）技术的智能知识问答系统，支持文档上传、知识库管理、混合检索、SSE 流式对话",
    version="2.0.0",
)

# 配置 CORS 中间件，允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(knowledge.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(interact.router)


@app.on_event("startup")
def startup_event():
    """应用启动时初始化"""
    # 创建默认管理员账户（如果不存在），并确保管理员权限
    admin_user = db.get_user_by_username(settings.ADMIN_USERNAME)
    if not admin_user:
        hashed = hash_password(settings.ADMIN_PASSWORD)
        db.create_user(settings.ADMIN_USERNAME, hashed, is_admin=True)
        print(f"[系统] 已创建默认管理员账户: {settings.ADMIN_USERNAME}")
    elif not admin_user.get("is_admin"):
        db.update_user_admin(admin_user["id"], True)
        print(f"[系统] 已恢复默认管理员账户的权限: {settings.ADMIN_USERNAME}")

    # 自动创建测试用户和知识库
    _create_test_data()

    # 创建风格化 Prompt 模板（跳过已存在的）
    existing_templates = db.get_prompt_templates()
    existing_names = {t["name"] for t in existing_templates}

    template_list = [
        {
            "name": "通用助手",
            "description": "准确、有条理、适中，适用于大多数场景",
            "is_default": True,
            "top_k": 4,
            "temperature": 0.3,
            "prompt": """你是一个专业的知识库问答助手。请根据以下参考资料来回答用户的问题。

要求：
1. 仅基于提供的参考资料回答问题，不要编造信息
2. 如果参考资料中没有相关信息，请明确告知用户
3. 回答要准确、简洁、有条理
4. 在回答末尾注明信息来源

参考资料：
{context}""",
        },
        {
            "name": "客服助手",
            "description": "口语化、简洁、友好，适用于超市咨询、学校前台、企业客服等场景",
            "is_default": False,
            "top_k": 3,
            "temperature": 0.5,
            "prompt": """你是一位友好的客服助手，用口语化的方式帮助用户解决问题。

要求：
1. 用亲切、自然的语气回答，像朋友聊天一样
2. 回答要简短，先说结论再补充细节
3. 涉及具体信息（价格、时间、地址）时直接给出
4. 不确定的信息要如实告知，建议联系人工客服
5. 如果用户情绪不好，先安抚再解决问题

参考资料：
{context}""",
        },
        {
            "name": "文档专家",
            "description": "严谨、引用原文、专业，适用于技术文档、政策法规、学术资料等场景",
            "is_default": False,
            "top_k": 6,
            "temperature": 0.2,
            "prompt": """你是一位专业的文档分析专家，帮助用户深入理解文档内容。

要求：
1. 回答要严谨、专业，引用原文关键内容
2. 涉及条款、规范时，逐条列出并解释
3. 涉及技术细节时，用准确的术语描述
4. 如果文档中有矛盾或不清楚的地方，明确指出
5. 在回答中标注引用来源的段落位置

参考资料：
{context}""",
        },
    ]

    created_count = 0
    for t in template_list:
        if t["name"] not in existing_names:
            db.create_prompt_template(
                name=t["name"],
                system_prompt=t["prompt"],
                description=t["description"],
                is_default=t["is_default"],
                default_top_k=t["top_k"],
                default_temperature=t["temperature"],
            )
            created_count += 1

    if created_count > 0:
        print(f"[系统] 新增 {created_count} 个风格化 Prompt 模板")


@app.get("/")
def root():
    """系统根路径，返回系统基本信息"""
    return {
        "name": "RAG 智能知识问答系统",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


def _create_test_data():
    """自动创建测试用户和知识库"""
    # 测试用户
    test_users = [
        ("admin1", "user123", False),
        ("zhangsan", "user123", False),
        ("lisi", "user123", False),
        ("wangwu", "user123", False),
        ("一只鱼", "user123", False),
        ("两只鱼", "user123", False),
    ]

    user_ids = {}
    for username, password, is_admin in test_users:
        user = db.get_user_by_username(username)
        if not user:
            hashed = hash_password(password)
            uid = db.create_user(username, hashed, is_admin)
            user_ids[username] = uid
        else:
            user_ids[username] = user["id"]

    # 获取管理员ID
    admin_user = db.get_user_by_username("admin")
    if admin_user:
        user_ids["admin"] = admin_user["id"]

    # 检查是否已有测试知识库
    existing_kbs = db.get_all_knowledge_bases()
    if len(existing_kbs) >= 3:
        return  # 已有数据，跳过

    # 测试知识库
    test_kbs = [
        {"name": "Python编程核心技术", "desc": "Python语言核心技术文档", "owner": "admin", "vis": "public"},
        {"name": "JavaScript前端开发", "desc": "JavaScript语言核心知识", "owner": "zhangsan", "vis": "public"},
        {"name": "机器学习入门教程", "desc": "从零开始学习机器学习", "owner": "admin", "vis": "public"},
        {"name": "Web开发全栈教程", "desc": "从前端到后端的Web开发教程", "owner": "zhangsan", "vis": "public"},
        {"name": "数据库技术大全", "desc": "关系型和非关系型数据库技术", "owner": "lisi", "vis": "private"},
        {"name": "项目管理知识体系", "desc": "项目管理方法论和最佳实践", "owner": "lisi", "vis": "shared", "share_with": ["zhangsan"]},
        {"name": "个人学习笔记", "desc": "日常学习积累的知识点", "owner": "wangwu", "vis": "private"},
        {"name": "人工智能前沿技术", "desc": "AI领域最新技术动态", "owner": "admin", "vis": "private"},
    ]

    for kb_info in test_kbs:
        owner = kb_info["owner"]
        owner_id = user_ids.get(owner)
        if not owner_id:
            continue

        # 检查知识库是否已存在
        owner_kbs = db.get_knowledge_bases_by_user(owner_id)
        if any(kb["name"] == kb_info["name"] for kb in owner_kbs):
            continue

        kb_id = db.create_knowledge_base(kb_info["name"], kb_info["desc"], owner_id)

        # 设置可见性
        vis = kb_info.get("vis", "private")
        if vis != "private":
            db.update_kb_visibility(kb_id, vis)

        # 公开的需要审核通过
        if vis == "public":
            db.update_kb_visibility(kb_id, "public")

        # 分享给用户
        if vis == "shared" and "share_with" in kb_info:
            for share_user in kb_info["share_with"]:
                share_user_id = user_ids.get(share_user)
                if share_user_id:
                    db.share_knowledge_base(kb_id, share_user_id, owner_id)

    print(f"[系统] 已创建测试数据：{len(test_users)} 个用户，{len(test_kbs)} 个知识库")


@app.get("/health")
def health_check():
    """健康检查接口"""
    return {"status": "ok"}


# 生产环境：服务前端静态文件
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA 路由兜底：非 API 路径一律返回 index.html"""
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
