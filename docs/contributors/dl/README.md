# dl (xixiyhaha) 贡献文档

时间：2026-09-05 至 2026-09-10

## 主要贡献

### 后端整合与治理
- 整合 yjj 的医患闭环到统一后端
- 问卷版本治理流程（预览、导入、发布、停用）
- 数据库 Alembic 迁移
- UTC 时长计算修正
- 前端包大小优化

### 文档输出
- [BACKEND_INTEGRATION.md](../../BACKEND_INTEGRATION.md) - 系统整合说明
- [DEVELOPMENT_LOG.md](../../DEVELOPMENT_LOG.md) - 开发与运维日志
- API.md (已移至 contracts/API.md) - API 契约文档

## 技术栈
- FastAPI + SQLAlchemy (后端)
- Vue 3 + Element Plus (前端)
- PostgreSQL (数据库)
- Alembic (数据库迁移)

## 相关 Git 提交
```
9e3e85b - 2026-09-05 16:37 - feat: integrate patient assessment backend
65c0c93 - 2026-09-05 17:07 - docs: document repository structure and API contract
4cab2ca - 2026-09-10 16:42 - feat: integrate patient workflow with yjj backend
e099115 - 2026-09-10 17:16 - fix: correct assessment timing and timezone display
84ddd48 - 2026-09-10 17:31 - docs: add dl development and operations log
7b931ca - 2026-09-10 21:02 - feat: add questionnaire version governance
ce1378f - 2026-09-10 21:05 - perf: reduce frontend initial bundle size
e4fcf05 - 2026-09-10 21:08 - fix: require previews for all questionnaire imports
c8f0210 - 2026-09-10 21:48 - docs: record questionnaire governance and bundle optimization
```
