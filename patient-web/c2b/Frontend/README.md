# 患者端 C/B 阶段功能演示

该子项目实现四个可独立演示的认知评估前端模块：

- C 类：SCD 结构化访谈、MoCA-B 开放题；
- B 类：Boston 图片命名、STT 形状连线。

所有问题、图片和评分均为 `DEMO` 占位内容，不构成医学诊断。当前默认使用 Mock API，不需要 DeepSeek Key 或后端服务。

## 本地运行

```bash
npm install
npm run dev
```

浏览器打开 Vite 输出的本地地址。入口页提供四个任务的独立路由。

## 验证

```bash
npm run typecheck
npm run test
npm run build
```

## 切换到后端代理

复制 `.env.example` 为 `.env.local`，修改：

```env
VITE_USE_MOCK_API=false
VITE_API_BASE_URL=/api
```

后端需实现：

- `POST /api/llm/session/{sessionId}/message`
- `POST /api/llm/open-answer/analyze`

接口类型和运行时校验位于 `src/api/llm.ts`。DeepSeek API Key、Prompt、会话历史和模型返回解析必须保留在后端，不得写入前端环境变量。
