# 从零开始：用 Python 实现一个命令行待办事项管理工具

> 每天都有很多事情要做，却总是忘记？今天我们用 Python 写一个简单实用的命令行待办事项工具，让你的生活井井有条！

## 前言

作为一名程序员，我们每天都在和各种任务打交道。有时候是修复一个 bug，有时候是完成一个功能，还有那些数不清的日常琐事。如果有一个简单好用的工具来管理这些待办事项，生活会变得更有条理。

市面上的待办事项应用很多，但作为程序员，我们更想自己动手实现一个。今天，就让我们用 Python 从零开始，实现一个功能完整的命令行待办事项管理工具。

## 项目目标

我们要实现一个具备以下功能的待办事项工具：

- 添加待办事项
- 查看所有待办事项
- 标记待办事项为已完成
- 删除待办事项
- 数据持久化存储

## 准备工作

本项目使用 Python 3.x 开发，只需要使用 Python 标准库，无需安装额外的依赖包。

首先，创建一个项目文件夹，并在其中新建 `todo.py` 文件：

```bash
mkdir todo-cli
cd todo-cli
touch todo.py
```

## 第一步：设计数据结构

我们需要考虑如何存储待办事项。每条待办事项应该包含以下信息：

- 唯一标识 ID
- 任务内容
- 创建时间
- 是否完成

我们使用 JSON 格式来存储数据，这样既方便读写，又易于人类阅读。

## 第二步：实现数据存储模块

首先，我们来实现数据的读取和保存功能：

```python
import json
import os
from datetime import datetime

DATA_FILE = "todos.json"

def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_todos(todos):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
```

这里我们定义了两个核心函数：

- `load_todos()`：从 JSON 文件加载待办事项，如果文件不存在则返回空列表
- `save_todos()`：将待办事项保存到 JSON 文件

## 第三步：实现添加待办事项功能

接下来实现添加待办事项的功能：

```python
def add_todo(content):
    todos = load_todos()
    
    new_id = max([t['id'] for t in todos], default=0) + 1
    
    todo = {
        'id': new_id,
        'content': content,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'done': False
    }
    
    todos.append(todo)
    save_todos(todos)
    
    print(f"✓ 已添加待办事项 [ID: {new_id}]: {content}")
```

这个函数会：

1. 加载现有的待办事项
2. 生成一个新的唯一 ID
3. 创建待办事项对象，包含 ID、内容、创建时间和完成状态
4. 保存到文件
5. 输出确认信息

## 第四步：实现查看待办事项功能

我们需要一个美观的方式来展示所有待办事项：

```python
def list_todos():
    todos = load_todos()
    
    if not todos:
        print("暂无待办事项")
        return
    
    print("\n" + "=" * 60)
    print("📋 待办事项列表")
    print("=" * 60)
    
    for todo in todos:
        status = "✅" if todo['done'] else "⬜"
        content = todo['content']
        if todo['done']:
            content = f"\033[9m{content}\033[0m"
        
        print(f"{status} [ID: {todo['id']}] {content}")
        print(f"   创建时间: {todo['created_at']}")
        print("-" * 60)
    
    pending = sum(1 for t in todos if not t['done'])
    completed = sum(1 for t in todos if t['done'])
    print(f"\n统计: 共 {len(todos)} 项 | 待完成 {pending} 项 | 已完成 {completed} 项\n")
```

这个函数会：

1. 加载所有待办事项
2. 用表格形式展示
3. 已完成的项目会有删除线效果
4. 显示统计信息

## 第五步：实现完成和删除功能

```python
def complete_todo(todo_id):
    todos = load_todos()
    
    for todo in todos:
        if todo['id'] == todo_id:
            todo['done'] = True
            save_todos(todos)
            print(f"✓ 已完成待办事项 [ID: {todo_id}]: {todo['content']}")
            return
    
    print(f"✗ 未找到 ID 为 {todo_id} 的待办事项")

def delete_todo(todo_id):
    todos = load_todos()
    
    for i, todo in enumerate(todos):
        if todo['id'] == todo_id:
            deleted = todos.pop(i)
            save_todos(todos)
            print(f"✓ 已删除待办事项 [ID: {todo_id}]: {deleted['content']}")
            return
    
    print(f"✗ 未找到 ID 为 {todo_id} 的待办事项")
```

