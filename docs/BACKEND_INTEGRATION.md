# 答题后端与 lfy 前端对接说明

## 对接结论

`lfy` 前端的数据访问原来集中在 `src/repositories/mockRepository.ts`，页面同步读写浏览器 `localStorage`。现在页面改用 `src/repositories/apiRepository.ts`，通过 HTTP API 对接 `server/index.mjs`。

后端保持前端现有的 `Patient`、`AssessmentAssignment`、`AssessmentDraft` 和 `AssessmentSubmission` 结构，因此量表渲染组件及四份量表配置无需修改。

## 已实现接口

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查 |
| GET | `/api/patients` | 演示患者列表 |
| GET | `/api/patients/current` | 当前患者 |
| PUT | `/api/patients/current` | 切换当前患者 |
| GET | `/api/patients/:patientId/assignments` | 患者任务列表 |
| POST | `/api/assignments` | 管理员派发任务 |
| GET | `/api/assignments/:assignmentId/draft` | 获取草稿 |
| PUT | `/api/assignments/:assignmentId/draft` | 保存单题草稿 |
| POST | `/api/assignments/:assignmentId/submit` | 正式提交并由服务端计分 |
| GET | `/api/assignments/:assignmentId/submission` | 获取任务提交结果 |
| GET | `/api/submissions?patientId=...` | 获取全部或指定患者提交 |
| DELETE | `/api/demo` | 重置演示运行数据 |

## 关键行为

- 后端校验任务归属、量表 ID、必答题数量、题目 ID 和答案值。
- 后端对 SCD-Q9、GDS-15、ESS、爱丁堡利手量表重新计分，不信任浏览器传入的分数。
- 同一 assignment 重复提交时返回首次提交结果，不创建重复记录。
- 正式提交会写入答案和结果、更新任务状态并删除对应草稿。
- 运行数据原子写入 `server/data/store.json`；该文件不提交 Git。

## 本地启动

```bash
npm install
npm run dev:server
```

另开终端：

```bash
npm run dev
```

Vite 将 `/api` 转发到 `127.0.0.1:3001`。部署时可以设置前端环境变量：

```text
VITE_API_BASE_URL=https://example.com/api
```

## 当前边界

当前实现是可联调的课程项目后端骨架，不是生产医疗系统。下一阶段应加入：

1. 用户登录、患者/医生角色鉴权与任务访问令牌；
2. PostgreSQL/MySQL 数据库及迁移脚本；
3. assessmentVersionId 和不可变计分规则版本；
4. 草稿 revision 乐观锁和正式提交 Idempotency-Key；
5. Boston、STT 的过程事件接口；
6. SCD 访谈、MoCA-B 开放题的异步分析接口；
7. 操作审计、敏感数据保护和医生复核流程。
