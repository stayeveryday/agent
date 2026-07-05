# Python 入门：列表、元组、字典

这三个数据结构是 Python 入门里最常用、也最容易混的部分。可以先用一句话记住：

- `list` 用来放一串会变化的数据。
- `tuple` 用来放一组固定结构的数据。
- `dict` 用来放一组有名字的数据。

## 1. 列表 list

列表用 `[]` 表示，适合保存“多个同类东西”，而且以后可能还会增删改。

```python
tickets = ["T001", "T002", "T003"]
tickets.append("T004")
tickets[0] = "T000"
```

常见场景：

- 一组文档 chunk
- 一组消息 messages
- 一组检索结果
- 一组用户 ID
- 一组工具 tools

你可以把它理解成 Java 里的 `ArrayList`。

## 2. 元组 tuple

元组用 `()` 表示，适合保存“固定结构”的数据。一般创建以后不再修改。

```python
point = (120.1, 30.2)
message_template = ("system", "You are an assistant.")
```

常见场景：

- 坐标
- 固定返回值
- 消息角色 + 消息内容
- 一组不打算修改的配对数据

你可以把它理解成“轻量、不可变的组合值”。

## 3. 字典 dict

字典用 `{}` 表示，适合保存“键值对”。你通过 key 去找 value。

```python
user = {
    "id": "u001",
    "name": "Alice",
    "department": "IT",
}
```

常见场景：

- JSON 请求和响应
- 配置项
- metadata
- tool 参数
- Agent state
- 用户信息

你可以把它理解成 Java 里的 `HashMap`。

## 3.1 元组值和 tuple 类型标注

这里有一个容易混的地方：

```python
value = ("get_ticket_status", {"ticket_id": "INC-1001"})
```

这是在创建一个真正的元组值。

也可以省略括号：

```python
value = "get_ticket_status", {"ticket_id": "INC-1001"}
```

它和上面是一样的。Python 里真正决定元组的是逗号，不是括号。

所以：

```python
return "get_ticket_status", {"ticket_id": "INC-1001"}
```

等价于：

```python
return ("get_ticket_status", {"ticket_id": "INC-1001"})
```

但是下面这种写法：

```python
def build_tool_call() -> tuple[str, dict[str, object]]:
    ...
```

这里的 `tuple[...]` 不是在创建元组，而是在写类型标注。

它的意思是：

```text
这个函数返回一个 tuple
第 1 个元素是 str
第 2 个元素是 dict[str, object]
```

可以类比 Java 泛型：

```java
Tuple<String, Map<String, Object>>
```

Python 里的类型标注经常用 `[]` 表示“里面是什么类型”：

```python
list[str]
dict[str, object]
tuple[str, dict[str, object]]
```

所以要区分：

```text
运行时创建元组值：("a", 1)
类型标注：tuple[str, int]
```

再补一个单元素元组的特殊规则：

```python
a = (1)
```

这不是元组，而是整数 `1`。

真正的单元素元组要写：

```python
a = (1,)
```

简单记：

```text
创建 tuple 看逗号
类型标注 tuple[...] 看泛型
```

## 4. 怎么选

最简单的判断方式：

```text
一串东西，用 list
固定结构，用 tuple
按名字取值，用 dict
```

## 5. 和 Agent 项目的关系

在你的 LangChain + LangGraph 项目里，这三种结构会经常出现：

```python
# list：一组检索结果
retrieved_docs = [doc1, doc2, doc3]

# tuple：prompt 模板里的消息定义
("system", "You are an IT assistant.")
("user", "{question}")

# dict：Agent 状态
state = {
    "user_id": "u001",
    "query": "我要创建工单",
    "intent": "ticket_create",
    "tool_results": [],
}
```

## 6. 快速记忆

- `list` 负责“顺序”
- `tuple` 负责“固定”
- `dict` 负责“名字”

如果你以后拿不准，先问自己一句：

```text
我是在保存一串东西，还是一组固定结构，还是带字段名的数据？
```

## 7. 逗号小规则

Python 里有些逗号是可选的，常见于多行写法：

```python
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Hello"),
        ("user", "{question}"),
    ]
)
```

```python
return ChatOpenAI(
    model=settings.model_name,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)
```

这里最后的逗号不是必须的，但通常建议保留。好处是：

- 以后新增参数更方便
- 代码格式化更稳定
- 多行结构更整齐

## 8. 和 Java 的对照

这类 Pydantic 写法：

```python
class ChatRequest(BaseModel):
    question: str = Field(min_length=1, description="User question")
```

可以大致理解成 Java 里的 DTO 加校验注解：

```java
public class ChatRequest {
    @NotBlank
    @Schema(description = "User question")
    private String question;
}
```

对应关系可以这样记：

- `BaseModel` = 请求对象 / DTO
- `question: str` = `private String question`
- `Field(min_length=1)` = `@NotBlank` 或 `@Size(min = 1)`
- `description="User question"` = `@Schema(description = "...")`

这也是为什么 Python 写接口入参时，看起来会比纯 Java 更简洁，但本质上做的事很像：定义字段、加约束、给文档加说明。

## 9. Literal 固定可选值

`Literal` 是 Python 类型提示里的工具，用来表示“这个值只能是几个固定值中的一个”。

```python
from typing import Literal

IntentType = Literal[
    "knowledge_question",
    "ticket_query",
    "ticket_create",
    "asset_query",
    "smalltalk",
]
```

这表示 `IntentType` 只能取这 5 个字符串之一，不能随便写其他值。

在你的 Agent 项目里，它很适合用来限制意图分类结果：

```python
class IntentResult(BaseModel):
    intent: IntentType
    reason: str
```

可以把它类比成 Java 里的 `enum`：

```java
public enum IntentType {
    KNOWLEDGE_QUESTION,
    TICKET_QUERY,
    TICKET_CREATE,
    ASSET_QUERY,
    SMALLTALK
}
```

简单记：

```text
Literal = 这个字段只能取指定的几个固定值
```
