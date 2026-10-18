# kegxthy / Agent Lab

面向企业办公 Agent 与 B 端 Skills 创作的独立产品 MVP。新建求职作品不代表原实习公司的系统或业绩。

## 运行
Node.js 22+，无第三方依赖。

```bash
npm start
npm test
```

访问 http://localhost:3000。浏览器模式不调用模型。

## 五个模块当前范围
- 财务：明确 key=value 字段、工具计算、来源行号、规则预警、可选 DeepSeek 解释。没有自动解析 PDF，也不是完全自主规划 Agent。
- 商品图：手动裁切、边缘连通背景移除、白底或透底 PNG 下载。复杂抠图、主体内 Logo 修复和多角度生成尚未实现；多角度仅导出任务方案。
- 搜索：6 条合成商品、规则或 DeepSeek 意图解析、预算/库存/品类/偏好硬过滤。未接真实商品或向量库。
- 标签：基于明确字段的受控词表、拒绝原因、人工确认后导出；DeepSeek 可生成审核说明。
- Skills：文字事实转 SKILL.md；可选截图视觉观察需要另配可用的视觉模型。预览截图不等于识别截图。导出内容需要人工确认。

## Render Free 部署
仓库根目录构建命令：node --check agent-lab/server.mjs && node --check agent-lab/public/app.mjs && node --test agent-lab/test.mjs
启动命令：node agent-lab/server.mjs
使用单个 Free Web Service 承载五个模块，无需数据库。

## 服务端环境变量
- DEEPSEEK_API_KEY：仅在 Render Environment 中填写。
- DEEPSEEK_MODEL：默认 deepseek-flash，可按账号可用模型调整。
- DEMO_ACCESS_TOKEN：至少 24 字符的自定义随机口令；前端填写同一口令，不能用模型 Key 代替。
- DEEPSEEK_VISION_MODEL：可选，填写账号实际支持图片输入的模型 ID；未设置时明确拒绝截图识别。
- MAX_LLM_PER_HOUR：默认 30，每个实例的内存窗口限额，重启后重置，不是严格的持久化费用上限。
- ALLOWED_ORIGINS：额外前端来源，默认 https://kegxthy.github.io；服务同源请求也允许。

Key 配好后，在网页“模型连接设置”里填写访问口令并勾选真实调用。接口失败会明确报错，不悄悄返回模拟结果。

## 人工审核与数据边界
不持久保存用户输入；浏览器图像处理不上传图片。选择真实调用会将文字（以及明确选择的截图）发至 DeepSeek。不要上传内部平台截图或真实财务材料。财务规则阈值未经过统计验证，模型输出为待审核草案。

## 产品经理交付
核心假设：受约束的工具工作流能减少重复整理工作。验收关注字段证据、预算硬约束、标签拒绝理由、模型失败降级和明确的人工确认。评估数据、用户访谈、线上实验与量化成果尚未收集，不宣称已完成。

费用参考：[Render Free](https://render.com/docs/free)；闲置 15 分钟后休眠，模型 API 另计费。