## 第六步：实现命令行参数解析

最后，我们需要解析命令行参数，让用户可以通过命令行与程序交互：

```python
import sys

def print_help():
    print("""
命令行待办事项管理工具

用法:
    python todo.py add "任务内容"    添加待办事项
    python todo.py list             查看所有待办事项
    python todo.py done <ID>        标记待办事项为已完成
    python todo.py delete <ID>      删除待办事项
    python todo.py help             显示帮助信息

示例:
    python todo.py add "完成项目报告"
    python todo.py done 1
    python todo.py delete 2
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1]
    
    if command == "add":
        if len(sys.argv) < 3:
            print("✗ 请提供待办事项内容")
            return
        add_todo(sys.argv[2])
    
    elif command == "list":
        list_todos()
    
    elif command == "done":
        if len(sys.argv) < 3:
            print("✗ 请提供待办事项 ID")
            return
        try:
            todo_id = int(sys.argv[2])
            complete_todo(todo_id)
        except ValueError:
            print("✗ ID 必须是数字")
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("✗ 请提供待办事项 ID")
            return
        try:
            todo_id = int(sys.argv[2])
            delete_todo(todo_id)
        except ValueError:
            print("✗ ID 必须是数字")
    
    elif command == "help":
        print_help()
    
    else:
        print(f"✗ 未知命令: {command}")
        print_help()

if __name__ == "__main__":
    main()
```

## 完整代码

将以上所有代码整合到一起，完整的 `todo.py` 文件如下：

```python
import json
import os
import sys
from datetime import datetime

DATA_FILE = "todos.json"

def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_todos(todos):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def add_todo(content):
    todos = load_todos()
    new_id = max([t['id'] for t in todos], default=0) + 1
    todo = {
        'id': new_id,
        'content': content,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'done': False
    }
    todos.append(todo)
    save_todos(todos)
    print(f"✓ 已添加待办事项 [ID: {new_id}]: {content}")

def list_todos():
    todos = load_todos()
    if not todos:
        print("暂无待办事项")
        return
    print("\n" + "=" * 60)
    print("📋 待办事项列表")
    print("=" * 60)
    for todo in todos:
        status = "✅" if todo['done'] else "⬜"
        content = todo['content']
        if todo['done']:
            content = f"\033[9m{content}\033[0m"
        print(f"{status} [ID: {todo['id']}] {content}")
        print(f"   创建时间: {todo['created_at']}")
        print("-" * 60)
    pending = sum(1 for t in todos if not t['done'])
    completed = sum(1 for t in todos if t['done'])
    print(f"\n统计: 共 {len(todos)} 项 | 待完成 {pending} 项 | 已完成 {completed} 项\n")

def complete_todo(todo_id):
    todos = load_todos()
    for todo in todos:
        if todo['id'] == todo_id:
            todo['done'] = True
            save_todos(todos)
            print(f"✓ 已完成待办事项 [ID: {todo_id}]: {todo['content']}")
            return
    print(f"✗ 未找到 ID 为 {todo_id} 的待办事项")

def delete_todo(todo_id):
    todos = load_todos()
    for i, todo in enumerate(todos):
        if todo['id'] == todo_id:
            deleted = todos.pop(i)
            save_todos(todos)
            print(f"✓ 已删除待办事项 [ID: {todo_id}]: {deleted['content']}")
            return
    print(f"✗ 未找到 ID 为 {todo_id} 的待办事项")

def print_help():
    print("""
命令行待办事项管理工具

用法:
    python todo.py add "任务内容"    添加待办事项
    python todo.py list             查看所有待办事项
    python todo.py done <ID>        标记待办事项为已完成
    python todo.py delete <ID>      删除待办事项
    python todo.py help             显示帮助信息

示例:
    python todo.py add "完成项目报告"
    python todo.py done 1
    python todo.py delete 2
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
    command = sys.argv[1]
    if command == "add":
        if len(sys.argv) < 3:
            print("✗ 请提供待办事项内容")
            return
        add_todo(sys.argv[2])
    elif command == "list":
        list_todos()
    elif command == "done":
        if len(sys.argv) < 3:
            print("✗ 请提供待办事项 ID")
            return
        try:
            todo_id = int(sys.argv[2])
            complete_todo(todo_id)
        except ValueError:
            print("✗ ID 必须是数字")
    elif command == "delete":
        if len(sys.argv) < 3:
            print("✗ 请提供待办事项 ID")
            return
        try:
            todo_id = int(sys.argv[2])
            delete_todo(todo_id)
        except ValueError:
            print("✗ ID 必须是数字")
    elif command == "help":
        print_help()
    else:
        print(f"✗ 未知命令: {command}")
        print_help()

if __name__ == "__main__":
    main()
```

