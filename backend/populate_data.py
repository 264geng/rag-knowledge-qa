"""批量创建知识库和文档"""
import requests
import tempfile
import os

BASE_URL = 'http://localhost:8000/api'

def login(username, password):
    r = requests.post(f'{BASE_URL}/auth/login', json={'username': username, 'password': password})
    return r.json().get('access_token') if r.status_code == 200 else None

def get_me(token):
    r = requests.get(f'{BASE_URL}/auth/me', headers={'Authorization': f'Bearer {token}'})
    return r.json() if r.status_code == 200 else None

def create_kb(token, name, desc):
    r = requests.post(f'{BASE_URL}/knowledge-base', json={'name': name, 'description': desc}, headers={'Authorization': f'Bearer {token}'})
    return r.json().get('id') if r.status_code == 200 else None

def upload_doc(token, kb_id, filename, content):
    suffix = '.md' if filename.endswith('.md') else '.txt'
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
        f.write(content)
        temp = f.name
    with open(temp, 'rb') as f:
        r = requests.post(f'{BASE_URL}/knowledge-base/{kb_id}/documents', files={'file': (filename, f)}, headers={'Authorization': f'Bearer {token}'})
    os.unlink(temp)
    return r.status_code == 200

def set_visibility(token, kb_id, vis):
    r = requests.put(f'{BASE_URL}/interact/knowledge-base/{kb_id}/visibility', json={'visibility': vis}, headers={'Authorization': f'Bearer {token}'})
    return r.status_code == 200

def approve_kb(token, kb_id):
    r = requests.put(f'{BASE_URL}/admin/review/knowledge-bases/{kb_id}/approve', headers={'Authorization': f'Bearer {token}'})
    return r.status_code == 200

def share_kb(token, kb_id, user_id):
    r = requests.post(f'{BASE_URL}/interact/knowledge-base/{kb_id}/share', json={'user_id': user_id}, headers={'Authorization': f'Bearer {token}'})
    return r.status_code == 200

# 登录所有用户
print('=== 登录用户 ===')
tokens = {}
ids = {}
for u, p in [('admin','admin123'),('zhangsan','user123'),('lisi','user123'),('wangwu','user123')]:
    t = login(u, p)
    if t:
        tokens[u] = t
        info = get_me(t)
        ids[u] = info['id']
        print(f'  {u} (ID:{info["id"]})')

admin_token = tokens['admin']

# 知识库2: JavaScript前端开发 (zhangsan, 公开)
print('\n=== 知识库2: JavaScript前端开发 ===')
kb2 = create_kb(tokens['zhangsan'], 'JavaScript前端开发', 'JavaScript语言核心知识和前端开发技术')
print(f'  ID: {kb2}')
upload_doc(tokens['zhangsan'], kb2, 'ES6+新特性.txt', """ES6+新特性详解

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
""")
upload_doc(tokens['zhangsan'], kb2, 'Vue3框架入门.md', """# Vue3框架入门

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
""")
set_visibility(tokens['zhangsan'], kb2, 'public')
approve_kb(admin_token, kb2)
print('  状态: 已公开(已审核)')

# 知识库3: 数据库技术大全 (lisi, 待审核)
print('\n=== 知识库3: 数据库技术大全 ===')
kb3 = create_kb(tokens['lisi'], '数据库技术大全', '关系型和非关系型数据库技术文档')
print(f'  ID: {kb3}')
upload_doc(tokens['lisi'], kb3, 'MySQL性能优化.txt', """MySQL性能优化指南

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
""")
upload_doc(tokens['lisi'], kb3, 'MongoDB入门教程.md', """# MongoDB入门教程

## 1. 基本概念

MongoDB是一个基于分布式文件存储的NoSQL数据库。

- 数据库（Database）
- 集合（Collection）
- 文档（Document）

## 2. CRUD操作

### 创建
db.users.insertOne({name: "张三", age: 25})

### 查询
db.users.find({age: {$gt: 20}})

### 更新
db.users.updateOne({name: "张三"}, {$set: {age: 26}})

### 删除
db.users.deleteOne({name: "张三"})
""")
set_visibility(tokens['lisi'], kb3, 'pending')
print('  状态: 待审核')

# 知识库4: 机器学习入门教程 (admin, 公开)
print('\n=== 知识库4: 机器学习入门教程 ===')
kb4 = create_kb(tokens['admin'], '机器学习入门教程', '从零开始学习机器学习，包含理论和实践')
print(f'  ID: {kb4}')
upload_doc(tokens['admin'], kb4, '机器学习基础概念.txt', """机器学习基础概念

一、什么是机器学习
机器学习是人工智能的一个分支，它让计算机能够从数据中学习，而无需显式编程。

二、机器学习的类型
1. 监督学习
   - 分类：预测离散标签
   - 回归：预测连续值

2. 无监督学习
   - 聚类：将数据分组
   - 降维：减少特征数量

3. 强化学习
   - 通过与环境交互学习

三、常见算法
1. 线性回归
2. 逻辑回归
3. 决策树
4. 随机森林
5. 支持向量机
6. 神经网络
""")
upload_doc(tokens['admin'], kb4, 'Python机器学习实战.md', """# Python机器学习实战

## 1. 环境准备

```bash
pip install numpy pandas scikit-learn matplotlib
```

## 2. 数据预处理

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

data = pd.read_csv('data.csv')
X = data.drop('target', axis=1)
y = data['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
```

## 3. 模型训练

```python
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

model = LogisticRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
```
""")
set_visibility(tokens['admin'], kb4, 'public')
approve_kb(admin_token, kb4)
print('  状态: 已公开(已审核)')

