# 阿尔茨海默病认知评估系统：患者答题端与后端

本仓库 `dl` 分支包含患者移动端 Web 和首版答题后端，已经打通：

```text
管理员派发量表 → 患者任务中心 → 逐题作答与草稿保存 → 后端校验和权威计分 → 结果及历史记录
```

当前是课程项目 MVP，不构成医学诊断系统。患者端只展示中性完成提示；正式题目、评分规则和结果解释应由医学专业人员审核。

## 1. 技术栈与当前功能

前端使用 React 19、TypeScript 5.9、Vite 7、Tailwind CSS 4 和 React Router 7。后端使用 Node.js 20 原生 HTTP 服务、本地 JSON 持久化和 `node:test`，当前无额外后端运行时依赖。

已实现演示患者入口、管理员派发、患者任务中心、配置驱动答题器、草稿保存与恢复、完成页、历史页，以及 SCD-Q9、GDS-15、ESS、爱丁堡利手量表的服务端权威计分。真实鉴权、正式数据库、Boston、STT、LLM 分析、医生复核和统计仍待实现。

## 2. 仓库结构

> 新增、删除、移动或重命名目录/关键文件时，必须在同一次修改中更新本节；接口变化时同时更新 [`docs/API.md`](docs/API.md)。

```text
.
├─ AGENTS.md
├─ README.md
├─ STARTUP.md
├─ package.json
├─ package-lock.json
├─ index.html
├─ vite.config.ts
├─ tsconfig.json
├─ tsconfig.app.json
├─ bootstrap_references.sh
├─ assets/
├─ docs/
│  ├─ API.md
│  ├─ BACKEND_INTEGRATION.md
│  ├─ INTERACTIVE_TASKS.md
│  ├─ PATIENT_SCALE_SPEC.md
│  ├─ PROJECT_SPEC.md
│  ├─ TEMPLATE_REFERENCES.md
│  ├─ plan/
│  ├─ sources/
│  └─ status/
├─ server/
│  ├─ index.mjs
│  ├─ assessments.mjs
│  ├─ assessments.test.mjs
│  ├─ store.mjs
│  └─ data/                 # 运行时生成，不提交 Git
└─ src/
   ├─ main.tsx
   ├─ App.tsx
   ├─ components/
   ├─ data/assessments/
   ├─ lib/
   ├─ pages/
   ├─ repositories/
   ├─ styles/
   └─ types/
```

### 2.1 根目录文件

| 文件 | 作用 |
| --- | --- |
| `AGENTS.md` | 仓库维护约定，规定文档同步和分支边界。 |
| `README.md` | 项目总入口：结构、职责、启动方式和对接机制。 |
| `STARTUP.md` | 精简版本地启动和演示步骤。 |
| `package.json` | 前后端启动、构建、测试脚本及前端依赖。 |
| `package-lock.json` | 锁定 npm 依赖版本。 |
| `index.html` | Vite 前端 HTML 入口。 |
| `vite.config.ts` | Vite、React、Tailwind 和 `/api` 代理配置。 |
| `tsconfig.json` | TypeScript 工程引用入口。 |
| `tsconfig.app.json` | 前端 TypeScript 严格编译选项。 |
| `bootstrap_references.sh` | 参考材料初始化脚本，非应用运行必需。 |
| `.gitignore` | 忽略依赖、构建产物、本地数据和编辑器文件。 |

### 2.2 `src/`：患者前端

| 文件/目录 | 作用 |
| --- | --- |
| `src/main.tsx` | 创建 React 根节点、引入全局样式并启动应用。 |
| `src/App.tsx` | 定义登录、任务中心、历史、管理员、答题和完成页路由。 |
| `src/styles/globals.css` | 全局主题、颜色、排版和 Tailwind 样式入口。 |
| `src/types/assessment.ts` | 题目、答案、量表、任务、草稿、结果和患者公共类型。 |

#### `src/components/`

| 文件 | 作用 |
| --- | --- |
| `AppShell.tsx` | 页面公共布局和导航外壳。 |
| `AssessmentRenderer.tsx` | 统一量表答题容器。 |
| `QuestionRenderer.tsx` | 根据题型渲染是非题、单选题等交互。 |
| `ui.tsx` | Card、按钮、状态标签、指标卡等 UI 原语。 |

#### `src/data/assessments/`

| 文件 | 作用 |
| --- | --- |
| `index.ts` | 汇总并按 ID 查找量表定义。 |
| `scd-q9.ts` | SCD-Q9 题目、选项和前端初步计分。 |
| `gds-15.ts` | GDS-15 题目及正反向初步计分。 |
| `ess.ts` | ESS 八个场景、0～3 选项和初步计分。 |
| `edinburgh-handedness.ts` | 爱丁堡利手量表及利手指数初步计算。 |

前端评分只用于即时展示和结构兼容，正式结果以后端 `server/assessments.mjs` 为准。

#### `src/pages/`

| 文件 | 路由/作用 |
| --- | --- |
| `LoginPage.tsx` | `/login`，患者端和管理员模式入口。 |
| `AdminPage.tsx` | `/admin`，患者选择、任务派发、重置和提交查看。 |
| `HomePage.tsx` | `/home`，患者任务列表和状态统计。 |
| `AssessmentIntroPage.tsx` | `/assessment/:id/intro`，量表说明。 |
| `AssessmentPage.tsx` | `/assessment/:id`，答题、草稿保存、恢复和提交。 |
| `AssessmentCompletePage.tsx` | `/assessment/:id/complete`，提交完成结果。 |
| `HistoryPage.tsx` | `/history`，患者历史提交列表。 |

#### `src/repositories/` 与 `src/lib/`

