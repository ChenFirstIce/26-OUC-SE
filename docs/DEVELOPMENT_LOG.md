# dl 分支开发与操作日志

本文记录 `dl` 分支从患者答题端原型、接入 yjj 医生派发流程，到填写时长与时区修复的完整操作。它用于复盘、联调和交接；当前接口契约仍以 [API.md](API.md) 为准，架构说明以 [BACKEND_INTEGRATION.md](BACKEND_INTEGRATION.md) 为准。

最后整理日期：2026-09-10（Asia/Shanghai）。

## 1. 工作范围与分支规则

- 指定仓库：`D:\Desktop\ad-ouc-master\26-OUC-SE`。
- 所有代码、文档、提交和允许的推送只在 `dl` 分支进行。
- `main`、`yjj`、`lfy` 等其他分支只允许读取和比较，未经负责人明确授权不得修改或推送。
- 目录、关键文件、启动方式、接口或调用链发生变化时，分别同步维护 `README.md`、`STARTUP.md`、`docs/API.md` 和 `docs/BACKEND_INTEGRATION.md`。
- 自动评分仅用于课程开发和流程验证；正式临床使用前必须确认量表版权、评分规则、隐私合规及专业复核流程。

## 2. 当前正式架构

整合后以 yjj 的实现方式为基准：

| 层级 | 正式实现 | 说明 |
| --- | --- | --- |
| 医生/管理员/患者前端 | Vue 3 + Vite + TypeScript + Element Plus | 同一前端工程，患者入口为 `/p/fill/{token}`。 |
| 后端 | FastAPI + SQLAlchemy | 统一前缀 `/api/v1`，正式路由位于 `backend/app/routers/`。 |
| 问卷 | 模板 + 不可变版本 | 管理员导入、发布后，医生按 `questionnaire_version_id` 派发。 |
| 答题 | `Response` | 保存答案、开始/提交时间和 revision 乐观锁。 |
| 结果 | `Assessment` | 后端校验并权威计分，前端不能提交最终分数。 |
| 数据库 | SQLite（默认）/可配置 SQLAlchemy URL | 默认数据库位于系统临时目录，避免中文路径兼容问题。 |

`backend/app/modules/` 是 yjj 早期领域化草案，没有被 `app/main.py` 注册。实际联调必须使用 `routers/`、`services/` 和根 `models.py`，不能混用草案中的路由或字段。

## 3. 操作时间线

### 3.1 患者答题端原型

早期依据前端分析文档梳理患者答题流程，并在 `dl` 上形成患者答题后端原型。该阶段验证了以下核心能力：

- 根据任务获取问卷；
- 保存患者答案；
- 服务端校验必答题；
- GDS-15、ESS、爱丁堡利手量表计分；
- 患者端与后端 API 的基本闭环。

对应提交：`9e3e85b feat: integrate patient assessment backend`。

### 3.2 文档基线建立

建立仓库总览、启动说明、统一 API 文档和协作约定，明确目录职责、启动命令、端口、数据流和分支限制。

对应提交：`65c0c93 docs: document repository structure and API contract`。

### 3.3 只读分析 yjj 分支

通过 Git 对象读取 yjj 分支的 `doc` 和源代码，没有切换后修改其工作树，也没有向 yjj 写入或推送。分析确认 yjj 已实现：

- 医生/管理员登录与权限；
- 患者主档和临床记录；
- 问卷模板、版本、发布和目录导入；
- 一次派发多份问卷的任务包；
- 患者 token、6 位访问码和 patient JWT；
- 草稿 revision 乐观锁与幂等提交；
- 自动评分、人工复核状态、统计和审计。

因此决定以 yjj 的 FastAPI + Vue 架构为正式主干，不再维护旧 React + Node JSON 运行时，避免任务 ID、状态、答案格式和计分入口重复。

### 3.4 将患者能力接入 yjj 主流程

Windows 环境下直接合并曾因中文路径/文件权限报错而无法完整落盘。处理方式是在 `dl` 上保留双方父提交的合并关系，再逐项迁移和核对正式运行文件；整个过程没有修改 yjj 分支本身。