# 知识库5: Web开发全栈教程 (zhangsan, 公开)
print('\n=== 知识库5: Web开发全栈教程 ===')
kb5 = create_kb(tokens['zhangsan'], 'Web开发全栈教程', '从前端到后端的完整Web开发教程')
print(f'  ID: {kb5}')
upload_doc(tokens['zhangsan'], kb5, 'HTML和CSS基础.txt', """HTML和CSS基础教程

一、HTML基础
1. HTML文档结构
<!DOCTYPE html>
<html>
<head><title>标题</title></head>
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

二、CSS基础
1. 选择器
- 元素选择器：p { }
- 类选择器：.class { }
- ID选择器：#id { }

2. 盒模型：content, padding, border, margin

3. 布局：Flexbox, Grid
""")
upload_doc(tokens['zhangsan'], kb5, 'Node.js后端开发.md', """# Node.js后端开发

## 1. Express框架

```javascript
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.json({ message: 'Hello World' });
});

app.listen(3000);
```

## 2. 路由处理

- GET: 获取数据
- POST: 创建数据
- PUT: 更新数据
- DELETE: 删除数据

## 3. 中间件

```javascript
app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});
```
""")
set_visibility(tokens['zhangsan'], kb5, 'public')
approve_kb(admin_token, kb5)
print('  状态: 已公开(已审核)')

# 知识库6: 项目管理知识体系 (lisi, 分享给zhangsan)
print('\n=== 知识库6: 项目管理知识体系 ===')
kb6 = create_kb(tokens['lisi'], '项目管理知识体系', '项目管理方法论和最佳实践')
print(f'  ID: {kb6}')
upload_doc(tokens['lisi'], kb6, '敏捷开发Scrum指南.txt', """敏捷开发Scrum指南

一、Scrum概述
Scrum是一个用于开发和维护复杂产品的框架。

二、Scrum角色
1. 产品负责人（Product Owner）
2. Scrum Master
3. 开发团队

三、Scrum事件
1. Sprint：固定时间周期
2. Sprint计划会
3. 每日站会
4. Sprint评审会
5. Sprint回顾会

四、Scrum工件
1. 产品待办事项
2. Sprint待办事项
3. 增量
""")
upload_doc(tokens['lisi'], kb6, '项目风险管理.md', """# 项目风险管理

## 1. 风险识别
- 头脑风暴
- 检查表分析
- SWOT分析

## 2. 风险评估
- 概率评估
- 影响评估
- 风险等级划分

## 3. 风险应对策略
- 规避：消除风险
- 转移：转嫁给第三方
- 减轻：降低概率或影响
- 接受：制定应急计划
""")
set_visibility(tokens['lisi'], kb6, 'shared')
share_kb(tokens['lisi'], kb6, ids['zhangsan'])
print('  状态: 已分享给zhangsan')

# 知识库7: 个人学习笔记 (wangwu, 私有)
print('\n=== 知识库7: 个人学习笔记 ===')
kb7 = create_kb(tokens['wangwu'], '个人学习笔记', '日常学习过程中积累的知识点')
print(f'  ID: {kb7}')
upload_doc(tokens['wangwu'], kb7, 'Git常用命令.txt', """Git常用命令速查

一、基础配置
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

二、仓库操作
git init                    # 初始化仓库
git clone <url>            # 克隆仓库

三、文件操作
git add <file>             # 添加文件到暂存区
git commit -m "message"    # 提交更改
git status                 # 查看状态

四、分支操作
git branch                 # 查看分支
git branch <name>          # 创建分支
git checkout <branch>      # 切换分支
git merge <branch>         # 合并分支

五、远程操作
git push origin <branch>   # 推送到远程
git pull                   # 拉取远程更新
""")
upload_doc(tokens['wangwu'], kb7, 'Docker入门指南.md', """# Docker入门指南

## 1. 基本概念
- 镜像（Image）：只读模板
- 容器（Container）：镜像的运行实例
- 仓库（Repository）：存储镜像的地方

## 2. 常用命令

### 镜像操作
docker images              # 列出镜像
docker pull <image>        # 拉取镜像
docker build -t <name> .   # 构建镜像

### 容器操作
docker run -d -p 80:80 <image>  # 运行容器
docker ps                       # 查看运行中的容器
docker stop <container>         # 停止容器

## 3. Dockerfile
FROM node:14
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["node", "app.js"]
""")
print('  状态: 私有')

# 知识库8: 人工智能前沿技术 (admin, 待审核)
print('\n=== 知识库8: 人工智能前沿技术 ===')
kb8 = create_kb(tokens['admin'], '人工智能前沿技术', 'AI领域最新技术动态和研究成果')
print(f'  ID: {kb8}')
upload_doc(tokens['admin'], kb8, '大语言模型概述.txt', """大语言模型概述

一、什么是大语言模型
大语言模型（LLM）是基于深度学习的自然语言处理模型，通常包含数十亿甚至数万亿参数。

二、代表性模型
1. GPT系列（OpenAI）
   - GPT-3: 1750亿参数
   - GPT-4: 多模态模型

2. BERT系列（Google）
   - BERT: 双向编码器
   - T5: 文本到文本转换

3. LLaMA系列（Meta）
   - 开源大语言模型

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
""")
set_visibility(tokens['admin'], kb8, 'pending')
print('  状态: 待审核')

print('\n' + '='*50)
print('所有知识库创建完成!')
print('='*50)
print(f'\n统计:')
print(f'  用户: {len(ids)} 个')
print(f'  知识库: 8 个')
print(f'  公开(已审核): 4 个')
print(f'  待审核: 2 个')
print(f'  分享: 1 个')
print(f'  私有: 1 个')
