# 下一步工作清单

## 已完成 ✅

### 1. 文档结构整理
- ✅ 创建 `docs/contributors/` 按贡献者分类
  - cyb/ - 陈怡冰的初始化和整合工作
  - lfy/ - lfy 的患者端原型
  - dl/ - dl 的后端整合
  - cyf/ - cyf 的 C/B 任务整合
- ✅ 创建 `docs/integration/` 整合文档目录
- ✅ 创建 `docs/archived/` 归档早期规划
- ✅ 创建 `docs/README.md` 文档索引
- ✅ 移除 `docs/references/` 重复目录
- ✅ 为每个贡献者创建 README.md 说明

### 2. 架构文档
- ✅ 创建 `docs/ARCHITECTURE.md` - 系统架构说明
- ✅ 创建 `docs/REFACTORING_PLAN.md` - 重构计划
- ✅ 创建 `docs/CLEANUP_PROPOSAL.md` - 清理提案
- ✅ 创建 `docs/MODULES_CLEANUP_ANALYSIS.md` - 深度分析

## 待完成 🚧

### 3. 后端代码清理（模块化）

**目标**：消除 `server/app/modules/` 和 `server/app/core/db.py` 的冗余

**步骤**：

```bash
# 1. 创建备份分支
git checkout -b backup/before-cleanup-modules

# 2. 切回主分支
git checkout main

# 3. 删除未使用的 modules/ 目录
git rm -rf server/app/modules/

# 4. 删除重复的 db.py 文件
git rm server/app/core/db.py

# 5. 提交更改
git commit -m "refactor: remove unused modules/ directory and duplicate db.py

- modules/ 目录未被 main.py 注册，从未实际使用
- modules/ 中的模型已统一到 models.py
- core/db.py 与 core/database.py 重复，main.py 使用后者
- 无任何代码依赖 modules/ 或 db.py
- 删除以消除混淆，Git 保留历史可恢复

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

# 6. 验证系统运行
.\scripts\start.ps1
```

**验证清单**：
- [ ] 后端服务正常启动（http://127.0.0.1:8000/health）
- [ ] 前端服务正常启动（http://127.0.0.1:5173）
- [ ] 医生登录功能正常
- [ ] 患者入口访问正常
- [ ] 运行后端测试：`python -m pytest server/tests/`
- [ ] 运行前端 E2E 测试：`npm run test:e2e --prefix admin-web`

**预期结果**：
- 代码结构更清晰
- 减少 40+ 个未使用文件
- 消除新人困惑
- 维护成本降低

### 4. 前端代码整理

**目标**：明确 admin-web（正式）和 patient-web（参考）的边界

**步骤**：

```bash
# 1. 为 patient-web 添加 README
cat > patient-web/c2b/Frontend/README.md << 'EOF'
# C/B 任务参考原型（React）

⚠️ **仅供来源参考，不在生产环境使用**

本目录包含 main 分支的原始 React 原型代码，已迁移到正式 Vue 前端。

## 迁移状态

- ✅ Boston 命名任务 → `admin-web/src/components/patient/AssistedTask.vue`
- ✅ STT 连线任务 → `admin-web/src/components/patient/AssistedTask.vue`
- ✅ SCD 访谈任务 → `admin-web/src/components/patient/AssistedTask.vue`
- ✅ MoCA 开放题 → `admin-web/src/components/patient/AssistedTask.vue`

## 正式入口

患者通过以下方式访问 C/B 任务：
1. 医生派发任务包
2. 患者访问 `http://127.0.0.1:5173/p/fill/:token`
3. 输入 6 位访问码
4. 在任务列表中看到辅助任务

## 数据文件

- `patient-web/stt_sequences_with_coordinates.json` - STT-A/B 完整坐标
- `patient-web/stt_age_thresholds.json` - STT 年龄阈值

这些数据已被正式前端使用。

## 开发历史

来源：main 分支（fd2bc03）
作者：陈怡冰
时间：2026-09-03
EOF

# 2. 添加正式前端说明
cat > admin-web/README_STRUCTURE.md << 'EOF'
# Admin-Web 结构说明

## 项目定位

**正式 Vue 前端**，包含医生端和患者端，是生产环境唯一使用的前端。

## 目录结构

