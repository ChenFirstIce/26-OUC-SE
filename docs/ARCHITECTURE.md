# 系统架构说明

更新时间：2026-09-15（modules/ 清理后）

## 后端结构

后端位于 `server/app/`，采用扁平分层架构：

```
server/app/
├── main.py              # FastAPI 应用入口，注册所有路由
├── models.py            # 所有数据库模型（统一定义）
├── seed.py              # 数据库初始化种子数据
├── core/                # 核心功能
│   ├── config.py        # 配置管理
│   ├── database.py      # 数据库连接（Base/engine/SessionLocal）
│   ├── dependencies.py  # 依赖注入
│   └── security.py      # 认证和加密
├── routers/             # API 路由层（main.py 注册的唯一入口）
│   ├── admin.py         # 管理员：部门、用户、审计日志、LLM 配置
│   ├── assignments.py   # 派发与任务管理
│   ├── assisted_tasks.py # C/B 辅助任务
│   ├── auth.py          # 认证登录
│   ├── patient_session.py # 患者会话（验证、任务包、草稿、提交）
│   ├── patients.py      # 患者档案
│   ├── questionnaires.py # 问卷模板治理（预览/导入/发布/停用）
│   └── statistics.py    # 统计报表
└── services/            # 业务逻辑服务层
    ├── assignment.py    # 派发逻辑
    ├── audit.py         # 审计日志
    ├── deepseek.py      # DeepSeek LLM 集成
    ├── llm_config.py    # LLM 凭据加密存储
    ├── moca_open.py     # MoCA 开放题分析
    ├── permissions.py   # 权限检查
    ├── questionnaire.py # 问卷 schema 验证
    ├── questionnaire_governance.py # 问卷版本治理
    ├── review_rules.py  # 复核规则
    ├── scale_catalog.py # 量表目录
    └── scoring.py       # 计分逻辑
```

### 历史说明

2026-09-15 之前，仓库中还存在 `server/app/modules/`（yjj 分支的模块化草稿）和
`server/app/core/db.py`（与 database.py 重复）。两者均未被 main.py 使用，
已在 `7ebdbc5` 提交中删除。历史代码可通过 `backup/before-cleanup-modules`
分支查看。

### 数据库迁移

Alembic 配置在 `server/alembic/`，`env.py` 从 `app.models` 导入模型元数据。
迁移版本：

- `20260910_01_questionnaire_governance.py`
- `20260914_02_assisted_tasks.py`
- `20260914_03_assessment_review.py`
- `20260915_04_llm_provider_config.py`

## 前端结构

### 正式前端（admin-web/）

Vue 3 + Element Plus，包含医生端和患者端。完整结构说明见
[admin-web/STRUCTURE.md](../admin-web/STRUCTURE.md)。

```
admin-web/src/
├── views/
│   ├── LoginView.vue         # 医生登录
│   ├── DashboardView.vue     # 仪表盘
│   ├── PatientsView.vue      # 患者列表
│   ├── PatientDetailView.vue # 患者详情
│   ├── AssignmentsView.vue   # 派发列表
│   ├── CreateAssignmentView.vue # 创建派发
│   ├── QuestionnairesView.vue # 问卷治理
│   ├── AdminCenterView.vue   # 管理中心
│   └── patient/
│       └── PatientPortal.vue # 患者填写入口
├── components/
│   ├── DynamicQuestion.vue   # 动态题型
│   ├── patient/AssistedTask.vue # C/B 辅助任务
│   ├── ReviewEvidence.vue    # 复核证据
│   └── ...
├── layouts/StaffLayout.vue   # 医生端布局
├── stores/auth.ts            # 认证状态
└── utils/                    # 工具函数
```

### 参考原型（patient-web/c2b/Frontend/）

React + TypeScript，仅作来源参考，**不在生产环境使用**。
说明见 [patient-web/README.md](../patient-web/README.md)。

其中 `patient-web/stt_sequences_with_coordinates.json` 与
`patient-web/stt_age_thresholds.json` 被正式前端使用（STT 坐标与年龄阈值）。

## 数据库模型

所有模型定义在 `server/app/models.py`：

- User, Department - 用户和部门
- Patient - 患者档案
- QuestionnaireTemplate, QuestionnaireVersion - 问卷模板和版本
- Assignment, TaskPackage, TaskItem - 派发和任务
- Response, ResponseRevision - 答卷和草稿
- AssistedTask, AssistedTaskReview - 辅助任务和复核
- AuditLog, LlmProviderConfig - 审计日志、LLM 配置

## API 契约

详见 [contracts/API.md](../contracts/API.md)。

所有端点前缀为 `/api/v1`：

- `/api/v1/auth/*` - 认证
- `/api/v1/patients/*` - 患者管理
- `/api/v1/questionnaires/*` - 问卷治理
- `/api/v1/assignments/*` - 派发管理
- `/api/v1/patient-session/*` - 患者会话
- `/api/v1/assisted-tasks/*` - 辅助任务
- `/api/v1/statistics/*` - 统计报表
- `/api/v1/admin/*` - 管理中心
