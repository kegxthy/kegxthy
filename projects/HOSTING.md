# 免费部署建议

核查日期：2026-10-18。当前作品集是纯静态页面，无需后端或模型费用。GitHub 中提供源码不等于后端已部署。

## 财务项目：Render Free

适配现有 FastAPI，而不是改写成其他运行时。

- 连接 kegxthy/kegxthy，Root Directory 设为 finguard-ai。
- Build Command：pip install -r requirements.txt
- Start Command：uvicorn app:app --host 0.0.0.0 --port $PORT
- 选择 Free 实例；先不配置模型 Key，验证示例模式。
- 如需 DeepSeek，在服务端环境变量中配置 LLM_BASE_URL、LLM_MODEL、LLM_API_KEY，勿写入网页或仓库。
- 免费服务无流量 15 分钟后休眠，唤醒约一分钟；每工作区每月共享 750 免费实例小时。
- 本地文件不能持久保存，免费 Postgres 30 天后到期，不适合作为长期作品集数据库。
- 不上传真实企业报表。公开推理接口上线前需鉴权、限流和预算控制。

官方：https://render.com/docs/free

## 可选数据库：Supabase Free

适用于标签审核、任务记录和公开样本元数据；不是现有 Python 服务的替代托管。

- 免费层每项目 500 MB 数据库、1 GB 文件存储。
- 最多 2 个活跃免费项目，闲置一周后可能暂停。
- 五个作品集模块可共享一个演示项目；表数据应按模块组织并配置访问策略。
- 当前不需要登录或保存任务，不必创建数据库。

官方：https://supabase.com/pricing

## 当前交付与尚未完成

五个项目已作为同一仓库下的独立案例目录整理，不是五个独立生产系统。网页演示采用固定合成数据，未接入图像生成、检索、打标或截图解析模型。当前没有连接 Render / Supabase 账户，未部署真实后端。

模型推理和图像生成可能计费；免费平台额度不等于免费模型调用。需要接入真实模型时，应通过平台的密钥管理配置，不通过聊天发送密钥。
