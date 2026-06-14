import os
import sys
import uvicorn

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

port = int(os.environ.get("PORT", 8000))

uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=port,
)
