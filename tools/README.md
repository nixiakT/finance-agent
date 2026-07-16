# tools

`tools/` 定义模型可调用能力及统一注册表。模型只生成工具名和 JSON 参数，真正的函数执行由 AgentLoop 完成。

## 主要入口

- `base.py`：`Tool`、`ToolRegistry` 与 `build_default_registry()`。
- `finance_tools.py`：行情、历史、财务、新闻、指标、报告、辩论和预测工具。
- `fs.py`、`more_tools.py`、`shell.py`：文件、搜索、Todo 和受限 Shell。
- `web_tools.py`：网页获取。
- `skill_tools.py`、`memory_tools.py`：Skill 与 Memory。
- `wechat_tools.py`、`scheduler_tools.py`：具有副作用的消息与调度能力。
- `security.py`：工作区路径、敏感文件、Shell 和不可信内容边界。

## 工具契约

每个工具都必须提供稳定的 `name`、清楚的 `description`、JSON Schema `parameters` 和 `run(**arguments) -> str`。新增工具应注册到 `ToolRegistry`，并为正常、错误和权限路径添加测试；不要只在提示词里声称某项能力存在。

## 安全与副作用边界

- 文件访问限制在工作区，拒绝 `.env`、`.git` 等敏感路径；写入前检查明显 secret。
- Shell 使用允许列表，并拒绝管道、重定向、命令替换和危险 Git 操作。
- 网页和金融外部文本包装为不可信数据。
- 消息发送、预测记录等操作必须返回可核验回执；最终回答不能在回执失败时声称已完成。
- 真实交易不属于工具能力，执行层会拒绝相关请求。

## 长文件读取

`fs.py` 的 `read` 支持 `start_line` 与 `line_count` 分段读取，并在结果中给出总行数和下一段起始行。Agent 应先使用 `grep` 获取行号，再读取相关区间，避免反复读取长文件前缀。
