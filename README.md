# 阿尔茨海默症筛查问卷与数据统计系统

`dl` 分支已以 `yjj` 的医生派发工作流为主干完成整合：医生/管理员使用 Vue 管理端创建患者和派发问卷；患者通过链接与 6 位访问码进入移动答题端；FastAPI 后端保存草稿、校验并计分，再向医生端提供结果与统计。

> 医学声明：本仓库用于课程开发与流程验证，自动评分不等于诊断。正式临床使用前必须完成量表授权、评分规则、数据合规和专业人员复核。

## 1. 工作流与对接边界

```text
管理员导入并发布问卷版本
  -> 医生创建患者
  -> 医生选择一个或多个 questionnaire_version_id 创建任务包
  -> 后端生成患者链接 + 随机 token + 6 位访问码
  -> 患者验证后获得短期 patient JWT
  -> 患者读取任务、按 answers 对象自动保存草稿（revision 乐观锁）
  -> 患者使用 Idempotency-Key 正式提交
  -> 后端校验必答题、按已锁定问卷版本计分并保存 Assessment
  -> 医生查看原始答案/结果，统计页和 CSV 同步更新
```

统一 API 前缀为 `/api/v1`。实际运行入口是 `backend/app/routers/` + `backend/app/services/` + `backend/app/models.py`；`backend/app/modules/` 是 yjj 保留的分模块草案，不由 `app/main.py` 注册，联调时不要调用其中的旧字段或旧路由。

## 2. 第一次运行

环境要求：Python 3.12、Node.js 20+、PowerShell 5/7。

```powershell
Set-Location D:\Desktop\ad-ouc-master\26-OUC-SE
.\scripts\setup.ps1
.\scripts\start.ps1
```

启动成功后：

- 医生/管理端：<http://127.0.0.1:5173/login>
- 患者演示端：以启动脚本输出的局域网地址为准
- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

演示账号：医生 `doctor1 / Doctor123!`，管理员 `admin / Admin123!`；演示患者访问码 `123456`。

停止和检查：

```powershell
.\scripts\stop.ps1
.\scripts\test.ps1
```

单独启动后端或前端见 [STARTUP.md](STARTUP.md)。完整接口契约见 [docs/API.md](docs/API.md)。

## 3. 当前目录结构

```text
26-OUC-SE/
├─ backend/                 FastAPI、SQLAlchemy、测试
├─ frontend/                Vue 3 医生端、管理端、患者答题端
├─ scripts/                 Windows 初始化、启动、停止、测试脚本
├─ samples/                 问卷 JSON 导入示例
├─ docs/                    统一接口与前后端对接文档
├─ assets/                  历史临床材料视觉参考，不参与运行
├─ .env.example             环境变量示例
├─ .gitignore               本地依赖、运行数据和构建产物忽略规则
├─ AGENTS.md                dl 分支协作、文档同步和测试约定
├─ STARTUP.md               本地启动与演示流程
└─ README.md                项目总入口和结构归档
```

### 3.1 `backend/`

| 文件/目录 | 作用 |
| --- | --- |
| `backend/run.py` | 使用 Uvicorn 启动后端。 |
| `backend/requirements.txt` | FastAPI、SQLAlchemy、JWT、测试等 Python 依赖。 |
| `backend/app/main.py` | 创建应用、CORS、请求 ID、统一错误处理、数据库初始化和正式路由注册。 |
| `backend/app/models.py` | 用户、权限、患者、问卷版本、任务包、答卷、评估、临床记录、审计表。 |
| `backend/app/seed.py` | 初始化匿名演示科室、账号、患者、问卷与演示任务。 |
| `backend/app/__init__.py` | Python 包标识。 |

`backend/app/core/`：

| 文件 | 作用 |
| --- | --- |
| `config.py` | `/api/v1`、数据库、JWT 时长、前端地址等配置。 |
| `database.py` | 正式 SQLAlchemy Engine、Session 和 Base。 |
| `dependencies.py` | 医生/管理员/患者 JWT 身份与数据范围依赖。 |
| `security.py` | 密码哈希、JWT、任务 token 和访问码安全函数。 |
| `api.py`、`db.py` | yjj 早期公共接口/数据库草案，正式入口当前不引用。 |
| `__init__.py` | 包标识。 |

