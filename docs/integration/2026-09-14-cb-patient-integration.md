# C/B 辅助任务患者系统整合记录

日期：2026-09-14

基础版本：`origin/main`（当前集成工作区分支 `cyf`）

范围：仅处理“C/B 功能未进入正式患者系统”问题；不在本次更新中补齐所有量表题目，也不把人工复核量表改造成自动评分量表。

## 1. 更新背景

更新前，`main` 中已经存在四个 C/B 功能页面，但它们位于独立 React 工程 `patient-web/c2b/Frontend/`，需要单独启动 5174 端口。该工程使用 Mock 数据和浏览器本地状态，不使用正式患者链接与访问码，不属于医生派发的任务包，也不会把过程数据写入正式患者数据库。因此，患者从邓林实现的 `admin-web` 正式入口进入时看不到这四项任务，医生端也无法查看对应记录。

本次更新以邓林的 Vue + FastAPI + SQLAlchemy 患者闭环为运行基础，将四项交互改写并接入正式患者系统。原 React 工程继续保留，作为 main 来源和界面逻辑参考，不再作为正式入口。

## 2. 本次整合的四项任务

| 分类 | 任务 | 当前记录内容 | 提交后状态 |
| --- | --- | --- | --- |
| C 类 | SCD 结构化访谈（DEMO） | 患者与助手消息、会话进度、完成状态 | 待医生复核 |
| C 类 | MoCA-B 开放回答（DEMO） | 原始自然语言回答、任务用时、AI 候选状态 | 待医生复核 |
| B 类 | Boston 图片命名（DEMO） | 逐题回答、提示使用情况、单题及总用时 | 程序核验后待医生确认 |
| B 类 | STT 形状连线（DEMO） | 点击顺序、时间戳、正确性、错误次数和总用时 | 程序核验后待医生确认 |

四项任务的正式编码为 `DEMO_SCD_INTERVIEW`、`DEMO_MOCA_OPEN`、`DEMO_BOSTON` 和 `DEMO_TRAIL`。它们随演示数据初始化为已发布版本，可以由医生正常派发，也会加入 `demo-patient-token` 对应的演示任务包。

## 3. 更新前后对比

| 能力 | 更新前 | 更新后 |
| --- | --- | --- |
| 患者入口 | 5174 独立 React 演示 | 统一使用 `/p/fill/:token` |
| 身份验证 | 无正式患者身份 | 链接 token + 6 位访问码 + 患者 JWT |
| 医生派发 | 不支持 | 使用正式问卷版本和任务包派发 |
| 草稿恢复 | 浏览器本地状态 | 后端草稿、revision 和冲突保护 |
| 正式提交 | 不进入正式系统 | 使用幂等键提交并锁定答卷 |
| 数据保存 | 浏览器本地 | SQLite/正式配置数据库 |
| 医生查看 | 不支持 | 任务结果页查看原始过程与核验状态 |
| C 类候选结果 | Mock 页面内生成 | 与最终结果分层保存，不返回患者端 |
| 服务端口 | 8000、5173、5174 | 正式运行只需 8000、5173 |

## 4. 前端改动

新增 `admin-web/src/components/patient/AssistedTask.vue`，在一个 Vue 组件中承载四类专用交互。`PatientPortal.vue` 根据问卷版本的 `administration_mode` 判断任务类型：普通结构化问卷继续使用 `DynamicQuestion`，`assisted_task` 和 `interview_assisted` 则进入 C/B 专用组件。

患者仍从同一任务列表开始或继续任务。C/B 页面复用正式 Axios 客户端和患者 Bearer Token，使用现有草稿接口保存状态，提交成功后返回任务列表并刷新完成状态。医生端 `AssignmentsView.vue` 增加了 C/B 原始 JSON 过程数据、程序核验结果和 AI 候选状态展示。

## 5. 后端与数据模型改动

新增路由 `server/app/routers/assisted_tasks.py`，提供：

```text
POST /api/v1/patient-session/tasks/{item_id}/assisted-submit
POST /api/v1/patient-session/tasks/{item_id}/llm/sessions/{session_id}/messages
```

`assisted-submit` 接受 `answers`、`revision` 和 `metrics`，并要求 `Idempotency-Key`。服务端会再次核对任务是否属于当前患者任务包，并对 Boston 与 STT 过程数据进行基本完整性核验。患者响应只包含提交凭据、状态和中性提示，不包含程序得分或 AI 候选结果。

评估数据新增三个分层字段：

- `auto_result_json`：B 类程序核验产生的暂定结果；
- `candidate_result_json`：C 类 AI 辅助产生的候选状态或建议；
- `final_result_json`：预留给医生最终确认，患者提交时保持为空。

同时新增 `llm_sessions` 和 `llm_messages` 表，用于保存访谈会话进度与消息证据。迁移文件为 `server/alembic/versions/20260914_02_assisted_tasks.py`，兼容仅包含问卷治理表的历史测试数据库。

问卷治理新增 `assisted_task` 和 `interview_assisted` 两种施测模式。医生创建患者任务时，后端会拒绝将纯 `clinician` 模式的版本派发到患者端。

## 6. 安全与临床边界

本次更新完成的是系统接入和数据闭环，不代表四项任务已经成为正式临床量表。系统继续保留 `DEMO` 标识，原因如下：

- Boston 当前只有三道占位题，使用 Emoji 演示图，不是正式授权图片材料；
- STT 当前为六节点演示流程，不是完整的正式施测与评分规则；
- SCD 访谈使用固定 Mock 追问，尚未接入真实 LLM Provider；
- MoCA-B 当前只有一道开放回答演示题，不是完整 MoCA-B；
- 程序结果和 AI 候选结果都不能直接成为最终临床评分。

因此，B 类任务提交后必须由医生确认，C 类候选结果必须由医生复核。患者端不能查看内部规则、候选分或最终诊断结论。

## 7. 启动与体验

在项目根目录运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

访问地址与演示凭据：

```text
医生端：http://127.0.0.1:5173/login
患者端：http://127.0.0.1:5173/p/fill/demo-patient-token
Swagger：http://127.0.0.1:8000/docs

医生：doctor1 / Doctor123!
管理员：admin / Admin123!
患者访问码：123456
```

停止服务：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

## 8. 验证结果

- 后端回归与 C/B 新增测试：`22 passed`；
- Vue TypeScript 检查与生产构建：通过；
- 后端与统一患者端本地启动：通过；
- Playwright 用例已改为从正式患者任务包打开四项 C/B 任务；本轮因 Chromium 测试浏览器下载未完成，尚未实际执行浏览器用例；
- 测试结束后 8000 与 5173 服务均已停止。

## 9. 后续工作

后续应优先实现医生复核、最终结果确认、退回与重新开启任务的完整接口和页面，然后再接入真实 LLM Provider、正式授权素材及更多 B/C 类任务。其他量表内容不完整和部分量表不能直接评分的问题应另行分析，避免与本次 C/B 接入混为同一项完成状态。
