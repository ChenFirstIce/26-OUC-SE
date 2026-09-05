# 患者答题端统一 API 文档

> 适用分支：`dl`  
> 开发环境 Base URL：`/api`  
> 后端地址：`http://127.0.0.1:3001`  
> 格式：除 `204 No Content` 外均为 JSON

## 1. 通用约定

时间使用 ISO 8601；演示患者 ID 为 `P001`；任务 ID 格式为 `assignment-{UUID}`。

任务状态：

```text
pending → in_progress → completed
```

统一错误结构：

```json
{
  "error": {
    "code": "ASSIGNMENT_NOT_FOUND",
    "message": "未找到评估任务"
  }
}
```

每个响应带有 `X-Request-Id` 响应头。

### 错误码

| HTTP | code | 含义 |
| --- | --- | --- |
| 400 | `ANSWERS_REQUIRED` | 缺少 answers 数组。 |
| 400 | `INVALID_ANSWER` | 单条答案结构错误。 |
| 400 | `DUPLICATE_ANSWER` | 同一题重复提交。 |
| 400 | `INCOMPLETE_ANSWERS` | 缺少题目或包含未知题目。 |
| 400 | `INVALID_ANSWER_VALUE` | 答案值不合法。 |
| 403 | `ASSIGNMENT_MISMATCH` | 患者、量表与任务不匹配。 |
| 404 | `PATIENT_NOT_FOUND` | 患者不存在。 |
| 404 | `ASSESSMENT_NOT_FOUND` | 量表不存在。 |
| 404 | `ASSIGNMENT_NOT_FOUND` | 任务不存在。 |
| 404 | `ROUTE_NOT_FOUND` | 路径不存在。 |
| 409 | `ASSIGNMENT_NOT_EDITABLE` | 已完成任务不能修改草稿。 |
| 413 | `PAYLOAD_TOO_LARGE` | 请求体超过 1 MiB。 |
| 500 | `INTERNAL_ERROR` | 未处理的服务端异常。 |

## 2. 公共数据结构

### Patient

```json
{ "id": "P001", "name": "演示患者" }
```

### AssessmentAssignment

```json
{
  "assignmentId": "assignment-550e8400-e29b-41d4-a716-446655440000",
  "patientId": "P001",
  "assessmentId": "scd-q9",
  "createdAt": "2026-09-05T08:00:00.000Z",
  "status": "pending",
  "startedAt": "2026-09-05T08:05:00.000Z",
  "completedAt": "2026-09-05T08:10:00.000Z"
}
```

`startedAt` 和 `completedAt` 根据状态可能不存在。

### AssessmentDraft

```json
{
  "assignmentId": "assignment-...",
  "patientId": "P001",
  "assessmentId": "scd-q9",
  "startedAt": "2026-09-05T08:05:00.000Z",
  "updatedAt": "2026-09-05T08:06:00.000Z",
  "answers": [{ "questionId": "q1", "value": true, "score": 0 }]
}
```

草稿 `score` 不是正式结果；正式提交时由后端重新计分。

### AssessmentSubmission

```json
{
  "assignmentId": "assignment-...",
  "patientId": "P001",
  "assessmentId": "scd-q9",
  "startedAt": "2026-09-05T08:05:00.000Z",
  "completedAt": "2026-09-05T08:10:00.000Z",
  "answers": [{ "questionId": "q1", "value": true, "score": 1 }],
  "result": { "rawScore": 7.5 },
  "metrics": { "durationMs": 300000 }
}
```

## 3. 接口清单

| 方法 | 路径 | 功能 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查。 |
| GET | `/api/patients` | 患者列表。 |
| GET | `/api/patients/current` | 当前患者。 |
| PUT | `/api/patients/current` | 切换当前患者。 |
| GET | `/api/patients/:patientId/assignments` | 患者任务列表。 |
| POST | `/api/assignments` | 派发任务。 |
| GET | `/api/assignments/:assignmentId/draft` | 读取草稿。 |
| PUT | `/api/assignments/:assignmentId/draft` | 保存一道题。 |
| POST | `/api/assignments/:assignmentId/submit` | 正式提交并计分。 |
| GET | `/api/assignments/:assignmentId/submission` | 获取任务结果。 |
| GET | `/api/submissions` | 查询提交记录。 |
| DELETE | `/api/demo` | 重置演示数据。 |

## 4. 接口详情

### `GET /api/health`

响应 `200`：

