"""
后端启动文件
直接在 IDEA / PyCharm 中右键运行此文件即可启动后端服务
启动后访问 http://localhost:8000/docs 查看 API 文档
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
