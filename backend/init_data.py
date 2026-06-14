"""
部署初始化脚本
在云平台部署后运行此脚本，自动创建用户、知识库和文档
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
# 知识库内容
# ============================================================

KB_DATA = [
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
        ]
    },
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
        ]
    },
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
        ]
    },
    {
        "name": "数据库技术大全",
        "desc": "关系型和非关系型数据库技术文档",
        "owner": "lisi",
        "visibility": "pending",
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
        ]
    },
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
        ]
    },
]


def main():
    print('='*50)
    print('部署初始化脚本')
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
        print('后端服务启动超时，请检查配置')
        return

    # 创建用户
    print('\n[1/5] 创建用户...')
    users = [
        ('admin', 'admin123'),
        ('zhangsan', 'user123'),
        ('lisi', 'user123'),
        ('wangwu', 'user123'),
    ]
    for u, p in users:
        register(u, p)
        print(f'  {u}: OK')

    # 登录
    print('\n[2/5] 登录用户...')
    tokens = {}
    ids = {}
    for u, p in users:
        t = login(u, p)
        if t:
            tokens[u] = t
            r = requests.get(f'{BASE_URL}/auth/me', headers={'Authorization': f'Bearer {t}'})
            ids[u] = r.json().get('id')
            print(f'  {u} (ID:{ids[u]}): OK')

    admin_token = tokens['admin']

    # 创建提示词模板
    print('\n[3/5] 创建提示词模板...')
    create_templates(admin_token)
    print('  3个模板创建完成')

    # 创建知识库
    print('\n[4/5] 创建知识库...')
    for kb_info in KB_DATA:
        owner = kb_info['owner']
        owner_token = tokens.get(owner)
        if not owner_token:
            continue

        kb_id = create_kb(owner_token, kb_info['name'], kb_info['desc'])
        if not kb_id:
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
                share_kb(owner_token, kb_id, ids[share_user])

    # 等待文档处理
    print('\n[5/5] 等待文档处理...')
    time.sleep(10)

    print('\n' + '='*50)
    print('初始化完成!')
    print('='*50)
    print(f'\n测试账号:')
    print(f'  管理员: admin / admin123')
    print(f'  用户1: zhangsan / user123')
    print(f'  用户2: lisi / user123')
    print(f'  用户3: wangwu / user123')


if __name__ == '__main__':
    main()
