"""
一键启动脚本
自动启动后端和前端服务
在 IDEA 中直接运行此文件即可
"""

import subprocess
import sys
import os
import time

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")


def main():
    print("=" * 50)
    print("  RAG 智能知识问答系统 - 一键启动")
    print("=" * 50)
    print()

    # 启动后端
    print("[1/2] 启动后端服务 (FastAPI) ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=BACKEND_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )
    print("      后端地址: http://localhost:8000")
    print("      API 文档: http://localhost:8000/docs")
    print()

    # 等待后端启动
    time.sleep(3)

    # 启动前端
    print("[2/2] 启动前端服务 (Vite) ...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=FRONTEND_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )
    print("      前端地址: http://localhost:5173")
    print()
    print("=" * 50)
    print("  两个服务已在新窗口中启动")
    print("  关闭对应窗口即可停止对应服务")
    print("=" * 50)

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        backend_proc.terminate()
        frontend_proc.terminate()


if __name__ == "__main__":
    main()
