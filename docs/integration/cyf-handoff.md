# cyf 对接交接记录

更新时间：2026-09-15。

## 当前分支与来源

- 工作区：`D:\A_Senior\B_软件工程实践_cyb`
- 当前分支：`cyb`
- 已合入来源：`origin/cyf` at `a85525385bc3551dac99ebcd5cb230d0366ccfa9`
- 来源记录：`docs/integration/sources.json`
- 原 `main` 工作区未提交内容未修改。

## 已完成改动

- 将 `origin/cyf` 快进合入 `cyb`，保留正式患者入口、C/B 任务和医生复核流程。
- MoCA-B 开放回答从单题 demo 扩展为两个结构化子任务：
  - `moca_payment_13`：13 元付款方式，候选 0-3 分。
  - `moca_abstraction`：火车/轮船、锣鼓/笛子、南方/北方抽象分类，候选 0-3 分。
- 正式 Vue 患者端和 React 来源参考端均改为逐题记录原始回答；患者端不展示候选分。
- 后端 `DEMO_MOCA_OPEN` 提交时校验两题非空，优先用 DeepSeek 生成 `candidate_result_json`；未配置或失败时用本地规则降级，总候选分范围 0-6。
- DeepSeek API key 已支持管理员接口加密入库；数据库只保存密文、掩码和配置元数据，解密主密钥来自 `LLM_SECRET_KEY`。
- 医生复核证据页按 MoCA-B 子题展示原始回答。
- 同步更新 `contracts/API.md`、`docs/integration/coverage.md`。
- **2026-09-15**：建立 C/B 任务正式资料映射索引（`docs/integration/c-b-task-mapping.md`），标注 6 个网页 AI 映射任务和 P0/P1/P2 缺口清单。

## 未完成事项

- 不要在代码、文档、日志或测试快照中写入 DeepSeek API key 明文；管理员配置接口也只返回 `key_hint`。
- Boston 正式图片材料、SCD 完整结构化访谈状态机仍是缺口；STT 来源参考端已接入坐标 JSON、完整形状节点和年龄阈值，统一 Vue 正式患者入口仍需按同一数据源替换锁定版本配置（详见 `docs/integration/c-b-task-mapping.md`）。
- MoCA-B 候选分仅为课程演示辅助规则，不代表医学认证评分。
- 映射索引中 6 个网页 AI 任务仍需执行：Boston 题目/评分、STT 序列/节点值、MoCA-B 任务列表、SCD 问题树，获取结构化数据后填充代码。

## 测试结果

- 通过：`npm test -- --run` in `patient-web/c2b/Frontend`，2 files / 5 tests。
- 通过：`npm run typecheck` in `patient-web/c2b/Frontend`。
- 通过：`npm run build` in `patient-web/c2b/Frontend`。
- 通过：`npm run build --prefix admin-web`。
- 通过：`..\.venv\Scripts\python.exe -m pytest tests -q` in `server`，24 passed，1 个 Starlette/AnyIO 弃用提示。
- 说明：从仓库根目录直接执行系统 Python 或 `.venv` pytest 会分别遇到缺少 `fastapi` 或 `PYTHONPATH` 未包含 `server/app`；以上通过结果按项目脚本口径在 `server/` 目录运行。

## 阻塞问题

- 当前未发现阻塞。

## 下一步建议

- 跑完上述测试后，把结果回填到本文件和 `docs/integration/validation.md`。
- **优先**：执行 `docs/integration/c-b-task-mapping.md` 中 6 个网页 AI 映射任务，获取结构化数据。
- 后续：根据映射索引修复代码，替换 DEMO 占位数据为正式材料。