\`\`\`
src/
├── views/              # 页面视图
│   ├── 医生端
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── PatientsView.vue
│   │   ├── PatientDetailView.vue
│   │   ├── AssignmentsView.vue
│   │   ├── CreateAssignmentView.vue
│   │   ├── QuestionnairesView.vue
│   │   └── AdminCenterView.vue
│   └── 患者端
│       └── patient/PatientPortal.vue
├── components/         # 可复用组件
│   ├── DynamicQuestion.vue     # 动态题型渲染
│   ├── AssistedTask.vue        # C/B 辅助任务
│   ├── ReviewEvidence.vue      # 复核证据展示
│   ├── QuestionnaireDetailDialog.vue
│   ├── ChartPanel.vue
│   └── StatCard.vue
├── layouts/
│   └── StaffLayout.vue         # 医生端布局框架
├── stores/
│   └── auth.ts                 # 认证状态管理
├── utils/              # 工具函数
│   ├── patient.ts              # 患者逻辑
│   ├── mocaOpen.ts             # MoCA 开放题分析
│   ├── date.ts                 # 日期处理
│   └── idempotency.ts          # 幂等键生成
├── api/
│   └── client.ts               # API 客户端
├── router.ts           # 路由配置
└── main.ts             # 应用入口
\`\`\`

## 路由

### 医生端（需登录）
- `/login` - 医生登录
- `/` - 仪表盘
- `/patients` - 患者列表
- `/patients/:id` - 患者详情
- `/assignments` - 派发列表
- `/assignments/new` - 创建派发
- `/questionnaires` - 问卷治理
- `/admin` - 管理中心

### 患者端（token + 访问码）
- `/p/fill/:token` - 患者填写入口

## 技术栈

- Vue 3 (Composition API)
- TypeScript
- Element Plus (UI 组件库)
- Pinia (状态管理)
- Vue Router (路由)
- Axios (HTTP 客户端)
- ECharts (图表)
- Vite (构建工具)
EOF
```

### 5. 系统运行验证

**目标**：确保重构后系统完全正常

**测试清单**：

#### 后端测试
- [ ] 健康检查：`curl http://127.0.0.1:8000/health`
- [ ] API 文档：访问 http://127.0.0.1:8000/docs
- [ ] 单元测试：`python -m pytest server/tests/`
- [ ] 数据库迁移：确认 Alembic 版本正确

#### 前端测试（医生端）
- [ ] 登录：使用 `doctor1 / Doctor123!`
- [ ] 患者列表：查看、搜索、创建患者
- [ ] 派发任务：创建新派发，生成链接和访问码
- [ ] 问卷管理：查看问卷目录，预览量表
- [ ] 统计报表：查看仪表盘图表
- [ ] 复核流程：查看辅助任务复核界面

#### 前端测试（患者端）
- [ ] 访问 http://127.0.0.1:5173/p/fill/demo-patient-token
- [ ] 输入访问码 `123456`
- [ ] 查看任务列表（问卷 + 辅助任务）
- [ ] 填写问卷：逐题作答、草稿保存、提交
- [ ] 执行 C/B 任务：Boston、STT、SCD、MoCA
- [ ] 完成记录：查看已完成任务

#### E2E 测试
- [ ] 安装 Playwright：`npm exec --prefix admin-web -- playwright install chromium`
- [ ] 运行测试：`npm run test:e2e --prefix admin-web`

## 文件清单

### 新增文档
- [x] `docs/README.md` - 文档索引
- [x] `docs/ARCHITECTURE.md` - 系统架构
- [x] `docs/REFACTORING_PLAN.md` - 重构计划
- [x] `docs/CLEANUP_PROPOSAL.md` - 清理提案
- [x] `docs/MODULES_CLEANUP_ANALYSIS.md` - 深度分析
- [x] `docs/NEXT_STEPS.md` - 本文件
- [x] `docs/contributors/cyb/README.md`
- [x] `docs/contributors/lfy/README.md`
- [x] `docs/contributors/dl/README.md`
- [x] `docs/contributors/cyf/README.md`
- [ ] `patient-web/c2b/Frontend/README.md` - 参考原型说明
- [ ] `admin-web/README_STRUCTURE.md` - 正式前端结构

### 待删除
- [ ] `server/app/modules/` (40+ 文件)
- [ ] `server/app/core/db.py`

### 重新组织
- [x] `docs/plan/week1/` → `docs/archived/week1-planning/`
- [x] `docs/references/cyb/` → `docs/contributors/cyb/`
- [x] `docs/references/lfy/` → `docs/contributors/lfy/`

## 时间估算

- ✅ 文档整理：已完成（1 小时）
- 🚧 后端清理：30 分钟
- 🚧 前端整理：30 分钟
- 🚧 系统验证：1 小时

**总计**：2.5 - 3 小时

## 注意事项

1. **备份优先**：清理前创建 backup 分支
2. **逐步验证**：每步完成后立即验证
3. **保留历史**：Git 中仍可访问所有删除的代码
4. **文档同步**：更新 README.md 和 ARCHITECTURE.md
