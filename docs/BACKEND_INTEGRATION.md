# yjj 医生端与 dl 答题能力整合说明

## 整合结论

整合以 yjj 的 FastAPI、SQLAlchemy、Vue 和版本化问卷模型为唯一正式运行架构，不再保留旧 dl 的 React + Node JSON 后端，避免两套任务 ID、状态、答案格式和计分入口并存。

旧 dl 的可复用能力已迁入 yjj 主流程：

- GDS-15 题目与正反向计分；
- ESS 八个情景与 0～3 分计分；
- 爱丁堡利手量表与 -100～100 利手指数；
- 答案完整性校验、后端权威计分和相关测试思想；
- README、启动文档、统一 API 文档的持续维护规则。

## 正式调用链

```text
Vue 医生端
  -> frontend/src/api/client.ts
  -> /api/v1/questionnaires、/patients、/assignments、/statistics
  -> backend/app/routers/*
  -> backend/app/services/*
  -> backend/app/models.py / SQLAlchemy

Vue 患者端
  -> /p/fill/{token}
  -> POST /api/v1/patient-session/verify（token + access_code）
  -> patient JWT
  -> GET tasks / GET task（首次打开记录 UTC started_at）
  -> PUT draft（answers 对象 + revision）
  -> POST submit（answers 对象 + revision + Idempotency-Key）
  -> validate_answers + score_questionnaire
  -> Response + Assessment
```

## 数据模型映射

| 业务概念 | 正式模型 | 说明 |
| --- | --- | --- |
| 医生派发单 | `AssignmentPackage` | 一次可包含多份问卷。 |
| 派发单中的单份问卷 | `AssignmentItem` | 锁定不可变 `QuestionnaireVersion`。 |
| 患者草稿/原始答案 | `Response` | `answers_json` 为 `{question_key: value}`，使用 `revision` 乐观锁。 |
| 后端计分结果 | `Assessment` | 保存总分、分域、风险、复核状态。 |
| 问卷定义 | `QuestionnaireTemplate` + `QuestionnaireVersion` | 模板可产生多个版本，只派发已发布版本。 |

问卷状态保存在版本层：`draft -> published -> retired`。发布新版本会停止旧版本的新派发，但 `AssignmentItem` 已锁定的旧版本仍可继续填写、计分和查阅。数据库结构通过 Alembic 在启动时兼容升级。

## 状态

- 任务包：`pending -> in_progress -> submitted -> reviewed`；也可能为 `revoked`、`expired`。
- 单项任务：`not_started -> draft -> submitted -> reviewed`。
- 已提交/已复核单项不可继续保存草稿。
- `duration_seconds` 从患者首次打开具体问卷起算，到正式提交为止；后端按 UTC 计算，前端仅负责本地化显示。

## 接入新增量表

1. 在 `backend/app/services/scale_catalog.py` 增加稳定 code、schema 和 scoring 配置。
2. 简单求和使用 `metadata_sum`；复杂算法在 `backend/app/services/scoring.py` 增加明确策略。
3. 在 `backend/tests/test_flow.py` 增加边界和期望分数。
4. 管理员先执行无写入预览，再导入草稿，核对版本差异并二次确认发布。
5. 医生派发返回的 `questionnaire_version_id`，患者端动态渲染，无需为每张简单量表新增页面。
6. 同步更新 README 和 `docs/API.md`。

## 问卷治理调用链

```text
目录选择/JSON 文件
  -> import-preview（结构、题型、条件、计分、来源校验）
  -> content_hash + 当前版本 + 差异摘要
  -> import（再次校验摘要与基础版本，写入 draft）
  -> versions / diff（管理员复核）
  -> publish（问卷编号 + 变更说明 + 警告确认）
  -> 原 published 版本转 retired，新版本转 published
  -> assignments 只允许新建到 published 版本
```

停用版本只改变未来派发资格，不级联修改 `AssignmentItem`、`Response` 或 `Assessment`。所有导入、发布和停用操作进入审计日志。

## 兼容提醒

`backend/app/modules/` 是 yjj 留下的分模块草案，存在 `due_at/deadline`、`patient_url/patient_link` 等字段差异。`backend/app/main.py` 当前只注册 `backend/app/routers/`，因此所有联调和文档均以后者为准。

## 整合记录

- `9e3e85b`：建立 dl 患者答题后端原型和迁入量表能力。
- `65c0c93`：建立 README、启动说明、统一接口和文档维护约定。
- `4cab2ca`：以 yjj 为主干完成 FastAPI/Vue 架构整合；yjj 分支始终只读。
- `e09911f`：首次打开问卷起算填写时长，后端统一 UTC，前端统一本地化展示。
- `7b931ca`：引入问卷版本治理、Alembic 迁移和管理端治理页面。
- `ce1378f`：按需注册 Element Plus 并拆分前端公共依赖。
- `e4fcf05`：目录和 JSON 问卷统一强制“先预览、后导入”。

逐项操作、验证结果、服务故障和恢复方法见 [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md)。
