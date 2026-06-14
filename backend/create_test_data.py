"""
测试数据生成脚本
创建不同格式、不同大小的知识库和文档
支持三种提示词模板场景：
1. 技术文档问答
2. 学习教程问答
3. 通用知识问答
"""

import requests
import json
import os
import tempfile
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000/api"

# 测试用户
TEST_USERS = [
    {"username": "admin", "password": "admin123", "is_admin": True},
    {"username": "zhangsan", "password": "user123", "is_admin": False},
    {"username": "lisi", "password": "user123", "is_admin": False},
    {"username": "wangwu", "password": "user123", "is_admin": False},
]

# 技术文档类知识库模板
TECH_KNOWLEDGE_BASES = [
    {
        "name": "Python编程核心技术",
        "description": "Python语言核心技术文档，涵盖基础语法、高级特性、最佳实践",
        "visibility": "public",
        "owner": "admin",
        "template": "技术文档",
        "documents": [
            {
                "filename": "Python基础语法详解.txt",
                "content": """Python基础语法详解

一、变量和数据类型
Python是动态类型语言，变量无需声明即可使用。

1. 基本数据类型：
   - int: 整数，如 42, -10, 0
   - float: 浮点数，如 3.14, -0.5
   - str: 字符串，如 "hello", 'world'
   - bool: 布尔值，True 或 False
   - None: 空值

2. 变量命名规则：
   - 以字母或下划线开头
   - 区分大小写
   - 不能使用保留字

二、控制流语句
1. 条件语句：
   if condition:
       # code
   elif another_condition:
       # code
   else:
       # code

2. 循环语句：
   for item in iterable:
       # code

   while condition:
       # code

三、函数定义
def function_name(parameters):
    '''文档字符串'''
    # function body
    return result

四、类和面向对象
class MyClass:
    def __init__(self, value):
        self.value = value

    def method(self):
        return self.value * 2
"""
            },
            {
                "filename": "Python高级特性.md",
                "content": """# Python高级特性

## 1. 装饰器（Decorator）

装饰器是一种设计模式，用于在不修改原函数代码的情况下扩展函数功能。

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("函数调用前")
        result = func(*args, **kwargs)
        print("函数调用后")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")
```

## 2. 生成器（Generator）

生成器是一种特殊的迭代器，使用yield关键字。

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b
```

## 3. 上下文管理器

使用with语句管理资源。

```python
with open('file.txt', 'r') as f:
    content = f.read()
```

## 4. 类型注解

Python 3.5+支持类型注解。

```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```
"""
            },
            {
                "filename": "Python异常处理.txt",
                "content": """Python异常处理指南

一、异常处理基础
使用try-except语句捕获和处理异常。

try:
    # 可能引发异常的代码
    result = 10 / 0
except ZeroDivisionError:
    print("除零错误")
except Exception as e:
    print(f"其他错误: {e}")
else:
    print("没有异常时执行")
finally:
    print("总是执行")

二、常见内置异常
1. ValueError: 值错误
2. TypeError: 类型错误
3. KeyError: 字典键错误
4. IndexError: 索引越界
5. FileNotFoundError: 文件未找到
6. AttributeError: 属性错误

三、自定义异常
class CustomError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

四、异常链
try:
    # some code
except Exception as e:
    raise RuntimeError("新错误") from e

五、最佳实践
1. 捕获具体的异常类型
2. 不要捕获所有异常
3. 记录异常信息
4. 适当使用finally清理资源
"""
            }
        ]
    },
    {
        "name": "JavaScript前端开发",
        "description": "JavaScript语言核心知识和前端开发技术",
        "visibility": "public",
        "owner": "zhangsan",
        "template": "技术文档",
        "documents": [
            {
                "filename": "ES6+新特性.txt",
                "content": """ES6+新特性详解

一、let和const
1. let: 块级作用域变量
2. const: 常量声明

二、箭头函数
const add = (a, b) => a + b;

三、模板字符串
const name = 'World';
const greeting = `Hello, ${name}!`;

四、解构赋值
const { name, age } = person;
const [first, second] = array;

五、Promise
const promise = new Promise((resolve, reject) => {
    // async operation
});

六、async/await
async function fetchData() {
    const response = await fetch(url);
    const data = await response.json();
    return data;
}

七、类
class Person {
    constructor(name) {
        this.name = name;
    }

    greet() {
        return `Hello, ${this.name}`;
    }
}

八、模块
export const helper = () => {};
import { helper } from './module';
"""
            },
            {
                "filename": "Vue3框架入门.md",
                "content": """# Vue3框架入门

## 1. 组合式API

Vue3引入了组合式API，提供更灵活的代码组织方式。

```javascript
import { ref, computed, onMounted } from 'vue'

export default {
    setup() {
        const count = ref(0)
        const doubleCount = computed(() => count.value * 2)

        onMounted(() => {
            console.log('组件已挂载')
        })

        return { count, doubleCount }
    }
}
```

## 2. 响应式系统

- ref: 基本类型的响应式
- reactive: 对象的响应式
- computed: 计算属性
- watch: 侦听器

## 3. 生命周期

- onMounted
- onUpdated
- onUnmounted

## 4. 组件通信

- props
- emit
- provide/inject
- Pinia状态管理
"""
            }
        ]
    },
    {
        "name": "数据库技术大全",
        "description": "关系型和非关系型数据库技术文档",
        "visibility": "pending",
        "owner": "lisi",
        "template": "技术文档",
        "documents": [
            {
                "filename": "MySQL性能优化.txt",
                "content": """MySQL性能优化指南

一、索引优化
1. 创建合适的索引
   - 主键索引
   - 唯一索引
   - 普通索引
   - 组合索引

2. 索引使用原则
   - 最左前缀原则
   - 避免索引失效
   - 控制索引数量

二、查询优化
1. 使用EXPLAIN分析查询
2. 避免SELECT *
3. 合理使用JOIN
4. 子查询优化

三、表结构优化
1. 选择合适的数据类型
2. 范式化设计
3. 适当反范式化

四、配置优化
1. innodb_buffer_pool_size
2. max_connections
3. query_cache_size

五、慢查询分析
1. 开启慢查询日志
2. 分析慢查询
3. 优化慢查询
"""
            },
            {
                "filename": "MongoDB入门教程.md",
                "content": """# MongoDB入门教程

## 1. 基本概念

MongoDB是一个基于分布式文件存储的NoSQL数据库。

- 数据库（Database）
- 集合（Collection）
- 文档（Document）

## 2. CRUD操作

### 创建
```javascript
db.users.insertOne({name: "张三", age: 25})
db.users.insertMany([{name: "李四"}, {name: "王五"}])
```

### 查询
```javascript
db.users.find({age: {$gt: 20}})
db.users.findOne({name: "张三"})
```

### 更新
```javascript
db.users.updateOne(
    {name: "张三"},
    {$set: {age: 26}}
)
```

### 删除
```javascript
db.users.deleteOne({name: "张三"})
```

## 3. 索引
```javascript
db.users.createIndex({name: 1})
```

## 4. 聚合
```javascript
db.orders.aggregate([
    {$match: {status: "completed"}},
    {$group: {_id: "$userId", total: {$sum: "$amount"}}}
])
```
"""
            }
        ]
    }
]

