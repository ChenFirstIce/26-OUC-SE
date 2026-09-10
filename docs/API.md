# 统一 API 文档

适用分支：`dl`。本文是前端、后端和测试的统一联调契约；实际正式路由位于 `backend/app/routers/`。

## 1. 通用约定

- 后端开发地址：`http://127.0.0.1:8000`
- 业务前缀：`/api/v1`
- Swagger：`GET /docs`
- 健康检查：`GET /health`，响应 `{"status":"ok","service":"..."}`
- JSON 字段使用 `snake_case`，时间使用 ISO 8601。
- 医生/管理员接口：`Authorization: Bearer {staff_access_token}`。
- 患者任务接口：`Authorization: Bearer {patient_access_token}`。
- 每个响应含 `X-Request-ID`；请求也可主动传入该头便于追踪。

统一错误：

```json
{
  "code": "HTTP_409",
  "message": "答案已在其他页面更新，请刷新后继续",
  "request_id": "uuid",
  "errors": []
}
```

`errors` 只在答案或参数具有明细错误时出现。常用状态：`401` 未登录/凭证错误，`403` 越权，`404` 不存在，`409` 状态或 revision 冲突，`410` 撤销/过期，`422` 参数或答案校验失败。

## 2. 接口总表

| 身份 | 方法 | 路径 | 用途 |
| --- | --- | --- | --- |
| 公共 | GET | `/health` | 健康检查 |
| 公共 | POST | `/api/v1/auth/login` | 医生/管理员登录 |
| 职员 | GET | `/api/v1/auth/me` | 当前身份与权限 |
| 职员 | GET/POST | `/api/v1/patients` | 患者分页列表/创建 |
| 职员 | GET/PATCH | `/api/v1/patients/{patient_id}` | 患者详情/修改 |
| 管理员 | DELETE | `/api/v1/patients/{patient_id}` | 归档患者并撤销未完成任务 |
| 职员 | GET | `/api/v1/patients/{patient_id}/analysis` | 患者纵向分析 |
| 职员 | GET/POST | `/api/v1/patients/{patient_id}/clinical-records` | 临床记录列表/创建 |
| 职员 | PATCH | `/api/v1/patients/{patient_id}/clinical-records/{record_id}` | 修改临床记录 |
| 职员 | GET | `/api/v1/questionnaires` | 可见问卷模板和最新版本 |
| 管理员 | GET | `/api/v1/questionnaires/catalog` | 内置量表目录 |
| 管理员 | POST | `/api/v1/questionnaires/import-catalog` | 从目录导入新版本 |
| 管理员 | POST | `/api/v1/questionnaires/import-package` | 导入外部 JSON 包 |
| 管理员 | POST | `/api/v1/questionnaires` | 创建模板和首版本 |
| 管理员 | POST | `/api/v1/questionnaires/{template_id}/publish` | 发布最新版本 |
| 职员 | GET/POST | `/api/v1/assignments` | 任务包列表/派发 |
| 职员 | GET/PATCH | `/api/v1/assignments/{assignment_id}` | 任务详情/修改未完成任务 |
| 职员 | POST | `/api/v1/assignments/{assignment_id}/revoke` | 撤销未提交任务 |
| 职员 | GET | `/api/v1/assignments/{assignment_id}/items/{item_id}/result` | 查看原始答案和评分 |
| 公共 | POST | `/api/v1/patient-session/verify` | 患者链接与访问码验证 |
| 患者 | GET | `/api/v1/patient-session/tasks` | 当前任务包和单项列表 |
| 患者 | GET | `/api/v1/patient-session/tasks/{item_id}` | 问卷 schema、草稿和 revision |
| 患者 | PUT | `/api/v1/patient-session/tasks/{item_id}/draft` | 全量保存草稿 |
| 患者 | POST | `/api/v1/patient-session/tasks/{item_id}/submit` | 幂等正式提交并计分 |
| 职员 | GET | `/api/v1/statistics/overview` | 总览指标 |
| 职员 | GET | `/api/v1/statistics/funnel` | 任务状态漏斗 |
| 职员 | GET | `/api/v1/statistics/questionnaires` | 各问卷完成率 |
| 职员 | GET | `/api/v1/statistics/risks` | 风险分布 |
| 职员 | GET | `/api/v1/statistics/score-summary` | 各量表分数摘要 |
| 职员 | GET | `/api/v1/exports/assessments.csv` | 导出授权范围内评估结果 |
| 职员 | GET | `/api/v1/admin/departments` | 科室列表 |
| 管理员 | POST/PATCH | `/api/v1/admin/departments[/{id}]` | 新建/修改科室 |
| 管理员 | GET/POST | `/api/v1/admin/users` | 账号列表/创建 |
| 管理员 | PATCH | `/api/v1/admin/users/{user_id}` | 账号、密码和权限修改 |
| 管理员 | GET | `/api/v1/admin/audit` | 审计分页列表 |

