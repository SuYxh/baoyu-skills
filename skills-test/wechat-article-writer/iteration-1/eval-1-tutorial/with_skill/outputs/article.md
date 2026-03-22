## 标题建议

1. 100 行 Python 代码，从零实现一个命令行待办工具，简单好用
2. Python 实战：手把手教你写一个命令行 Todo 工具，比记事本好用 10 倍
3. 不想用复杂的 GTD 软件？用 Python 写个简单的命令行待办吧

## 摘要

还在用记事本记录待办事项？本文带你用 Python 从零实现一个命令行待办工具，支持添加、完成、删除、列表查看等核心功能，代码不到 100 行，适合 Python 初学者练手。读完你就能拥有一个属于自己的效率工具。

---

# 100 行 Python 代码，从零实现一个命令行待办工具，简单好用

上周整理电脑的时候，翻到一个叫 `todo.txt` 的文件。

打开一看，里面密密麻麻写满了各种待办事项，有的已经完成了但没删，有的早就过期了，还有的重复写了三遍。

我盯着这个文件看了半天，心想：这也太乱了。

用记事本记待办，最大的问题就是——**没有状态管理**。完成了的事情没法标记，想删掉又怕误删，时间久了就变成了一堆"数字垃圾"。

市面上的 GTD 软件倒是不少，但要么功能太复杂，要么需要联网同步，我就想简单记录一下今天要干啥，至于这么麻烦吗？

所以，我决定自己写一个。

## 一、需求分析：我到底想要什么？

在动手写代码之前，我先想清楚了这个工具需要什么功能。

最核心的几个：

1. **添加待办**：`todo add "写周报"`，添加一条新待办
2. **查看列表**：`todo list`，列出所有待办
3. **标记完成**：`todo done 1`，把第 1 条标记为已完成
4. **删除待办**：`todo delete 1`，删除第 1 条

就这四个功能，够用了。

至于优先级、标签、截止日期这些？先不考虑，保持简单。

## 二、数据怎么存？

功能想清楚了，下一个问题是：数据存哪里？

最简单的方案——**JSON 文件**。

为什么选 JSON？

- Python 标准库直接支持，不需要安装任何依赖
- 人类可读，出问题了可以直接打开文件看
- 结构清晰，每条待办就是一个字典

数据结构设计如下：

```json
[
  {"id": 1, "content": "写周报", "done": false},
  {"id": 2, "content": "回复邮件", "done": true}
]
```

每条待办有三个字段：
- `id`：唯一标识，方便操作
- `content`：待办内容
- `done`：是否完成

## 三、开始写代码

### 1. 项目结构

创建一个文件夹，结构如下：

```
todo/
├── todo.py      # 主程序
└── todos.json   # 数据文件（自动生成）
```

### 2. 数据读写模块

先写两个基础函数，负责读取和保存数据：

```python
import json
import os

DATA_FILE = "todos.json"

def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
```

`load_todos()` 读取数据，如果文件不存在就返回空列表。

`save_todos()` 保存数据，`ensure_ascii=False` 保证中文正常显示，`indent=2` 让文件格式化输出，方便调试。

### 3. 添加待办

```python
def add_todo(content):
    todos = load_todos()
    
    # 生成新 ID
    if todos:
        new_id = max(t["id"] for t in todos) + 1
    else:
        new_id = 1
    
    todos.append({
        "id": new_id,
        "content": content,
        "done": False
    })
    
    save_todos(todos)
    print(f"✓ 已添加待办: {content}")
```

这里有个细节：**ID 的生成方式**。

我一开始想用 `len(todos) + 1`，但这样有问题——如果删除了中间某条，ID 就会重复。

所以改用 `max(id) + 1`，保证 ID 永远递增且唯一。

### 4. 查看待办列表

```python
def list_todos():
    todos = load_todos()
    
    if not todos:
        print("暂无待办事项")
        return
    
    print("\n待办列表:")
    print("-" * 40)
    for t in todos:
        status = "✓" if t["done"] else "○"
        print(f"{t['id']:3d}. [{status}] {t['content']}")
    print("-" * 40)
```

效果如下：

```
待办列表:
----------------------------------------
  1. [○] 写周报
  2. [✓] 回复邮件
  3. [○] 准备周会 PPT
----------------------------------------
```

`○` 表示未完成，`✓` 表示已完成，一目了然。

### 5. 标记完成

```python
def done_todo(todo_id):
    todos = load_todos()
    
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            save_todos(todos)
            print(f"✓ 已完成: {t['content']}")
            return
    
    print(f"✗ 未找到 ID 为 {todo_id} 的待办")
```

遍历列表，找到对应 ID，把 `done` 设为 `True`。

### 6. 删除待办

```python
def delete_todo(todo_id):
    todos = load_todos()
    
    for i, t in enumerate(todos):
        if t["id"] == todo_id:
            deleted = todos.pop(i)
            save_todos(todos)
            print(f"✓ 已删除: {deleted['content']}")
            return
    
    print(f"✗ 未找到 ID 为 {todo_id} 的待办")
```

