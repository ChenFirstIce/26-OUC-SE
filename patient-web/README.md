# Patient Web - 参考原型目录

⚠️ **本目录仅供来源参考，不在生产环境使用**

## 目录说明

### c2b/Frontend/ - React 参考原型

来自 main 分支的原始 C/B 任务演示代码（Boston 命名、STT 连线、SCD 访谈、MoCA 开放题）。

**迁移状态**：已迁移到正式 Vue 前端
- 原型代码：`patient-web/c2b/Frontend/src/`
- 正式代码：`admin-web/src/components/patient/AssistedTask.vue`

**正式入口**：
1. 医生在 http://127.0.0.1:5173 派发任务
2. 患者访问 `http://127.0.0.1:5173/p/fill/:token`
3. 输入 6 位访问码
4. 在任务列表中执行辅助任务

### 数据文件（正式使用）

以下 JSON 文件被正式前端使用：

- **stt_sequences_with_coordinates.json** - STT-A/B 完整坐标数据
  - 包含练习节点和正式测试节点
  - 支持 A 型（数字）和 B 型（数字+字母）
  - 被 `admin-web` 的 STT 组件使用

- **stt_age_thresholds.json** - STT 年龄分层阈值
  - 不同年龄段的完成时间标准
  - 用于判断测试结果是否正常

## 技术栈对比

| 特性 | patient-web (参考) | admin-web (正式) |
|---|---|---|
| 框架 | React + TypeScript | Vue 3 + TypeScript |
| 状态管理 | Zustand (本地) | Pinia + 后端 API |
| 数据持久化 | localStorage | PostgreSQL |
| 认证 | Mock | JWT Token + 访问码 |
| 后端集成 | 无 | FastAPI 完整集成 |
| 生产使用 | ❌ 否 | ✅ 是 |

## 开发历史

| 分支 | 作者 | 时间 | 说明 |
|---|---|---|---|
| main | 陈怡冰 | 2026-09-03 | React 原型创建 |
| cyf | cyf | 2026-09-14 | 迁移到 Vue，集成后端 |
| cyb | 陈怡冰 | 2026-09-15 | 补充 STT 数据 |

## 相关文档

- [C/B 任务映射](../docs/integration/c-b-task-mapping.md)
- [C/B 整合记录](../docs/integration/2026-09-14-cb-patient-integration.md)
- [系统架构](../docs/ARCHITECTURE.md)
