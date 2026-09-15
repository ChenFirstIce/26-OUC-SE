# 项目文档索引

本目录按贡献者和时间线组织文档。

## 目录结构

- **integration/** - 系统整合文档（2026-09-14 至今）
  - 分支整合记录、功能覆盖报告、验证结果
  
- **contributors/** - 按贡献者组织的文档
  - **cyb/** - 陈怡冰的初始规划和 C/B 任务整合（2026-08 至 2026-09）
  - **lfy/** - lfy 的患者端原型和量表参考（2026-09-03）
  - **dl/** - dl(xixiyhaha) 的后端整合和治理（2026-09-05 至 2026-09-10）
  - **cyf/** - cyf 的 C/B 任务患者端整合（2026-09-14）

- **requirements/** - 原始需求和量表材料
  - 来自 ad-ouc-master 的 PDF 量表、操作说明等

- **archived/** - 已归档的早期计划文档
  - 第一阶段 MVP 设计方案（web/小程序）等

## 时间线

### 2026-08-27: 项目初始化（陈怡冰）
- 初始提交，建立项目结构

### 2026-09-03: 患者端原型（lfy）
- React 患者端 MVP 骨架
- 四张量表配置和逐题交互

### 2026-09-05 至 09-10: 后端整合（dl）
- 整合 yjj 的医患闭环
- 问卷治理、UTC 时长、版本发布

### 2026-09-14: C/B 任务整合（cyf + 陈怡冰）
- C/B 任务接入正式患者入口
- 医生复核与退回流程
- STT 坐标数据和年龄阈值

### 2026-09-15: 辅助任务数据整合（陈怡冰）
- STT scale 数据完善
- 系统整合验证

## 前后端代码位置

### 前端
- **admin-web/** - 正式 Vue 前端（医生端 + 患者入口）
  - 医生管理：`/login`, `/patients`, `/assignments`, `/questionnaires`
  - 患者入口：`/p/fill/:token`
  
- **patient-web/c2b/Frontend/** - React 参考原型（仅供来源参考）
  - Boston 命名、STT 连线、SCD 访谈、MoCA 开放题

### 后端
- **server/app/** - FastAPI 后端
  - **routers/** - API 路由（正式入口）
  - **modules/** - 模块化模型和服务（部分为未注册的草稿）
  - **services/** - 业务逻辑服务
  - **core/** - 核心配置、数据库、认证

参见：[BACKEND_INTEGRATION.md](BACKEND_INTEGRATION.md) | [API Contract](../contracts/API.md)
