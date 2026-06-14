"""
完整数据初始化脚本
保留当前系统的所有用户、知识库和文档数据
"""

import requests
import json
import tempfile
import os
import time

# 配置
BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000/api')

def login(username, password):
    r = requests.post(f'{BASE_URL}/auth/login', json={'username': username, 'password': password})
    return r.json().get('access_token') if r.status_code == 200 else None

def register(username, password):
    r = requests.post(f'{BASE_URL}/auth/register', json={'username': username, 'password': password})
    return r.status_code == 200 or 'already exists' in r.text

def create_kb(token, name, desc):
    r = requests.post(f'{BASE_URL}/knowledge-base', json={'name': name, 'description': desc},
                      headers={'Authorization': f'Bearer {token}'})
    return r.json().get('id') if r.status_code == 200 else None

def upload_doc(token, kb_id, filename, content):
    suffix = '.md' if filename.endswith('.md') else '.txt'
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
        f.write(content)
        temp = f.name
    with open(temp, 'rb') as f:
        r = requests.post(f'{BASE_URL}/knowledge-base/{kb_id}/documents',
                         files={'file': (filename, f)},
                         headers={'Authorization': f'Bearer {token}'})
    os.unlink(temp)
    return r.status_code == 200

def set_visibility(token, kb_id, vis):
    r = requests.put(f'{BASE_URL}/interact/knowledge-base/{kb_id}/visibility',
                    json={'visibility': vis},
                    headers={'Authorization': f'Bearer {token}'})
    return r.status_code == 200

def approve_kb(token, kb_id):
    r = requests.put(f'{BASE_URL}/admin/review/knowledge-bases/{kb_id}/approve',
                    headers={'Authorization': f'Bearer {token}'})
    return r.status_code == 200

def share_kb(token, kb_id, user_id):
    r = requests.post(f'{BASE_URL}/interact/knowledge-base/{kb_id}/share',
                     json={'user_id': user_id},
                     headers={'Authorization': f'Bearer {token}'})
    return r.status_code == 200

def create_templates(token):
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
    for tmpl in templates:
        requests.post(f'{BASE_URL}/prompt-templates', json=tmpl, headers={'Authorization': f'Bearer {token}'})

# ============================================================
# 完整数据定义
# ============================================================

# 用户列表
USERS = [
    ('admin', 'admin123'),      # ID:2 管理员
    ('admin1', 'user123'),      # ID:4
    ('zhangsan', 'user123'),    # ID:8
    ('lisi', 'user123'),        # ID:9
    ('wangwu', 'user123'),      # ID:10
    ('一只猫', 'user123'),       # ID:6
    ('两只鱼', 'user123'),       # ID:7
]