# 学习教程类知识库模板
TUTORIAL_KNOWLEDGE_BASES = [
    {
        "name": "机器学习入门教程",
        "description": "从零开始学习机器学习，包含理论和实践",
        "visibility": "public",
        "owner": "admin",
        "template": "学习教程",
        "documents": [
            {
                "filename": "机器学习基础概念.txt",
                "content": """机器学习基础概念

一、什么是机器学习
机器学习是人工智能的一个分支，它让计算机能够从数据中学习，
而无需显式编程。

二、机器学习的类型
1. 监督学习
   - 分类：预测离散标签
   - 回归：预测连续值

2. 无监督学习
   - 聚类：将数据分组
   - 降维：减少特征数量

3. 强化学习
   - 通过与环境交互学习

三、基本流程
1. 数据收集
2. 数据预处理
3. 特征工程
4. 模型选择
5. 模型训练
6. 模型评估
7. 模型部署

四、常见算法
1. 线性回归
2. 逻辑回归
3. 决策树
4. 随机森林
5. 支持向量机
6. 神经网络
"""
            },
            {
                "filename": "Python机器学习实战.md",
                "content": """# Python机器学习实战

## 1. 环境准备

```bash
pip install numpy pandas scikit-learn matplotlib
```

## 2. 数据预处理

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 加载数据
data = pd.read_csv('data.csv')

# 分割特征和标签
X = data.drop('target', axis=1)
y = data['target']

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 特征标准化
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

## 3. 模型训练

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# 训练模型
model = LogisticRegression()
model.fit(X_train_scaled, y_train)

# 预测
y_pred = model.predict(X_test_scaled)

# 评估
accuracy = accuracy_score(y_test, y_pred)
print(f"准确率: {accuracy:.2f}")
```

## 4. 模型保存

```python
import joblib
joblib.dump(model, 'model.pkl')
```
"""
            }
        ]
    },
    {
        "name": "Web开发全栈教程",
        "description": "从前端到后端的完整Web开发教程",
        "visibility": "public",
        "owner": "zhangsan",
        "template": "学习教程",
        "documents": [
            {
                "filename": "HTML和CSS基础.txt",
                "content": """HTML和CSS基础教程

一、HTML基础
1. HTML文档结构
<!DOCTYPE html>
<html>
<head>
    <title>标题</title>
</head>
<body>
    <h1>一级标题</h1>
    <p>段落</p>
</body>
</html>

2. 常用标签
- 标题：h1-h6
- 段落：p
- 链接：a
- 图片：img
- 列表：ul, ol, li
- 表格：table, tr, td
- 表单：form, input, button

二、CSS基础
1. 选择器
- 元素选择器：p { }
- 类选择器：.class { }
- ID选择器：#id { }

2. 盒模型
- content
- padding
- border
- margin

3. 布局
- Flexbox
- Grid

4. 响应式设计
@media (max-width: 768px) {
    /* 移动端样式 */
}
"""
            },
            {
                "filename": "Node.js后端开发.md",
                "content": """# Node.js后端开发

## 1. Express框架

```javascript
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.json({ message: 'Hello World' });
});

app.listen(3000, () => {
    console.log('服务器运行在端口3000');
});
```

## 2. 路由处理

```javascript
// GET请求
app.get('/api/users', (req, res) => {
    // 获取用户列表
});

// POST请求
app.post('/api/users', (req, res) => {
    // 创建用户
});

// PUT请求
app.put('/api/users/:id', (req, res) => {
    // 更新用户
});

// DELETE请求
app.delete('/api/users/:id', (req, res) => {
    // 删除用户
});
```

## 3. 中间件

```javascript
// 日志中间件
app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// 错误处理中间件
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});
```

## 4. 数据库连接

```javascript
const mongoose = require('mongoose');

mongoose.connect('mongodb://localhost/mydb', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});
```
"""
            }
        ]
    }
]

