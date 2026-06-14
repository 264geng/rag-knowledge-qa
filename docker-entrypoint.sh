#!/bin/bash
cd /app/backend

# 启动uvicorn到后台
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# 等待服务启动
echo "等待服务启动..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/auth/me > /dev/null 2>&1; then
        echo "服务已启动"
        break
    fi
    sleep 1
done

# 填充测试数据（首次部署时）
echo "正在初始化测试数据..."
python create_test_data.py || echo "测试数据可能已存在，跳过"

# 等待后台进程
wait $SERVER_PID