# 知识库数据
KB_DATA = [
    # 1. 测试 - admin - public
    {
        "name": "测试",
        "desc": "正在放假期间。",
        "owner": "admin",
        "visibility": "public",
        "docs": [
            ("去年统计.docx", """2024年度公司运营统计报告

一、营收情况
2024年公司总营收达到1.2亿元，同比增长15%。
其中：
- 产品销售收入：8000万元
- 技术服务收入：3000万元
- 其他收入：1000万元

二、成本支出
总成本支出：9000万元
- 人力成本：5000万元
- 运营成本：2500万元
- 研发投入：1500万元

三、利润情况
净利润：3000万元
利润率：25%

四、人员情况
员工总数：150人
- 技术人员：80人
- 销售人员：30人
- 管理人员：20人
- 其他：20人
"""),
        ]
    },
    # 2. 学习资料 - 一只猫 - public
    {
        "name": "学习资料",
        "desc": "学习资料",
        "owner": "一只猫",
        "visibility": "public",
        "docs": [
            ("资料.docx", """Python学习资料汇编

一、基础入门
1. Python安装与配置
2. 变量与数据类型
3. 控制流语句
4. 函数定义与调用

二、进阶内容
1. 面向对象编程
2. 文件操作
3. 异常处理
4. 模块与包

三、实战项目
1. Web开发（Flask/Django）
2. 数据分析（Pandas）
3. 机器学习（Scikit-learn）
4. 爬虫开发（Scrapy）

四、学习资源推荐
1. 官方文档：https://docs.python.org
2. 在线教程：廖雪峰Python教程
3. 练习平台：LeetCode、牛客网
"""),
        ]
    },
    # 3. Python编程核心技术 - admin - public
    {
        "name": "Python编程核心技术",
        "desc": "Python语言核心技术文档，涵盖基础语法、高级特性、最佳实践",
        "owner": "admin",
        "visibility": "public",
        "docs": [
            ("Python基础语法详解.txt", """Python基础语法详解

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
       pass
   elif another_condition:
       pass
   else:
       pass

2. 循环语句：
   for item in iterable:
       pass
   while condition:
       pass

三、函数定义
def function_name(parameters):
    return result

四、类和面向对象
class MyClass:
    def __init__(self, value):
        self.value = value
    def method(self):
        return self.value * 2
"""),
            ("Python高级特性.md", """# Python高级特性

## 1. 装饰器

装饰器用于在不修改原函数代码的情况下扩展函数功能。

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("函数调用前")
        result = func(*args, **kwargs)
        print("函数调用后")
        return result
    return wrapper
```

## 2. 生成器

生成器使用yield关键字，可以惰性求值。

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
"""),
            ("Python异常处理.txt", """Python异常处理指南

一、异常处理基础
使用try-except语句捕获和处理异常。

try:
    result = 10 / 0
except ZeroDivisionError:
    print("除零错误")
except Exception as e:
    print(f"其他错误: {e}")
finally:
    print("总是执行")

二、常见内置异常
1. ValueError: 值错误
2. TypeError: 类型错误
3. KeyError: 字典键错误
4. IndexError: 索引越界
5. FileNotFoundError: 文件未找到

三、自定义异常
class CustomError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
"""),
        ]
    },
    # 4. JavaScript前端开发 - zhangsan - public
    {
        "name": "JavaScript前端开发",
        "desc": "JavaScript语言核心知识和前端开发技术",
        "owner": "zhangsan",
        "visibility": "public",
        "docs": [
            ("ES6+新特性.txt", """ES6+新特性详解

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
"""),
            ("Vue3框架入门.md", """# Vue3框架入门

## 1. 组合式API

Vue3引入了组合式API，提供更灵活的代码组织方式。

```javascript
import { ref, computed, onMounted } from 'vue'

export default {
    setup() {
        const count = ref(0)
        const doubleCount = computed(() => count.value * 2)
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
"""),
        ]
    },
    # 5. 机器学习入门教程 - admin - public
    {
        "name": "机器学习入门教程",
        "desc": "从零开始学习机器学习，包含理论和实践",
        "owner": "admin",
        "visibility": "public",
        "docs": [
            ("机器学习基础概念.txt", """机器学习基础概念

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
"""),
            ("Python机器学习实战.md", """# Python机器学习实战

## 1. 环境准备

```bash
pip install numpy pandas scikit-learn matplotlib
```

## 2. 数据预处理

```python
import pandas as pd
from sklearn.model_selection import train_test_split

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
"""),
        ]
    },
    # 6. Web开发全栈教程 - zhangsan - public
    {
        "name": "Web开发全栈教程",
        "desc": "从前端到后端的完整Web开发教程",
        "owner": "zhangsan",
        "visibility": "public",
        "docs": [
            ("HTML和CSS基础.txt", """HTML和CSS基础教程

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
"""),
            ("Node.js后端开发.md", """# Node.js后端开发

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
"""),
        ]
    },
    # 7. 数据库技术大全 - lisi - private
    {
        "name": "数据库技术大全",
        "desc": "关系型和非关系型数据库技术文档",
        "owner": "lisi",
        "visibility": "private",
        "docs": [
            ("MySQL性能优化.txt", """MySQL性能优化指南

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
"""),
            ("MongoDB入门教程.md", """# MongoDB入门教程

## 1. 基本概念

MongoDB是一个基于分布式文件存储的NoSQL数据库。

## 2. CRUD操作

### 创建
db.users.insertOne({name: "张三", age: 25})

### 查询
db.users.find({age: {$gt: 20}})

### 更新
db.users.updateOne({name: "张三"}, {$set: {age: 26}})

### 删除
db.users.deleteOne({name: "张三"})
"""),
        ]
    },
    # 8. 项目管理知识体系 - lisi - shared (分享给zhangsan)
    {
        "name": "项目管理知识体系",
        "desc": "项目管理方法论和最佳实践",
        "owner": "lisi",
        "visibility": "shared",
        "shared_with": ["zhangsan"],
        "docs": [
            ("敏捷开发Scrum指南.txt", """敏捷开发Scrum指南

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
"""),
            ("项目风险管理.md", """# 项目风险管理

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
"""),
        ]
    },
    # 9. 个人学习笔记 - wangwu - private
    {
        "name": "个人学习笔记",
        "desc": "日常学习过程中积累的知识点",
        "owner": "wangwu",
        "visibility": "private",
        "docs": [
            ("Git常用命令.txt", """Git常用命令速查

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
"""),
            ("Docker入门指南.md", """# Docker入门指南

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
"""),
        ]
    },
    # 10. 人工智能前沿技术 - admin - private
    {
        "name": "人工智能前沿技术",
        "desc": "AI领域最新技术动态和研究成果",
        "owner": "admin",
        "visibility": "private",
        "docs": [
            ("大语言模型概述.txt", """大语言模型概述

一、什么是大语言模型
大语言模型（LLM）是基于深度学习的自然语言处理模型，通常包含数十亿甚至数万亿参数。

二、代表性模型
1. GPT系列（OpenAI）
2. BERT系列（Google）
3. LLaMA系列（Meta）

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
"""),
        ]
    },
    # 11. 杂物 - 两只鱼 - shared (分享给admin1, 一只猫)
    {
        "name": "杂物",
        "desc": "杂物放这。",
        "owner": "两只鱼",
        "visibility": "shared",
        "shared_with": ["admin1", "一只猫"],
        "docs": []
    },
    # 12. 日记 - 一只猫 - pending
    {
        "name": "日记",
        "desc": "日记",
        "owner": "一只猫",
        "visibility": "pending",
        "docs": []
    },
    # 13. 公司管理章程 - admin - public
    {
        "name": "公司管理章程",
        "desc": "公司内部管理制度和规范",
        "owner": "admin",
        "visibility": "public",
        "docs": [
            ("公司管理章程.txt", """公司管理章程

第一章 总则

第一条 为规范公司管理，保障公司和员工的合法权益，制定本章程。

第二条 本章程适用于公司全体员工。

第二章 员工招聘与录用

第三条 公司根据业务发展需要，按照公开、公平、公正的原则招聘员工。

第四条 新员工试用期为三个月，试用期满经考核合格者，转为正式员工。

第三章 工作时间与休假

第五条 公司实行标准工时制度，每日工作8小时，每周工作40小时。

第六条 员工依法享有以下休假权利：
（一）法定节假日
（二）年假：工作满1年5天，满10年10天，满20年15天
（三）病假、婚假、产假、丧假

第四章 薪酬与福利

第七条 公司实行岗位绩效工资制度。

第八条 公司依法为员工缴纳社会保险和住房公积金。

第五章 附则

第九条 本章程自发布之日起施行。
"""),
        ]
    },
]


