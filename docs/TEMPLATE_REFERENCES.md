# 可直接下载的前端参考与启动方案

目标：**实际项目用官方 shadcn + Vite 搭底座；第三方项目只下载到 `.references/` 作为视觉/代码结构参考。**

# 1. 实际底座：官方 shadcn/ui + Vite

如果当前仓库没有前端工程，优先让 Codex 使用官方 CLI 初始化 Vite 项目；如果已有 Vite React 工程，按官方 Existing Project 流程接入 shadcn。

推荐组件：

- button
- card
- input
- textarea
- checkbox
- radio-group
- select
- progress
- badge
- tabs
- dialog
- alert-dialog
- sheet
- separator
- skeleton
- sonner

# 2. MIT 参考模板：shadcn-admin（管理员测试模式）

仓库：`https://github.com/draco-china/shadcn-admin.git`

特点：React + Vite + TypeScript + Tailwind + shadcn/ui，MIT；适合参考 Admin/Test Mode 的 layout、卡片、导航、响应式。

下载到参考目录，不作为项目根：

```bash
git clone --depth 1 https://github.com/draco-china/shadcn-admin.git .references/shadcn-admin
```

# 3. MIT 参考模板：Awell Intake（患者 intake / questionnaire 流程）

仓库：`https://github.com/vintasoftware/awell-intake.git`

特点：React + TypeScript + Vite，包含 patient onboarding / intake / questionnaire 方向的工程组织，MIT。适合参考患者录入流程，不需要接入其中的医疗服务依赖。

```bash
git clone --depth 1 https://github.com/vintasoftware/awell-intake.git .references/awell-intake
```

# 4. MIT 参考模板：Multi-step Form

仓库：`https://github.com/alyssonbarrera/multischema-form.git`

特点：React + Vite + TypeScript + Tailwind + shadcn/ui + React Hook Form + Zod。非常适合参考“多步骤表单 + 分步验证”的实现。

```bash
git clone --depth 1 https://github.com/alyssonbarrera/multischema-form.git .references/multischema-form
```

# 5. 可选保底：SurveyJS Form Library

仓库：`https://github.com/surveyjs/survey-library.git`，Form Library 为 MIT。

只有当自研 Assessment Engine 在时间上来不及时，才考虑把它作为普通问卷渲染保底；Boston/STT/AI 任务仍需自研。

```bash
git clone --depth 1 https://github.com/surveyjs/survey-library.git .references/surveyjs
```

# 6. Codex 使用规则

Codex 下载参考库后：

1. 不要修改 `.references/`。
2. 不要把参考库整体复制到 `src/`。
3. 只提取布局思路、表单模式、组件组合。
4. 项目自己的颜色、字号、路由、数据结构遵循 `PROJECT_SPEC.md`。
5. 第三方代码若复制具体实现，必须保留对应许可证要求；首选自己按思路重写。

# 7. 网络不可用时

跳过所有 git clone，直接使用官方 Vite + shadcn 组件完成项目；参考模板不是硬依赖。
