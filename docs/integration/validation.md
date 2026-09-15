# cyb 实际验证记录

日期：2026-09-15。环境：Windows、PowerShell、Python 3.12、Node.js 22.22.2。来源版本见 [sources.json](sources.json)。

| 检查 | 结果 | 证据/入口 |
| --- | --- | --- |
| 全分支文件清点 | 329 个来源文件，固定 SHA 与内容哈希 | `scripts/audit_branches.py`、`inventory.json` |
| 后端回归与新增边界 | **24 passed** | `server/tests/test_flow.py`、`test_integration.py`，含 C/B 正式会话、DeepSeek 加密配置与结果分层 |
| Vue 类型检查与生产构建 | **通过** | `npm run build --prefix admin-web` |
| C/B 正式患者端构建 | **通过** | 四项任务已迁入 `admin-web`，随统一 Vue 生产构建验证；MoCA-B 开放题两子任务已纳入构建 |
| React 来源参考端 | **通过** | `npm test`：2 files / 7 tests；`npm run typecheck`；`npm run build`；STT 坐标缩放、A/B 正式序列和年龄阈值已纳入断言 |
| 完整检查脚本 | **退出码 0** | `scripts/test.ps1`，输出“全部检查通过” |
| Chromium 浏览器检查 | **5 passed** | `admin-web/tests/integration.spec.ts` |
| 启动与停止 | **待本轮浏览器复验** | 启动脚本已收敛为 8000/5173；不再依赖 5174 独立演示服务 |
| 原工作区保护 | **未改变** | main 的 README/签到表修改和临时签到文件删除状态与整合前一致 |

## 后端覆盖场景

保留 dl 的 10 项测试，新增 11 个实际测试用例（含参数化用例）。验证医生登录/权限、患者建档、任务派发、答案保存/提交、报告和统计、目录导入、版本治理和旧 SQLite 升级。

新增验证覆盖：漏答返回 422；草稿恢复；过时 revision 返回 409；同一幂等键重复提交返回同一评估；已提交任务禁止改写；其他任务包 item 返回 404；历史字段只在当前包返回；撤销和过期阻止已建立会话继续访问；未先打开题目时直接提交；SCD 0/9、ESS 0/24、利手 -100/0/100、GDS 正反向 0/15 边界。另加强既有版本治理测试，确认已停用版本的既有任务仍能打开并提交。

## 浏览器覆盖场景

1. 390px 宽度手机视口：验证访问码、逐题作答、自动保存、刷新后恢复、漏答提示、提交、已完成记录、医生报告 API 可读。
2. 同一浏览器切换另一条评估链接：清除旧患者会话并要求新访问码。
3. 回答后立即返回列表：保存完成后再离开，再打开可恢复最后一次回答。
4. 1440px 桌面视口：医生登录以及患者、派发、问卷、统计页面无页面运行异常。
5. 浏览器用例已改为从正式患者任务包打开四项 C/B 任务并检查移动视口横向溢出；本轮尚未启动服务执行该用例。

已人工查看自动化生成的 [手机答题截图](screenshots/patient-mobile.png) 与 [医生桌面截图](screenshots/doctor-desktop.png)。

## 本轮修复

- 修复迁目录后的脚本、代理、端口与文档引用，隔离各工作区默认 SQLite 数据库。
- 修复患者会话与评估链接未绑定、返回列表丢失最后修改、保存并发与提交重试键问题。
- 修复后端直接提交时 `started_at` 尚未初始化导致异常。
- 修复 SCD 演示 effect 返回滚动调用结果导致当前 Chromium 中 `destroy is not a function` 白屏。
- 修复 PowerShell 将 npm 构建警告误判为脚本失败的问题，改为检查原生命令退出码。

## 验证限制

有一条 Starlette/AnyIO 弃用提示，未影响测试。没有进行压力测试、真实手机跨网络测试、生产部署、真实 LLM 接入或医学有效性认证。正式量表与演示模块的剩余功能缺口详见 [coverage.md](coverage.md)。

本轮补充验证：MoCA-B 开放题本地规则覆盖 13 元付款方式 0/3、3/3，抽象分类同义表达和空回答；后端 `DEMO_MOCA_OPEN` 校验两题非空，并生成 `candidate_total=6`、`max_score=6` 的候选结果供医生复核。DeepSeek 配置验证覆盖管理员权限、API key 加密入库不泄露明文、SCD/MoCA-B 成功使用模型候选结果，以及模型失败时本地降级。

2026-09-15 补充验证：React 来源参考端 STT 读取 `patient-web/stt_sequences_with_coordinates.json` 与 `patient-web/stt_age_thresholds.json`，将 PDF `1489 × 2105 px` 坐标缩放到网页 SVG 百分比画布；页面支持 STT-A/STT-B、练习/正式切换、STT-B 干扰节点、年龄分层阈值判读和结果留痕。已执行 `npm run typecheck`、`npm test`、`npm run build`，均通过；构建仅出现 zod 依赖注释被 Rollup 移除的非阻断提示。

浏览器测试添加的是本工作区隔离数据库内的虚拟测试患者和任务；没有操作其他分支数据库。验证完成后已停止三项服务，用户可按根目录 STARTUP.md 重新启动。