# 通用知识类知识库模板
GENERAL_KNOWLEDGE_BASES = [
    {
        "name": "项目管理知识体系",
        "description": "项目管理方法论和最佳实践",
        "visibility": "shared",
        "owner": "lisi",
        "template": "通用知识",
        "shared_with": ["zhangsan"],
        "documents": [
            {
                "filename": "敏捷开发Scrum指南.txt",
                "content": """敏捷开发Scrum指南

一、Scrum概述
Scrum是一个用于开发和维护复杂产品的框架。
它基于经验过程控制理论，强调透明性、检视和适应。

二、Scrum角色
1. 产品负责人（Product Owner）
   - 管理产品待办事项
   - 确保团队交付最大价值

2. Scrum Master
   - 确保团队遵循Scrum
   - 移除障碍
   - 促进团队协作

3. 开发团队
   - 自组织
   - 跨职能
   - 交付可工作的软件

三、Scrum事件
1. Sprint：固定时间周期（1-4周）
2. Sprint计划会：确定Sprint目标
3. 每日站会：15分钟同步会议
4. Sprint评审会：展示完成的工作
5. Sprint回顾会：改进过程

四、Scrum工件
1. 产品待办事项（Product Backlog）
2. Sprint待办事项（Sprint Backlog）
3. 增量（Increment）
"""
            },
            {
                "filename": "项目风险管理.md",
                "content": """# 项目风险管理

## 1. 风险识别

### 常见风险类型
- 技术风险
- 进度风险
- 人员风险
- 外部风险

### 识别方法
- 头脑风暴
- 检查表分析
- SWOT分析
- 专家访谈

## 2. 风险评估

### 定性分析
- 概率评估
- 影响评估
- 风险等级划分

### 定量分析
- 期望货币值分析
- 蒙特卡洛模拟
- 决策树分析

## 3. 风险应对策略

### 负面风险（威胁）
- 规避：消除风险
- 转移：转嫁给第三方
- 减轻：降低概率或影响
- 接受：制定应急计划

### 正面风险（机会）
- 开拓：确保机会实现
- 分享：与第三方共享
- 提高：增加概率或影响
- 接受：不主动追求

## 4. 风险监控
- 风险审计
- 偏差分析
- 技术绩效测量
- 储备分析
"""
            }
        ]
    },
    {
        "name": "个人学习笔记",
        "description": "日常学习过程中积累的知识点",
        "visibility": "private",
        "owner": "wangwu",
        "template": "通用知识",
        "documents": [
            {
                "filename": "Git常用命令.txt",
                "content": """Git常用命令速查

一、基础配置
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

二、仓库操作
git init                    # 初始化仓库
git clone <url>            # 克隆仓库

三、文件操作
git add <file>             # 添加文件到暂存区
git add .                  # 添加所有文件
git commit -m "message"    # 提交更改
git status                 # 查看状态
git diff                   # 查看差异

四、分支操作
git branch                 # 查看分支
git branch <name>          # 创建分支
git checkout <branch>      # 切换分支
git checkout -b <name>     # 创建并切换分支
git merge <branch>         # 合并分支
git branch -d <branch>     # 删除分支

五、远程操作
git remote add origin <url>  # 添加远程仓库
git push origin <branch>     # 推送到远程
git pull                     # 拉取远程更新
git fetch                    # 获取远程更新

六、撤销操作
git reset --soft HEAD~1    # 撤销提交，保留更改
git reset --hard HEAD~1    # 撤销提交，丢弃更改
git revert <commit>        # 反转提交

七、标签操作
git tag <name>             # 创建标签
git tag -a <name> -m "msg" # 创建带注释的标签
git push origin --tags     # 推送标签到远程
"""
            },
            {
                "filename": "Docker入门指南.md",
                "content": """# Docker入门指南

## 1. 基本概念

- 镜像（Image）：只读模板
- 容器（Container）：镜像的运行实例
- 仓库（Repository）：存储镜像的地方

## 2. 常用命令

### 镜像操作
```bash
docker images              # 列出镜像
docker pull <image>        # 拉取镜像
docker rmi <image>         # 删除镜像
docker build -t <name> .   # 构建镜像
```

### 容器操作
```bash
docker run -d -p 80:80 <image>  # 运行容器
docker ps                       # 查看运行中的容器
docker ps -a                    # 查看所有容器
docker stop <container>         # 停止容器
docker rm <container>           # 删除容器
docker logs <container>         # 查看日志
docker exec -it <container> bash # 进入容器
```

## 3. Dockerfile

```dockerfile
FROM node:14
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "app.js"]
```

## 4. Docker Compose

```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "3000:3000"
  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: password
```
"""
            }
        ]
    },
    {
        "name": "人工智能前沿技术",
        "description": "AI领域最新技术动态和研究成果",
        "visibility": "pending",
        "owner": "admin",
        "template": "通用知识",
        "documents": [
            {
                "filename": "大语言模型概述.txt",
                "content": """大语言模型概述

一、什么是大语言模型
大语言模型（LLM）是基于深度学习的自然语言处理模型，
通常包含数十亿甚至数万亿参数。

二、代表性模型
1. GPT系列（OpenAI）
   - GPT-3: 1750亿参数
   - GPT-4: 多模态模型

2. BERT系列（Google）
   - BERT: 双向编码器
   - T5: 文本到文本转换

3. LLaMA系列（Meta）
   - 开源大语言模型
   - 多种规模版本

三、关键技术
1. Transformer架构
2. 自注意力机制
3. 预训练+微调范式
4. 提示工程（Prompt Engineering）

四、应用场景
1. 文本生成
2. 问答系统
3. 代码生成
4. 翻译
5. 摘要生成

五、挑战与限制
1. 计算资源需求大
2. 幻觉问题
3. 安全性和伦理问题
4. 可解释性不足
"""
            }
        ]
    }
]