| 文件 | 作用 |
| --- | --- |
| `repositories/apiRepository.ts` | 当前数据入口，将页面操作转换为 HTTP API 请求。 |
| `repositories/mockRepository.ts` | 旧版 localStorage Mock，保留作离线和迁移参考。 |
| `lib/storage.ts` | 旧版 localStorage 封装，仅供 mockRepository 使用。 |
| `lib/cn.ts` | 合并组件 CSS class 名。 |

### 2.3 `server/`：答题后端

| 文件/目录 | 作用 |
| --- | --- |
| `server/index.mjs` | HTTP 入口、路由、请求校验、任务/草稿/提交编排。 |
| `server/assessments.mjs` | 四张量表的权威计分和答案完整性校验。 |
| `server/assessments.test.mjs` | 服务端计分及漏答校验测试。 |
| `server/store.mjs` | JSON 读取、排队写入和临时文件原子替换。 |
| `server/data/store.json` | 自动生成的本地运行数据，不提交 Git。 |

### 2.4 `docs/`：项目文档

| 文件/目录 | 作用 |
| --- | --- |
| `docs/API.md` | 前后端统一接口契约，是接口联调主文档。 |
| `docs/BACKEND_INTEGRATION.md` | 从 localStorage Mock 迁移到答题后端的说明。 |
| `docs/PROJECT_SPEC.md` | 患者端业务范围、闭环和验收规格。 |
| `docs/PATIENT_SCALE_SPEC.md` | 首批四张 A 类量表规格。 |
| `docs/INTERACTIVE_TASKS.md` | Boston、STT、AI 访谈等后续任务规格。 |
| `docs/TEMPLATE_REFERENCES.md` | UI/交互模板与参考来源。 |
| `docs/plan/前端分析.md` | 前端技术路线、页面和答题引擎分析。 |
| `docs/plan/前端构思.md` | 前端早期构思和交互方案。 |
| `docs/status/PROJECT_STATUS_2026-09-03.md` | 阶段完成情况快照。 |
| `docs/sources/README.md` | 原始材料文本化目录说明。 |
| `docs/sources/01_SCD基线量表_文本版.md` | SCD 基线量表文本整理。 |
| `docs/sources/02_Boston图片材料_状态说明.md` | Boston 图片材料状态说明。 |
| `docs/sources/03_MoCA模板_说明.md` | MoCA 模板和可实现范围说明。 |
| `docs/sources/04_评分手册_文本版.md` | 操作及评分手册文本整理。 |
| `docs/sources/05_CDR_文本版.md` | CDR 访谈材料文本整理。 |
| `docs/sources/06_ADAS-Cog_实现参考.md` | ADAS-Cog 资料与实现参考。 |

### 2.5 `assets/`：参考图片

| 文件 | 作用 |
| --- | --- |
| `gds_source_reference.png` | GDS 原始材料视觉参考。 |
| `moca_b_template.png` | MoCA-B 模板视觉参考。 |
| `stt_form_a_reference.png` | STT-A 连线任务参考。 |
| `stt_form_b_practice_reference.png` | STT-B 练习任务参考。 |
| `stt_form_b_test_reference.png` | STT-B 正式任务参考。 |

这些图片是需求和实现参考，不等同于已获得生产使用授权的公开资源。

## 3. 如何启动

环境要求：Node.js 20+，npm 10 或兼容版本。

```powershell
cd D:\Desktop\ad-ouc-master\26-OUC-SE
npm install
```

第一个终端启动后端：

```powershell
npm run dev:server
```

后端默认监听 `http://127.0.0.1:3001`，健康检查为 `GET /api/health`。

第二个终端启动前端：

```powershell
npm run dev
```

浏览器打开 Vite 输出地址，通常为 `http://localhost:5173`。

测试与构建：

```powershell
npm run test:server
npm run build
```

生产方式启动后端：

```powershell
npm run start:server
```

## 4. 前后端如何对接

```text
React 页面
→ src/repositories/apiRepository.ts
→ fetch /api/...
→ Vite 开发代理
→ http://127.0.0.1:3001
→ server/index.mjs
→ server/store.mjs / server/assessments.mjs
```

`vite.config.ts` 将开发环境中的 `/api` 请求代理到端口 `3001`，浏览器无需额外处理跨域。部署到不同地址时可设置：

```text
VITE_API_BASE_URL=https://example.com/api
```

核心流程：

```text
POST /api/assignments                         创建任务
GET  /api/patients/:patientId/assignments    获取任务
PUT  /api/assignments/:id/draft              保存草稿
POST /api/assignments/:id/submit             提交原始答案并计分
GET  /api/assignments/:id/submission         获取权威结果
```

完整请求、响应和错误码见 [`docs/API.md`](docs/API.md)。

## 5. npm 脚本

| 命令 | 作用 |
| --- | --- |
| `npm run dev` | 启动 Vite 前端开发服务。 |
| `npm run dev:server` | watch 模式启动答题后端。 |
| `npm run start:server` | 非 watch 模式启动答题后端。 |
| `npm run test:server` | 运行服务端计分测试。 |
| `npm run build` | TypeScript 检查并构建前端。 |
| `npm run preview` | 预览前端生产构建。 |

## 6. 文档维护约定

1. 目录或关键文件结构变化：同步更新 README 第 2 节；
2. 启动命令、端口或环境变量变化：同步更新 README、`STARTUP.md`；
3. API 请求、响应、错误码或行为变化：同步更新 `docs/API.md`；
4. 前后端调用链或数据源变化：同步更新 README 和 `docs/BACKEND_INTEGRATION.md`；
5. 提交前运行相关测试并核对文档路径。

## 7. 分支约定

当前工作仅在 `dl` 分支进行。未经项目负责人明确授权，不修改、合并或推送 `main`、`lfy` 等其他分支。