`backend/app/routers/`（正式 API）：

| 文件 | 作用 |
| --- | --- |
| `auth.py` | 医生/管理员登录与当前身份。 |
| `patients.py` | 患者主档、纵向分析、临床记录与归档。 |
| `questionnaires.py` | 模板、版本、内置目录导入和发布。 |
| `assignments.py` | 医生派发任务包、查看、修改、撤销和结果读取。 |
| `patient_session.py` | 患者验证、任务读取、草稿 revision、幂等提交与计分。 |
| `statistics.py` | 概览、漏斗、量表、风险、分数统计和 CSV 导出。 |
| `admin.py` | 科室、账号、权限和审计管理。 |
| `__init__.py` | 路由包标识。 |

`backend/app/services/`：

| 文件 | 作用 |
| --- | --- |
| `assignment.py` | 任务过期判断和任务包状态汇总。 |
| `audit.py` | 记录关键操作审计。 |
| `permissions.py` | 独立业务权限读取与校验。 |
| `questionnaire.py` | 动态问卷题型、条件显示、Schema 和答案校验。 |
| `scale_catalog.py` | 内置量表目录；含 yjj 原目录和从 dl 迁入的 GDS-15、ESS、爱丁堡利手量表。 |
| `scoring.py` | 后端权威计分；支持元数据求和、人工复核和利手指数。 |
| `__init__.py` | 服务包标识。 |

`backend/app/modules/` 是未接入正式运行入口的 yjj 领域化草案。其 `auth/`、`users/`、`departments/`、`patients/`、`questionnaires/`、`assignments/`、`assessments/`、`scoring/`、`audit/` 子目录中的 `models.py`、`router.py`、`schemas.py`、`service.py` 仅作后续重构参考；当前实现以同名 `routers/`、`services/` 和根 `models.py` 为准。

| 文件 | 作用 |
| --- | --- |
| `backend/tests/test_flow.py` | 覆盖登录、权限、患者、派发、患者答题、草稿冲突、幂等提交、统计、目录导入及迁入量表计分。 |

### 3.2 `frontend/`

| 文件/目录 | 作用 |
| --- | --- |
| `frontend/package.json`、`package-lock.json` | Vue/Vite/Element Plus/ECharts/Axios 依赖及脚本。 |
| `frontend/index.html` | Vite HTML 入口。 |
| `frontend/vite.config.ts` | 前端端口 5173，并把 `/api`、`/health` 代理到 8000。 |
| `frontend/tsconfig.json`、`tsconfig.app.json`、`tsconfig.node.json` | TypeScript 工程配置。 |
| `frontend/src/main.ts` | Vue 应用、路由、Pinia、Element Plus 初始化。 |
| `frontend/src/App.vue` | 根组件。 |
| `frontend/src/router.ts` | 医生、管理员、患者路由与鉴权守卫。 |
| `frontend/src/styles.css`、`advanced.css` | 全局和增强页面样式。 |
| `frontend/src/api/client.ts` | Axios `/api/v1` 客户端，自动选择 staff/patient token。 |
| `frontend/src/stores/auth.ts` | 医生/管理员登录状态和身份。 |
| `frontend/src/layouts/StaffLayout.vue` | 医生/管理员公共布局。 |
| `frontend/src/utils/idempotency.ts` | 为正式提交生成幂等键。 |
| `frontend/src/utils/patient.ts` | 患者显示辅助函数。 |
| `frontend/src/components/DynamicQuestion.vue` | 动态渲染文本、数字、日期、时间、是非、单选、多选和量表题。 |
| `frontend/src/components/QuestionnaireDetailDialog.vue` | 问卷结构详情弹窗。 |
| `frontend/src/components/ChartPanel.vue` | 统计图容器和导出。 |
| `frontend/src/components/StatCard.vue` | 统计指标卡。 |
| `frontend/src/views/LoginView.vue` | 医生/管理员登录页。 |
| `frontend/src/views/DashboardView.vue` | 数据总览与统计图。 |
| `frontend/src/views/PatientsView.vue` | 患者列表和创建。 |
| `frontend/src/views/PatientDetailView.vue` | 患者主档、评估时间线和临床记录。 |
| `frontend/src/views/QuestionnairesView.vue` | 问卷目录导入、模板管理和发布。 |
| `frontend/src/views/CreateAssignmentView.vue` | 选择患者与问卷版本，创建任务并显示链接/二维码/访问码。 |
| `frontend/src/views/AssignmentsView.vue` | 任务包查询、状态和管理。 |
| `frontend/src/views/AdminCenterView.vue` | 科室、账号、权限和审计管理。 |
| `frontend/src/views/patient/PatientPortal.vue` | 患者验证、任务列表、动态答题、5 秒自动保存和幂等提交。 |

