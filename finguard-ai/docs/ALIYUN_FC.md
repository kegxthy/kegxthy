# 阿里云 FC 部署边界与验收 / Alibaba FC deployment boundary

## 已确认现状

用户确认：地域华东1（杭州），现有函数 `kegxthy-agent-lab`；自定义运行时 Node.js 20，工作目录 `/code`，启动命令 `/var/fc/lang/nodejs20/bin/node /code/fc-start.mjs`，监听 9000。模型密钥已经保存在该函数的 `DEEPSEEK_API_KEY` 环境变量，不能打印或复制到 Git/聊天。

- 现有后端：[Agent Lab](https://kegxthygent-lab-wzhcchgpbj.cn-hangzhou.fcapp.run)
- 健康检查：[health](https://kegxthygent-lab-wzhcchgpbj.cn-hangzhou.fcapp.run/health)
- 现有前端：[Agent Lab 页面](https://kegxthy.github.io/kegxthy/lab/)
- 独立 Node.js 源码：[agent-lab](https://github.com/kegxthy/kegxthy/tree/main/agent-lab)

2026-10-19（Asia/Shanghai）只读请求 `/health` 返回 HTTP 200，正文为 `status=ok`、`llm_configured=true`、`vision_configured=false`。这只证明现有 Agent Lab 接口的配置检查可用，**不是 DeepSeek 实际调用成功的证明，也不是本 PR 的 Python FinGuard 部署或验收**。

只读源码检查发现该 Node 服务提供 `/api/finance`、`/api/search`、`/api/tags`、`/api/skill`。其财务模块为另一套实现。本次未修改这些代码、未向它发分析请求、未覆盖既有函数，也未操作 Render。FC 不是 SSH/ECS 部署，不适用服务器登录命令。

## 独立 FinGuard 尚未部署

当前 `finguard-ai/` 是 Python 3.12 FastAPI：SQLite 保存任务、进程内 asyncio 执行长阶段。独立长期进程加本地持久磁盘可运行，但不能把该保证直接套用到可回收、可扩实例的 FC 运行环境。单纯上传 Python 文件、把端口改成 9000，或让 Node 转发请求，都不等于已经解决持久化、重复执行和跨实例任务状态。

阿里云文档提供 [异步任务模式](https://www.alibabacloud.com/help/en/functioncompute/asynchronous-task) 和 [任务函数](https://www.alibabacloud.com/help/en/functioncompute/creating-a-task-function)，可用于后续独立适配；NAS/OSS 挂载不能单独证明 SQLite、多实例并发或任务恢复已经可靠。当前没有实现/验证这些云端适配，不提供冒充可上线的 FC 占位启动包。

## 独立 FC 发布所需后续工作

1. 为 FinGuard 使用独立函数/应用与独立数据域，不替换 `kegxthy-agent-lab`；选择 Python 自定义运行时或自定义容器，确认杭州资源与费用。
2. 将提取和分析阶段接入持久异步调度（例如 FC task mode），并实现幂等 claim、超时/失败状态、人工确认后续阶段的安全触发。HTTP 返回之后的进程内 task 不能作为云端持久队列。
3. 使用适合并发访问的持久任务数据存储及原文短期对象存储；端到端验证 TTL、权限、删除和备份。不要假定 `/code` 或实例临时文件能跨回收保存历史。
4. 通过函数计算控制台或获得授权的 FC 部署工具发布独立资源；保持已有 Agent Lab 完整。当前会话未获得 FC 账号操作连接/CLI 授权；插件发现也未找到可用的阿里云 FC 部署连接。
5. 私密配置独立函数的模型环境变量与至少 32 字符工作区令牌。FinGuard 支持 `LLM_API_KEY` 或 `DEEPSEEK_API_KEY`，以及 `LLM_MODEL` 或 `DEEPSEEK_MODEL`；仅官方 DeepSeek 端点。已有 Node 函数内的密钥不会自动进入另一个函数或本地测试环境，不得把它读回聊天。
6. 用独立 FinGuard HTTPS URL 验证：未授权请求拒绝、真实公开年报提取、人工确认、实际工具调用记录、数字/期间/来源核查、PDF，以及实例回收/跨实例/重试后任务状态与历史持久化。

真实模型验收必须观察实际调用，而不只是 `model_ready` 或 `llm_configured` 布尔值。没有独立函数 URL、持久执行适配和部署授权前，保持 PR 草稿，记录阻塞原因，不宣称线上部署完成。

## English

The supplied Hangzhou FC URL belongs to the separate Node.js Agent Lab function. Its health endpoint returned 200 and configuration flags; no live financial/model request was made. This does not validate the Python FinGuard application.

Do not overwrite the existing function or use SSH/ECS instructions. A separate FinGuard FC release needs an appropriate Python runtime, durable stage dispatch with idempotency, persistent shared task storage, retention/cleanup, approved deployment access and a separately configured server-side key/token. The current SQLite/in-process executor has not been adapted or accepted for FC. Official task-mode documentation is linked above as an implementation direction, not a claim of completed support.