def login(username, password):
    """登录获取token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"  ✗ 登录失败: {response.text}")
        return None


def create_user(username, password, is_admin=False):
    """创建用户"""
    response = requests.post(f"{BASE_URL}/auth/register", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        print(f"  ✓ 用户 {username} 创建成功")
        return True
    elif "already exists" in response.text:
        print(f"  - 用户 {username} 已存在")
        return True
    else:
        print(f"  ✗ 创建用户 {username} 失败: {response.text}")
        return False


def create_knowledge_base(token, name, description):
    """创建知识库"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/knowledge-base", json={
        "name": name,
        "description": description
    }, headers=headers)
    if response.status_code == 200:
        kb_id = response.json().get("id")
        print(f"    ✓ 知识库创建成功 (ID: {kb_id})")
        return kb_id
    else:
        print(f"    ✗ 创建知识库失败: {response.text}")
        return None


def upload_document(token, kb_id, filename, content):
    """上传文档"""
    headers = {"Authorization": f"Bearer {token}"}

    # 根据文件扩展名确定后缀
    suffix = '.txt'
    if filename.endswith('.md'):
        suffix = '.md'

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name

    try:
        with open(temp_path, 'rb') as f:
            files = {'file': (filename, f)}
            response = requests.post(
                f"{BASE_URL}/knowledge-base/{kb_id}/documents",
                files=files,
                headers=headers
            )
        if response.status_code == 200:
            print(f"      ✓ {filename}")
            return True
        else:
            print(f"      ✗ {filename}: {response.text}")
            return False
    finally:
        os.unlink(temp_path)