```json
{ "status": "ok" }
```

### `GET /api/patients`

响应 `200 Patient[]`。

### `GET /api/patients/current`

响应 `200 Patient`。

### `PUT /api/patients/current`

请求：

```json
{ "patientId": "P001" }
```

响应 `200 Patient`；患者不存在返回 `404 PATIENT_NOT_FOUND`。

### `GET /api/patients/:patientId/assignments`

按创建时间倒序返回 `200 AssessmentAssignment[]`。

### `POST /api/assignments`

请求：

```json
{ "patientId": "P001", "assessmentId": "gds-15" }
```

响应 `201 AssessmentAssignment`。

支持的 `assessmentId`：

```text
scd-q9
gds-15
ess
edinburgh-handedness
```

可能错误：`PATIENT_NOT_FOUND`、`ASSESSMENT_NOT_FOUND`。

### `GET /api/assignments/:assignmentId/draft`

- 有草稿：`200 AssessmentDraft`
- 无草稿：`200 null`

### `PUT /api/assignments/:assignmentId/draft`

保存或覆盖一道题，第一次保存将任务改为 `in_progress`。

请求：

```json
{
  "assignmentId": "assignment-...",
  "patientId": "P001",
  "assessmentId": "ess",
  "startedAt": "2026-09-05T08:05:00.000Z",
  "questionId": "q1",
  "value": "2"
}
```

`value` 类型为 `boolean | string | string[] | number | null`。

响应 `200 AssessmentDraft`。可能错误：`ASSIGNMENT_NOT_FOUND`、`ASSIGNMENT_MISMATCH`、`ASSIGNMENT_NOT_EDITABLE`。

### `POST /api/assignments/:assignmentId/submit`

前端提交原始答案，后端进行完整性校验和权威计分。

请求：

```json
{
  "assignmentId": "assignment-...",
  "patientId": "P001",
  "assessmentId": "scd-q9",
  "startedAt": "2026-09-05T08:05:00.000Z",
  "answers": [
    { "questionId": "q1", "value": true },
    { "questionId": "q4", "value": "sometimes" }
  ]
}
```

实际请求必须包含该量表全部题目。

- 首次提交：`201 AssessmentSubmission`
- 重复提交：`200 AssessmentSubmission`，返回首次结果

成功后服务端重新计分、保存答案和结果、删除草稿并将任务改为 `completed`。

可能错误：`ANSWERS_REQUIRED`、`INVALID_ANSWER`、`DUPLICATE_ANSWER`、`INCOMPLETE_ANSWERS`、`INVALID_ANSWER_VALUE`、`ASSIGNMENT_MISMATCH`、`ASSIGNMENT_NOT_FOUND`。

### `GET /api/assignments/:assignmentId/submission`

- 已提交：`200 AssessmentSubmission`
- 未提交：`200 null`

### `GET /api/submissions`

按完成时间倒序返回 `200 AssessmentSubmission[]`。

可选查询：

```http
GET /api/submissions?patientId=P001
```

### `DELETE /api/demo`

重置默认患者并清空任务、草稿和提交。响应 `204 No Content`。该接口仅限本地演示。

## 5. 前端方法映射

| `apiRepository` 方法 | 接口 |
| --- | --- |
| `getCurrentPatient()` | `GET /patients/current` |
| `setCurrentPatient(id)` | `PUT /patients/current` |
| `getPatients()` | `GET /patients` |
| `getAssignments(id)` | `GET /patients/:id/assignments` |
| `createAssignment(...)` | `POST /assignments` |
| `getDraft(id)` | `GET /assignments/:id/draft` |
| `saveDraft(...)` | `PUT /assignments/:id/draft` |
| `submitAssessment(...)` | `POST /assignments/:id/submit` |
| `getLatestSubmission(id)` | `GET /assignments/:id/submission` |
| `getSubmissions(id?)` | `GET /submissions` |
| `resetAllDemoData()` | `DELETE /demo` |

表中接口省略统一 `/api` 前缀。

## 6. 下一版本计划

- 增加 `/api/v1` 版本前缀；
- 增加登录、令牌和角色鉴权；
- 增加 `assessmentVersionId`；
- 增加草稿 `revision`/`If-Match`；
- 增加提交 `Idempotency-Key`；
- 增加分页和标准分页响应；
- 增加 Boston/STT 过程事件 API；
- 增加 LLM 会话和异步分析 API；
- 增加医生复核、统计和审计 API。
