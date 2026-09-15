# 认知评估与量表管理系统 · cyb 集成版

本分支按功能整合 `main`、`yjj`、`dl`、`lfy`。正式系统采用 Vue + FastAPI + SQLAlchemy，以 dl 已整合的医生/患者流程为基础；患者端加入 lfy 的逐题交互和完成记录，并将 main 的四项 C/B 任务接入同一正式患者流程。

## 功能与目录

| 目录 | 职责 |
| --- | --- |
| `admin-web/` | Vue 医生管理、患者移动填写、问卷治理；正式患者入口 `/p/fill/:token` |
| `server/` | FastAPI、数据库模型、认证、草稿、计分、统计、迁移与后端测试 |
| `patient-web/` | React C/B 参考原型（仅供来源参考）；STT 数据文件被正式前端使用 |
| `contracts/` | 正式 API 契约 |
| `scripts/` | 安装、启动、停止、测试及来源审计 |
| `docs/` | 项目文档（按贡献者和时间线组织，详见 [docs/README.md](docs/README.md)） |
| `assets/`、`samples/` | 参考图片与问卷导入样例 |

正式闭环：医生登录 → 建档 → 派发 → 患者通过链接和访问码进入 → 草稿/提交 → 服务端计分 → 医生查看报告和统计。

量表目录包含 SCD-Q9、GDS-15、ESS、利手量表及其他录入/复核模板。首次启动会发布两张结构化 DEMO 和四张 C/B DEMO；正式目录项须经管理员预览、导入、核对和发布。C/B 使用占位内容和可降级 AI；React 来源参考端的 STT 已接入 PDF 坐标 JSON 与年龄阈值 JSON，正式患者入口中的 C/B 过程数据、访谈证据及候选结果会写入正式评估库并等待医生复核。

## 运行

在 cyb 工作区根目录使用 PowerShell：

```powershell
.\scripts\setup.ps1
.\scripts\start.ps1
```

- 医生/管理员：<http://127.0.0.1:5173/login>
- 正式患者演示：<http://127.0.0.1:5173/p/fill/demo-patient-token>，访问码 `123456`
- C/B 任务：通过正式患者演示入口进入
- 后端接口：<http://127.0.0.1:8000/docs>
- 演示医生 `doctor1 / Doctor123!`；管理员 `admin / Admin123!`。

关闭：`.\scripts\stop.ps1`。详细配置、手机访问和数据库位置见 [STARTUP.md](STARTUP.md)。

## 验证与整合依据

```powershell
.\scripts\test.ps1
# 浏览器验证需先启动三个服务，并首次安装 Chromium：
npm exec --prefix admin-web -- playwright install chromium
npm run test:e2e --prefix admin-web
```

- [功能覆盖、分支取舍与剩余缺口](docs/integration/coverage.md)
- [2026-09-14 C/B 辅助任务患者系统整合记录](docs/integration/2026-09-14-cb-patient-integration.md)
- [实际验证结果](docs/integration/validation.md)
- [固定来源版本](docs/integration/sources.json) / [逐文件去向](docs/integration/inventory.json)
- [API 契约](contracts/API.md)
- [系统整合说明](docs/BACKEND_INTEGRATION.md)

本项目为课程原型，不提供医学诊断。演示/测试使用虚拟数据，量表来源与授权说明随模板保留。原计划的 8 位备用码与独立凭码进入尚未实现，当前保持链接加 6 位码的协议。
