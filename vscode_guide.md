# VS Code 使用指南

## Python 项目调试

如果你要调试 `enterprise-it-agent` 这个 FastAPI 项目，可以在 `E:\agent\enterprise-it-agent\.vscode\launch.json` 放下面这段配置：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "E:/agent/enterprise-it-agent",
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

## 一键启动 FastAPI

推荐以后按这个流程启动项目：

1. 用 VS Code 打开项目根目录：

```text
E:\agent\enterprise-it-agent
```

2. 选择项目虚拟环境解释器：

```text
Ctrl+Shift+P
-> Python: Select Interpreter
-> E:\agent\enterprise-it-agent\.venv\Scripts\python.exe
```

3. 按 `F5` 启动调试。

4. 如果弹出配置选择，选择：

```text
Run FastAPI
```

5. 启动成功后访问：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

其中：

- `/health` 用来确认服务是否正常启动
- `/docs` 是 FastAPI 自动生成的 Swagger 调试页面

### 怎么用

1. 在 VS Code 里打开 `E:\agent\enterprise-it-agent`
2. 确认右下角 Python 解释器选的是项目里的 `.venv`
3. 按 `F5`
4. 选择 `Run FastAPI`

### 这个配置的作用

- 用 `uvicorn` 启动 FastAPI
- 工作目录固定到项目根目录
- 自动重载代码改动
- 在集成终端里运行，方便看日志

### 为什么不直接跑 `main.py`

FastAPI 项目更适合按模块启动：

```powershell
uvicorn app.main:app --reload
```

这样 `from app.core.config import settings` 这类包导入更稳定，也更不容易出现 `No module named 'app'`。