完成内容：

- 采用 yjj 的 FastAPI、SQLAlchemy、Vue 3、Element Plus 工程；
- 删除旧 dl 的 React + Node 正式运行入口，防止两套服务并存；
- 将 GDS-15、ESS、爱丁堡利手量表加入 `scale_catalog.py`；
- 将元数据求和、人工复核和利手指数计分接入统一 `scoring.py`；
- 患者动态答题统一为 `{question_key: value}` 答案对象；
- 使用 revision 防止草稿覆盖，使用 `Idempotency-Key` 防止重复提交；
- 补充量表导入、派发、答题、计分和统计测试；
- 更新 README、启动说明、API 和架构对接文档。

对应合并提交：`4cab2ca feat: integrate patient workflow with yjj backend`。

### 3.5 PDF 量表需求核对

曾计划根据项目根目录的 6 份 PDF 固化 6 种量表。随后确认系统已支持管理员在平台导入和发布量表，负责人明确暂不进行 PDF 量表固化，因此该项停止，没有把临时解析产物或未确认的医学规则写入业务代码。

当前扩展方式仍是：在内置目录加入经过确认的 schema/scoring，或由管理员导入问卷包，发布版本后再派发。

### 3.6 修正填写时长和时区

问题表现：结果页填写时长始终显示 `0 秒`，提交时间与本地实际时间相差约 8 小时。

根因：

1. 答卷以前可能直到首次保存或正式提交才创建，`started_at` 与 `submitted_at` 几乎相同；秒级取整后得到 0。
2. SQLite 读回时间时可能丢失 `tzinfo`，前端又把无时区字符串按浏览器本地时间理解，UTC 与 Asia/Shanghai 之间出现偏移。
3. 多个页面各自直接调用 `new Date(...)`，历史无时区值没有统一兼容策略。

修复：

- 患者第一次打开具体问卷时立即创建 revision 为 0 的 `Response`，记录 UTC `started_at`，并把单项任务/任务包更新为进行中；
- 正式提交时以 UTC 的 `submitted_at - started_at` 计算填写时长，并向上取整；正常新答卷最低记为 1 秒；
- 新增 SQLAlchemy `UTCDateTime` 类型，写入前归一到 UTC，SQLite 读回无时区值时恢复为 UTC；
- 新增 `frontend/src/utils/date.ts`，所有相关页面统一把后端 UTC 时间转换为浏览器本地时间显示；
- 修复前已保存为 0 的历史数据不能可靠反推真实开始时间，前端明确显示“历史记录未计时”，不伪造时长；
- 测试覆盖首次打开起算、UTC 序列化、最小时长和历史值显示约定。

对应提交：`e09911f fix: correct assessment timing and timezone display`。

## 4. 关键文件变更索引

| 文件 | 本轮作用 |
| --- | --- |
| `backend/app/models.py` | 统一时间字段的 UTC 写入/读取语义。 |
| `backend/app/routers/patient_session.py` | 首次打开问卷起算、草稿、幂等提交和填写时长计算。 |
| `backend/app/services/scale_catalog.py` | 内置问卷目录及迁入量表定义。 |
| `backend/app/services/scoring.py` | 后端权威计分策略。 |
| `backend/tests/test_flow.py` | 闭环、权限、并发草稿、幂等、计分、时长和时区测试。 |
| `frontend/src/api/client.ts` | `/api/v1` 客户端和 staff/patient token 分流。 |
| `frontend/src/views/patient/PatientPortal.vue` | 患者验证、任务列表、动态答题、自动保存和提交。 |
| `frontend/src/utils/date.ts` | UTC 与历史无时区时间的统一本地化。 |
| `frontend/src/views/AssignmentsView.vue` | 任务和结果时间、历史填写时长展示。 |
| `frontend/src/views/PatientDetailView.vue` | 患者时间线本地化显示。 |
| `frontend/src/views/AdminCenterView.vue` | 审计时间本地化显示。 |

## 5. 已执行验证