def set_visibility(token, kb_id, visibility):
    """设置知识库可见性"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.put(
        f"{BASE_URL}/interact/knowledge-base/{kb_id}/visibility",
        json={"visibility": visibility},
        headers=headers
    )
    if response.status_code == 200:
        return True
    else:
        print(f"    ✗ 设置可见性失败: {response.text}")
        return False


def approve_knowledge_base(admin_token, kb_id):
    """管理员审核通过知识库"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.put(
        f"{BASE_URL}/admin/review/knowledge-bases/{kb_id}/approve",
        headers=headers
    )
    return response.status_code == 200


def share_knowledge_base(token, kb_id, user_id):
    """分享知识库给用户"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/interact/knowledge-base/{kb_id}/share",
        json={"user_id": user_id},
        headers=headers
    )
    return response.status_code == 200


def get_user_info(token):
    """获取用户信息"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None


def create_prompt_templates(token):
    """创建提示词模板"""
    headers = {"Authorization": f"Bearer {token}"}

    templates = [
        {
            "name": "技术文档问答",
            "description": "适用于技术文档、API文档、代码说明等场景",
            "system_prompt": "你是一个专业的技术文档问答助手。请根据以下技术文档来回答用户的问题。\n\n要求：\n1. 准确理解技术概念，使用专业术语\n2. 提供清晰的解释和示例代码\n3. 如果涉及代码，请给出完整的代码示例\n4. 引用文档中的具体内容作为依据\n\n参考资料：\n{context}",
            "default_top_k": 5,
            "default_temperature": 0.2
        },
        {
            "name": "学习教程问答",
            "description": "适用于教程、课程、学习资料等场景",
            "system_prompt": "你是一个耐心的学习辅导助手。请根据以下学习资料来回答用户的问题。\n\n要求：\n1. 使用通俗易懂的语言解释概念\n2. 提供循序渐进的讲解\n3. 给出实际的例子和类比\n4. 鼓励用户思考和实践\n\n学习资料：\n{context}",
            "default_top_k": 4,
            "default_temperature": 0.4
        },
        {
            "name": "通用知识问答",
            "description": "适用于各类知识库的通用问答场景",
            "system_prompt": "你是一个知识库问答助手。请根据以下参考资料来回答用户的问题。\n\n要求：\n1. 仅基于提供的参考资料回答问题\n2. 如果参考资料中没有相关信息，请明确告知\n3. 回答要准确、简洁、有条理\n4. 在回答末尾注明信息来源\n\n参考资料：\n{context}",
            "default_top_k": 4,
            "default_temperature": 0.3
        }
    ]

    print("\n[创建提示词模板]")
    for tmpl in templates:
        response = requests.post(f"{BASE_URL}/prompt-templates", json=tmpl, headers=headers)
        if response.status_code == 200:
            print(f"  ✓ 模板 '{tmpl['name']}' 创建成功")
        else:
            print(f"  - 模板 '{tmpl['name']}' 可能已存在")