用 `enumerate` 获取索引，找到后用 `pop` 删除。

### 7. 命令行入口

最后，用 `argparse` 处理命令行参数：

```python
import argparse

def main():
    parser = argparse.ArgumentParser(description="简单的命令行待办工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # add 命令
    add_parser = subparsers.add_parser("add", help="添加待办")
    add_parser.add_argument("content", help="待办内容")

    # done 命令
    done_parser = subparsers.add_parser("done", help="标记完成")
    done_parser.add_argument("id", type=int, help="待办 ID")

    # delete 命令
    delete_parser = subparsers.add_parser("delete", help="删除待办")
    delete_parser.add_argument("id", type=int, help="待办 ID")

    # list 命令
    subparsers.add_parser("list", help="查看待办列表")

    args = parser.parse_args()

    if args.command == "add":
        add_todo(args.content)
    elif args.command == "done":
        done_todo(args.id)
    elif args.command == "delete":
        delete_todo(args.id)
    elif args.command == "list":
        list_todos()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

## 四、效果演示

把上面的代码保存为 `todo.py`，然后就可以用了：

```bash
# 添加待办
python todo.py add "写周报"
python todo.py add "回复邮件"
python todo.py add "准备周会 PPT"

# 查看列表
python todo.py list

# 标记完成
python todo.py done 2

# 删除
python todo.py delete 1
```

运行效果：

```
$ python todo.py list

待办列表:
----------------------------------------
  1. [○] 写周报
  2. [✓] 回复邮件
  3. [○] 准备周会 PPT
----------------------------------------
```

## 五、还能怎么改进？

这个工具已经能用了，但如果你想继续折腾，还有很多可以加的功能：

**1. 按状态筛选**

```bash
python todo.py list --done      # 只看已完成的
python todo.py list --pending   # 只看未完成的
```

**2. 添加优先级**

数据结构加一个 `priority` 字段，列表按优先级排序。

**3. 支持修改**

```bash
python todo.py edit 1 "修改后的内容"
```

**4. 数据持久化到数据库**

如果待办多了，JSON 文件可能性能不够，可以换成 SQLite。

**5. 彩色输出**

用 `colorama` 库，让已完成的事项显示灰色，未完成的显示高亮。

## 六、完整代码

把所有代码放在一起，总共不到 100 行：

```python
import json
import os
import argparse

DATA_FILE = "todos.json"

def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def add_todo(content):
    todos = load_todos()
    new_id = max(t["id"] for t in todos) + 1 if todos else 1
    todos.append({"id": new_id, "content": content, "done": False})
    save_todos(todos)
    print(f"✓ 已添加待办: {content}")

def list_todos():
    todos = load_todos()
    if not todos:
        print("暂无待办事项")
        return
    print("\n待办列表:")
    print("-" * 40)
    for t in todos:
        status = "✓" if t["done"] else "○"
        print(f"{t['id']:3d}. [{status}] {t['content']}")
    print("-" * 40)

def done_todo(todo_id):
    todos = load_todos()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = True
            save_todos(todos)
            print(f"✓ 已完成: {t['content']}")
            return
    print(f"✗ 未找到 ID 为 {todo_id} 的待办")

def delete_todo(todo_id):
    todos = load_todos()
    for i, t in enumerate(todos):
        if t["id"] == todo_id:
            deleted = todos.pop(i)
            save_todos(todos)
            print(f"✓ 已删除: {deleted['content']}")
            return
    print(f"✗ 未找到 ID 为 {todo_id} 的待办")

def main():
    parser = argparse.ArgumentParser(description="简单的命令行待办工具")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("content")

    done_parser = subparsers.add_parser("done")
    done_parser.add_argument("id", type=int)

    delete_parser = subparsers.add_parser("delete")
    delete_parser.add_argument("id", type=int)

    subparsers.add_parser("list")

    args = parser.parse_args()

    if args.command == "add":
        add_todo(args.content)
    elif args.command == "done":
        done_todo(args.id)
    elif args.command == "delete":
        delete_todo(args.id)
    elif args.command == "list":
        list_todos()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

## 写在最后

从记事本到这个小程序，本质上是从"无结构"到"有结构"的转变。

代码不长，但涵盖了文件读写、命令行参数解析、列表操作等 Python 基础知识，非常适合初学者练手。

更重要的是，这是**你自己的工具**。想加什么功能，改几行代码就行，不用等别人更新。

不知道你手痒了没，要不要也写一个自己的命令行工具？

---

## 互动引导

如果这篇文章对你有帮助，点个赞再走呗 👍

关注「老码小张」，每周分享技术实践和行业洞察。

## SEO 关键词

- Python 命令行工具
- Python 待办事项
- argparse 教程
- Python 初学者项目
- 命令行 Todo