def main():
    print('='*50)
    print('完整数据初始化脚本')
    print('='*50)

    # 等待后端启动
    print('\n等待后端服务启动...')
    for i in range(30):
        try:
            r = requests.get(f'{BASE_URL.replace("/api", "")}/docs', timeout=5)
            if r.status_code == 200:
                print('后端服务已就绪')
                break
        except:
            pass
        time.sleep(2)
    else:
        print('后端服务启动超时')
        return

    # 创建用户
    print('\n[1/5] 创建用户...')
    for u, p in USERS:
        register(u, p)
        print(f'  {u}: OK')

    # 登录
    print('\n[2/5] 登录用户...')
    tokens = {}
    ids = {}
    for u, p in USERS:
        t = login(u, p)
        if t:
            tokens[u] = t
            r = requests.get(f'{BASE_URL}/auth/me', headers={'Authorization': f'Bearer {t}'})
            ids[u] = r.json().get('id')
            print(f'  {u} (ID:{ids[u]}): OK')

    admin_token = tokens.get('admin')

    # 创建提示词模板
    print('\n[3/5] 创建提示词模板...')
    create_templates(admin_token)
    print('  3个模板创建完成')

    # 创建知识库
    print('\n[4/5] 创建知识库和文档...')
    for kb_info in KB_DATA:
        owner = kb_info['owner']
        owner_token = tokens.get(owner)
        if not owner_token:
            print(f'  跳过 {kb_info["name"]}: 用户{owner}未登录')
            continue

        kb_id = create_kb(owner_token, kb_info['name'], kb_info['desc'])
        if not kb_id:
            print(f'  跳过 {kb_info["name"]}: 创建失败')
            continue

        print(f'  {kb_info["name"]} (ID:{kb_id})')

        # 上传文档
        for doc_name, doc_content in kb_info['docs']:
            upload_doc(owner_token, kb_id, doc_name, doc_content)

        # 设置可见性
        vis = kb_info.get('visibility', 'private')
        if vis != 'private':
            set_visibility(owner_token, kb_id, vis)

        # 公开的需要审核
        if vis == 'public':
            approve_kb(admin_token, kb_id)

        # 分享的需要分享给用户
        if vis == 'shared' and 'shared_with' in kb_info:
            for share_user in kb_info['shared_with']:
                share_user_id = ids.get(share_user)
                if share_user_id:
                    share_kb(owner_token, kb_id, share_user_id)

    # 等待文档处理
    print('\n[5/5] 等待文档处理...')
    time.sleep(15)

    print('\n' + '='*50)
    print('初始化完成!')
    print('='*50)
    print(f'\n用户账号:')
    for u, p in USERS:
        print(f'  {u} / {p}')
    print(f'\n知识库: {len(KB_DATA)}个')
    print(f'提示词模板: 3个')


if __name__ == '__main__':
    main()