## 运行效果演示

让我们来体验一下这个工具：

**添加待办事项：**

```bash
$ python todo.py add "完成 Python 教程文章"
✓ 已添加待办事项 [ID: 1]: 完成 Python 教程文章

$ python todo.py add "学习 argparse 模块"
✓ 已添加待办事项 [ID: 2]: 学习 argparse 模块

$ python todo.py add "整理代码仓库"
✓ 已添加待办事项 [ID: 3]: 整理代码仓库
```

**查看待办事项：**

```bash
$ python todo.py list

============================================================
📋 待办事项列表
============================================================
⬜ [ID: 1] 完成 Python 教程文章
   创建时间: 2024-01-15 10:30:00
------------------------------------------------------------
⬜ [ID: 2] 学习 argparse 模块
   创建时间: 2024-01-15 10:31:00
------------------------------------------------------------
⬜ [ID: 3] 整理代码仓库
   创建时间: 2024-01-15 10:32:00
------------------------------------------------------------

统计: 共 3 项 | 待完成 3 项 | 已完成 0 项
```

**标记完成：**

```bash
$ python todo.py done 1
✓ 已完成待办事项 [ID: 1]: 完成 Python 教程文章
```

**删除待办事项：**

```bash
$ python todo.py delete 3
✓ 已删除待办事项 [ID: 3]: 整理代码仓库
```

## 功能扩展思路

这个基础版本已经可以满足日常使用，如果你想进一步完善，可以考虑以下扩展方向：

**1. 添加优先级功能**

为每个待办事项添加优先级（高/中/低），并按优先级排序显示。

**2. 添加截止日期**

支持设置截止日期，并在临近截止时提醒用户。

**3. 添加分类标签**

支持给待办事项打标签，如「工作」「生活」「学习」等，方便分类查看。

**4. 使用 argparse 模块**

使用 Python 标准库的 `argparse` 模块，可以提供更友好的命令行参数解析和帮助信息。

**5. 添加搜索功能**

支持按关键词搜索待办事项。

**6. 数据同步**

将数据同步到云端，实现多设备共享。

## 总结

通过这个项目，我们学习了：

- 如何使用 JSON 文件进行数据持久化
- 如何设计简单的数据结构
- 如何解析命令行参数
- 如何组织一个完整的 Python 项目

这个待办事项工具虽然简单，但涵盖了程序开发的核心要素：数据存储、业务逻辑和用户交互。希望这个项目能给你带来启发，动手实现自己的版本，并在此基础上添加更多有趣的功能。

编程的乐趣在于创造，而最好的学习方式就是动手实践。快去试试吧！

---

> 如果你觉得这篇文章有帮助，欢迎点赞、收藏、转发！有问题欢迎在评论区留言讨论。