| 阶段 | 验证 | 结果 |
| --- | --- | --- |
| 架构整合 | 后端 `pytest` | 8 项通过。 |
| 架构整合 | 前端依赖/构建 | 初次因受限网络无法安装；依赖由本机补齐后构建通过。 |
| 时间修复 | 后端 `pytest` | 8 项通过。 |
| 时间修复 | 前端 TypeScript + 生产构建 | 通过；仅有构建产物体积提示，不影响功能。 |
| 文档整理 | Git 空白/冲突检查 | 见本次文档提交记录。 |

常规复验命令：

```powershell
Set-Location D:\Desktop\ad-ouc-master\26-OUC-SE
.\scripts\test.ps1
```

## 6. 故障记录与恢复方式

### 6.1 Git HTTPS 进程崩溃或推送失败

现象包括 `git-remote-https.exe` 内存读取异常、Just-In-Time Debugger 弹窗，或无法连接 `127.0.0.1:7890`。

已确认当前 Git 配置依赖本地 7890 代理；代理未启动时无法推送，而当前受限执行环境也不能直接连接 GitHub。这不影响本地提交，但会导致 `dl` 领先 `origin/dl`。

处理建议：

1. 确认代理软件已启动且监听 7890，或在负责人明确知情的情况下修正个人 Git 代理配置；
2. 在项目目录执行 `git status -sb`，确认当前确实是 `dl`；
3. 执行 `git push origin dl`；
4. 不要把本地 `dl` 推到 `main`、`yjj` 或其他分支。

### 6.2 服务修改后页面仍是旧行为

曾发现旧后端 PID `28492` 和旧前端 PID `9352` 占用 8000/5173。当前自动化终端对这些由其他权限上下文启动的进程执行停止操作时返回 `Access Denied`，新后端因此不能绑定 8000。

恢复方式：回到原来启动服务的 PowerShell 按 `Ctrl+C`，或只在任务管理器中结束与本项目对应的进程，然后在项目目录重新运行：

```powershell
.\scripts\start.ps1
```

不要批量结束系统中的全部 Python 或 Node 进程，以免影响其他项目。后端没有热重载时，代码修改必须重启后才生效。

### 6.3 前端依赖锁文件

`frontend/package-lock.json` 当前存在由本机安装依赖产生的未提交修改。该文件被视为用户/环境现有改动，本轮文档和此前时间修复提交均未包含、未还原它。后续如需提交锁文件，应先单独检查差异并由负责人确认。

### 6.4 保留的 Git stash

仓库仍保留 `stash@{0}`，内容是架构迁移前根目录旧 `package-lock.json` 的元数据变化。它没有应用到当前工作树，也没有擅自删除。除非确认仍有价值，否则不要直接弹出到现有 Vue 架构中。

## 7. 当前状态与后续事项

- 本地 `dl` 包含最新架构整合和时间修复；最后检查时相对 `origin/dl` 领先，尚需在网络/代理恢复后推送。
- 时间修复需要重启当前正在运行的旧后端进程后才能在页面生效。
- 新答卷会得到真实起算时间；历史 `0 秒` 数据因没有原始起点只能标记为“历史记录未计时”。
- `backend/app/modules/` 仍是未注册草案；若未来启用，必须先统一模型、迁移数据、更新接口文档和补测，不能直接并行注册。
- 6 份 PDF 不等于已经授权和验证的 6 个线上量表。新增量表必须先确认版本、题目、计分、风险阈值和使用许可。
- 正式上线前仍需更换 JWT 密钥和演示账号密码，并评审患者身份验证、数据脱敏、审计留存、备份与数据库部署方案。

## 8. 安全提交与回退

提交前：

```powershell
git branch --show-current
git status -sb
.\scripts\test.ps1
git diff --check
```

只暂存本次明确修改的文件，避免把 `frontend/package-lock.json` 等既有改动带入提交。需要撤销某个已经共享的提交时，优先在 `dl` 上使用 `git revert <commit>` 生成可追溯的反向提交；未经负责人授权不要重写历史，也不要操作其他分支。