### 3.3 其他目录

| 文件/目录 | 作用 |
| --- | --- |
| `scripts/setup.ps1` | 安装前后端依赖并初始化数据库。 |
| `scripts/start.ps1` | 检查端口，后台启动两端，生成局域网患者链接并健康检查。 |
| `scripts/stop.ps1` | 根据 `.runtime` PID 停止服务。 |
| `scripts/test.ps1` | 执行后端 pytest 与前端生产构建。 |
| `samples/questionnaire-template.example.json` | 外部问卷包 JSON 示例。 |
| `docs/API.md` | 唯一统一接口契约。 |
| `docs/BACKEND_INTEGRATION.md` | yjj 医生派发端与 dl 患者答题能力的整合决策。 |
| `assets/gds_source_reference.png` | GDS 历史原始材料视觉参考，不被应用加载。 |
| `assets/moca_b_template.png` | MoCA-B 模板视觉参考，不被应用加载。 |
| `assets/stt_form_a_reference.png` | STT-A 连线材料参考，不被应用加载。 |
| `assets/stt_form_b_practice_reference.png` | STT-B 练习材料参考，不被应用加载。 |
| `assets/stt_form_b_test_reference.png` | STT-B 正式材料参考，不被应用加载。 |

## 4. 问卷扩展方式

简单量表通过 `questionnaire_schema` + `scoring_json` 扩展，无需修改患者页面。管理员先查看 `GET /api/v1/questionnaires/catalog`，再调用 `POST /api/v1/questionnaires/import-catalog` 导入为版本，核对后发布，医生才能派发。

本次从旧 dl 答题端迁入：

| code | 题数 | 后端计分 |
| --- | ---: | --- |
| `OUC_GDS_15` | 15 | 是/否正反向元数据求和 |
| `OUC_ESS` | 8 | 每题 0～3 分求和 |
| `OUC_EDINBURGH` | 10 | `(右手累计-左手累计)/(两侧累计)*100` |

完整字段和调用示例见 [docs/API.md](docs/API.md)。

## 5. 数据与安全

- 默认 SQLite 位于 `%TEMP%\ad_questionnaire_data\ad_questionnaire.db`，可用 `DATABASE_URL` 指向其他 ASCII 路径；切换 PostgreSQL 时还需安装对应 SQLAlchemy 驱动。
- 生产前必须更换 `JWT_SECRET`、演示密码和访问机制。
- 患者任务使用随机 token + 访问码，验证成功后才签发有限时长的 patient JWT。
- 医生只能访问自己负责的患者；管理员拥有跨医生管理权限。
- 不要向演示环境录入真实身份、联系方式或病历数据。

## 6. 文档与分支约定

1. 目录或关键文件变化时同步更新本 README。
2. 命令、端口或环境变量变化时同步更新 README 和 `STARTUP.md`。
3. API 变化时同步更新 `docs/API.md`。
4. 调用链或数据源变化时同步更新 `docs/BACKEND_INTEGRATION.md`。
5. 所有开发、提交和允许的推送仅在 `dl`；未经负责人授权不得修改或推送其他分支。