## 3. 登录

### `POST /api/v1/auth/login`

```json
{ "username": "doctor1", "password": "Doctor123!" }
```

成功响应：

```json
{ "access_token": "jwt", "token_type": "bearer" }
```

前端将 token 存入 `localStorage.staff_token`。`GET /auth/me` 返回用户、科室、角色和 `can_create_patients`、`can_assign_questionnaires`、`can_review_results`、`can_manage_templates` 权限。

## 4. 患者主档与临床记录

### `GET /api/v1/patients?page=1&page_size=20&keyword=`

响应：

```json
{ "items": [{ "id": 1, "patient_code": "P0001", "full_name": "演示患者", "doctor_name": "演示医生1" }], "total": 1, "page": 1, "page_size": 20 }
```

医生只能看到本人患者；管理员可看全部。

### `POST /api/v1/patients`

最小请求：

```json
{ "patient_code": "P1001", "full_name": "匿名患者" }
```

可选字段：`sex`、`birth_date`、`education_level`、`residence_type`、`phone`、`marital_status`、`occupation`、`chief_concern`、`past_medical_history`、`family_history`、`current_medications`、`allergy_history`、`emergency_contact`、`emergency_phone`。成功为 `201`。

`PATCH /patients/{id}` 只提交需要修改的字段。`DELETE /patients/{id}` 仅管理员可用，执行逻辑归档。

### 临床记录

创建：

```json
{
  "record_type": "follow_up",
  "title": "阶段随访",
  "diagnosis_code": null,
  "content": "情况稳定，计划复评。",
  "event_at": "2026-09-10T09:00:00+08:00"
}
```

`record_type`：`diagnosis | follow_up | treatment | note`。修改接口还接受 `status: active | archived`。

## 5. 问卷模板、Schema 与版本

问卷创建/导入结构：

```json
{
  "code": "CUSTOM_SCALE",
  "name": "自定义问卷",
  "description": "说明",
  "questionnaire_schema": {
    "title": "自定义问卷",
    "administration_mode": "patient_self",
    "notice": "填写提示",
    "sections": [{
      "key": "section_1",
      "title": "第一部分",
      "questions": [{
        "key": "q1",
        "type": "single_choice",
        "label": "题目",
        "required": true,
        "dimension": "维度",
        "options": [{ "value": "yes", "label": "是", "score": 1 }]
      }]
    }]
  },
  "scoring_json": { "strategy": "metadata_sum", "risk_thresholds": [] }
}
```

支持题型：`short_text`、`long_text`、`integer`、`number`、`date`、`time`、`duration`、`yes_no`、`single_choice`、`multi_choice`、`scale`。条件显示：`show_if: {question_key, equals}`。

计分策略：

- `metadata_sum`：按 option.score 或 `score_numeric` 求和；
- `manual_review`：不自动给总分，进入人工复核；
- `laterality_index`：爱丁堡利手指数专用。

内置目录 code：`OUC_SCD_Q9`、`OUC_MMSE`、`OUC_FAQ`、`OUC_MOCA_B`、`OUC_CDR`、`OUC_ADAS_COG`、`OUC_GDS_15`、`OUC_ESS`、`OUC_EDINBURGH`。

目录导入：

```json
{ "codes": ["OUC_GDS_15", "OUC_ESS", "OUC_EDINBURGH"], "publish": false }
```

建议先以草稿导入、核对来源与计分，再调用 `/questionnaires/{template_id}/publish`。外部包导入请求为 `{templates: [...], conflict_strategy: "new_version|skip|error", publish: false}`。

## 6. 医生派发

### `POST /api/v1/assignments`