def process_knowledge_bases(kb_list, tokens, user_ids, admin_token, kb_type):
    """处理知识库列表"""
    created_count = 0

    for kb_info in kb_list:
        owner = kb_info["owner"]
        owner_token = tokens.get(owner)
        if not owner_token:
            print(f"  ✗ 用户 {owner} 未登录，跳过")
            continue

        print(f"\n  📚 {kb_info['name']}")
        print(f"     所有者: {owner} | 类型: {kb_info.get('template', '未知')}")

        # 创建知识库
        kb_id = create_knowledge_base(owner_token, kb_info["name"], kb_info["description"])
        if not kb_id:
            continue

        # 上传文档
        print(f"     上传文档:")
        for doc in kb_info["documents"]:
            upload_document(owner_token, kb_id, doc["filename"], doc["content"])

        # 设置可见性
        visibility = kb_info.get("visibility", "private")
        if visibility != "private":
            set_visibility(owner_token, kb_id, visibility)
            print(f"     可见性: {visibility}")

        # 如果是公开状态，需要管理员审核
        if visibility == "public":
            approve_knowledge_base(admin_token, kb_id)
            print(f"     ✓ 管理员已审核通过")

        # 如果是分享状态，分享给指定用户
        if visibility == "shared" and "shared_with" in kb_info:
            for share_username in kb_info["shared_with"]:
                share_user_id = user_ids.get(share_username)
                if share_user_id:
                    share_knowledge_base(owner_token, kb_id, share_user_id)
                    print(f"     ✓ 已分享给 {share_username}")

        created_count += 1

    return created_count


def main():
    print("=" * 70)
    print("       知识库测试数据生成脚本")
    print("       支持三种提示词模板场景")
    print("=" * 70)

    # 创建用户
    print("\n[步骤 1/4] 创建测试用户...")
    for user in TEST_USERS:
        create_user(user["username"], user["password"], user["is_admin"])

    # 登录所有用户
    print("\n[步骤 2/4] 登录用户...")
    tokens = {}
    user_ids = {}
    for user in TEST_USERS:
        token = login(user["username"], user["password"])
        if token:
            tokens[user["username"]] = token
            user_info = get_user_info(token)
            if user_info:
                user_ids[user["username"]] = user_info.get("id")
                print(f"  ✓ {user['username']} (ID: {user_info.get('id')})")

    admin_token = tokens.get("admin")
    if not admin_token:
        print("\n✗ 管理员登录失败，无法继续")
        return

    # 创建提示词模板
    print("\n[步骤 3/4] 创建提示词模板...")
    create_prompt_templates(admin_token)

    # 创建知识库
    print("\n[步骤 4/4] 创建知识库和文档...")

    total_created = 0

    print("\n" + "─" * 70)
    print("📖 技术文档类知识库")
    print("─" * 70)
    total_created += process_knowledge_bases(TECH_KNOWLEDGE_BASES, tokens, user_ids, admin_token, "技术文档")

    print("\n" + "─" * 70)
    print("📝 学习教程类知识库")
    print("─" * 70)
    total_created += process_knowledge_bases(TUTORIAL_KNOWLEDGE_BASES, tokens, user_ids, admin_token, "学习教程")

    print("\n" + "─" * 70)
    print("💡 通用知识类知识库")
    print("─" * 70)
    total_created += process_knowledge_bases(GENERAL_KNOWLEDGE_BASES, tokens, user_ids, admin_token, "通用知识")

    # 统计
    print("\n" + "=" * 70)
    print("✅ 创建完成!")
    print("=" * 70)
    print(f"\n📊 统计:")
    print(f"   - 创建用户: {len(user_ids)} 个")
    print(f"   - 创建知识库: {total_created} 个")
    print(f"   - 提示词模板: 3 个")

    print("\n📋 知识库状态:")
    print("   - 公开(public): 需要管理员审核后才能被其他用户看到")
    print("   - 待审核(pending): 等待管理员审核")
    print("   - 分享(shared): 仅分享给指定用户")
    print("   - 私有(private): 仅自己可见")

    print("\n👥 用户列表:")
    for username, uid in user_ids.items():
        role = "管理员" if username == "admin" else "普通用户"
        print(f"   - {username} (ID: {uid}, {role})")

    print("\n💡 提示:")
    print("   - 管理员可以审核待审核的知识库")
    print("   - 用户可以在知识库管理页面查看公开和分享的知识库")
    print("   - 聊天时可以选择不同的提示词模板")
    print("=" * 70)


if __name__ == "__main__":
    main()
