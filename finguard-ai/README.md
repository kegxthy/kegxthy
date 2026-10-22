# FinGuard AI V1

**中文** | [English](README_EN.md)

面向财务、风控与研究人员的独立财报分析工作台。仅开发本目录，不合并仓库中的其他项目。工程模块化和文档组织参考 [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)，不复制其代码。

## 功能

- PDF / DOCX / XLSX 原文提取，页、段落、表格行、工作表行定位。
- DeepSeek 分块结构化提取；校验引句及数字，再由用户确认期间、币种、倍率和合并口径。
- Python Decimal 计算四项比率，透明规则生成风险信号；缺失、冲突或非法分母明确提示。
- DeepSeek 在三项白名单工具间自主选择，最多四轮、每轮三次调用；不执行任意代码或访问外部网站。
- 中英切换、目标预设、自定义关注点、真实事件日志、SQLite 历史、删除、PDF 导出。

![真实本地工作台截图（未运行分析）](docs/workspace-zh.png)

## 本地启动

Python 3.12；不需要 GPU。在仓库根目录执行：

```bash
cd finguard-ai
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell 改用：.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

在当前 shell 设置 `LLM_API_KEY`（真实 DeepSeek 密钥，不要提交），可设置 `LLM_MODEL`（默认 `deepseek-flash`）。仅允许官方 `https://api.deepseek.com`。示例文件不会自动加载；需自行设置环境变量。

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
```

打开 http://127.0.0.1:8000，`/health` 查看配置，`/docs` 查看自动 API 文档。工作区启动必须设置至少 32 字符随机 `FINGUARD_ACCESS_TOKEN`（本机也不例外），并在网页输入。未设置令牌则启动失败。模型密钥支持 `LLM_API_KEY` 或阿里云现用的 `DEEPSEEK_API_KEY`；离线测试不需真实密钥，上传分析缺少模型密钥时返回 503。不要在聊天或仓库中提供密钥。

## 使用

1. 上传有权处理的公开非敏感财报，并明确批准发送至 DeepSeek。
2. 选择综合分析、现金流或流动性目标，也可填写自定义关注点。
3. 等待真实提取事件。进入 `needs_review` 后，勾选同一期间、同一币种的合并数据，每个字段一条。可编辑或添加带有原文引句的数据。
4. 确认后执行计算、风险规则与工具 Agent。完成后查看公式、来源、工具结果并下载 PDF。
5. 点击历史任务恢复查看；删除不再需要的任务。刷新后访问令牌需重新输入。

## 测试

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

模型在自动化测试中明确 mock；测试数据为测试夹具，绝不作为真实分析结果。真实模型与线上部署的验证状态见 [验证记录](docs/VALIDATION.md)。

## 部署

详见 [部署指南](README_DEPLOY.md)。标准入口为 `server:app`；旧 `app.py` 与 `index.html` 保留供回归参考，不再作为新版部署入口。旧 `/api/analyze`、`/api/upload` 仅存在于旧应用。

新版 `/api/reports` 为异步创建任务的兼容路径，返回 202 和任务 ID；原同步结果契约已改变。用 `/api/tasks/{id}` 轮询，等待人工确认。客户端需迁移，不能继续使用旧 `workspace.html` 的同步处理逻辑。

## 限制与安全

这是单一受信工作组版本，不是多租户公共 SaaS。全部工作区 API 强制 `FINGUARD_ACCESS_TOKEN`；持令牌成员共享所有任务。令牌仅在浏览器内存，模型密钥仅在服务端。不以客户端 IP 或转发头判断授权。共享令牌不是公共用户身份系统。`FINGUARD_MODE=public_demo` 仅展示界面，禁止全部 API，不打开工作区数据库，不能上传或分析。

每文件 12 MB、PDF 最多 300 页、提取文本 60 万字符、压缩文档展开上限 40 MB；无 OCR。XLSX 公式依赖已缓存值。复杂表格语义仍需人工复核。最多两项执行中任务、100 项历史；每阶段总超时 600 秒、单次 HTTP 60 秒。只运行一个进程、一个实例；重启中的任务标记失败，等待确认与完成任务仍保留。尚无跨进程队列、自动恢复、组织级账户、加密数据库、恶意文件沙箱或自动备份。

引用匹配只验证出处、引句与数字存在，不证明模型解读正确。模型解读中包含阿拉伯数字或无效来源的条目会被丢弃；这不能证明其余解读完全忠实，必须人工核查。规则阈值为示例筛查阈值，不是违约预测、审计结论、信用评级或投资建议。不计算缺少适用模型与输入的 Z-score。

完整提取原文仅在等待确认时留存，确认、失败或中断后删除；API 从不返回完整原文，只返回候选/已选数据的证据行。期间格式为 `YYYY-MM-DD/YYYY-MM-DD`，币种必须为支持的 ISO 代码，报表口径必须为 `consolidated`。新增必填 `line_number`、`number_index`、`scope`；旧客户端必须迁移。来源行、受支持字段标签和所选数字逐项校验，仍需人工确认列与期间，不能声称已证明财务语义。

SQLite 保留关注点、确认值、证据行、事件和报告，不保存原文件；默认 `data/tasks.sqlite3`，可通过 `FINGUARD_DB` 指定。删除任务移除应用记录，但不会清除外部备份或 DeepSeek 的提供方记录。处理敏感资料前必须另行批准提供方与数据保留政策。

[架构 / 产品约定 / API / 风险定义](docs/ARCHITECTURE.md) · [代码审计](docs/AUDIT.md)

## 审查修复与阿里云部署边界

[PR 审查修复记录](docs/REVIEW_FIXES.md) · [阿里云 FC 现状与验收边界](docs/ALIYUN_FC.md)。现有杭州 `kegxthy-agent-lab` 是另一 Node.js 项目，不得覆盖，也不计为独立 FinGuard 部署。当前 Python 的 SQLite/进程内任务尚不能直接通过上传包获得 FC 的持久任务能力。

默认保留 24 小时，`FINGUARD_RETENTION_HOURS` 可设 1–168 小时；到期按创建时间清理（启动、API 访问及每分钟），状态更新不延长保留期，正在执行的阶段最多延后到结束。保存记录预算约 20 MB；定期清理、备份与恢复说明见部署指南。