```json
{
  "patient_id": 1,
  "questionnaire_version_ids": [3, 4, 5],
  "title": "基线筛查",
  "note": "请在本周内完成",
  "deadline": "2026-09-17T23:59:59+08:00"
}
```

只能派发已发布版本。成功为 `201`：

```json
{
  "id": 8,
  "status": "pending",
  "patient_link": "http://.../p/fill/raw-token",
  "access_code": "123456",
  "token": "raw-token",
  "items": [{ "id": 20, "questionnaire_version_id": 3, "questionnaire_code": "OUC_GDS_15", "status": "not_started" }]
}
```

`token` 和 `access_code` 只在创建响应中返回，前端应立即展示/安全传递，不记录到普通日志。管理员可选传 `doctor_id`；普通医生不可替他人派发。

## 7. 患者答题（核心对接）

### 7.1 验证

`POST /api/v1/patient-session/verify`：

```json
{ "token": "患者链接中的原始 token", "access_code": "123456" }
```

响应 `{access_token, token_type, assignment}`。前端保存到 `sessionStorage.patient_token`，后续接口使用 Bearer token。

### 7.2 任务与问卷

`GET /patient-session/tasks` 返回：

```json
{
  "assignment": { "id": 8, "title": "基线筛查", "status": "in_progress", "patient_code": "P0001", "doctor_name": "演示医生1" },
  "items": [{ "id": 20, "status": "draft", "name": "GDS-15", "code": "OUC_GDS_15", "version": 1 }]
}
```

`GET /patient-session/tasks/{item_id}` 返回 `{id,status,name,description,schema,answers,revision}`。`answers` 是按题目 key 索引的对象，而不是数组：

```json
{ "gds_1": "yes", "gds_2": "no" }
```

### 7.3 保存草稿

`PUT /patient-session/tasks/{item_id}/draft`：

```json
{ "answers": { "gds_1": "yes" }, "revision": 0 }
```

成功返回 `{ "saved": true, "revision": 1 }`。前端下一次保存和提交必须使用返回的新 revision；旧 revision 返回 `409`，前端应提示刷新，不能静默覆盖。

### 7.4 正式提交

`POST /patient-session/tasks/{item_id}/submit` 必须携带：

```http
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

```json
{ "answers": { "gds_1": "yes", "gds_2": "no" }, "revision": 1 }
```

实际 answers 必须满足当前锁定 schema 的全部可见必答题。成功响应：

```json
{
  "id": 12,
  "questionnaire_code": "OUC_GDS_15",
  "total_score": 5,
  "dimension_scores": { "情绪状态": 5 },
  "risk_level": "unknown",
  "review_status": "auto"
}
```

相同 `Idempotency-Key` 重试返回首次结果，不创建重复评估；不同键重复提交返回 `409`。前端不得上传或覆盖分数，正式结果只由后端根据任务锁定版本生成。

## 8. 统计与权限

统计接口均自动按医生数据范围过滤；管理员查看全局。`score-summary` 返回量表的次数、平均/最小/最大分和中高风险数。CSV 导出字段为 `patient_code, questionnaire_code, total_score, risk_level, review_status, assessed_at`。

管理员权限对象字段：

```json
{
  "can_create_patients": true,
  "can_assign_questionnaires": true,
  "can_review_results": true,
  "can_manage_templates": false
}
```

审计列表支持 `page`、`page_size`，记录 actor、action、target、result 和时间。

## 9. 前端方法映射

`frontend/src/api/client.ts` 的 Axios Base URL 已固定为 `/api/v1`；Vite 只负责把 `/api` 代理到 8000。患者路由 `/p/*` 自动取 `sessionStorage.patient_token`，其他页面取 `localStorage.staff_token`。

关键页面映射：

| 页面 | 接口 |
| --- | --- |
| `LoginView.vue` | `/auth/login`、`/auth/me` |
| `PatientsView.vue` / `PatientDetailView.vue` | `/patients*` |
| `QuestionnairesView.vue` | `/questionnaires*` |
| `CreateAssignmentView.vue` / `AssignmentsView.vue` | `/assignments*` |
| `PatientPortal.vue` | `/patient-session/verify`、`tasks`、`draft`、`submit` |
| `DashboardView.vue` | `/statistics/*`、`/exports/assessments.csv` |
