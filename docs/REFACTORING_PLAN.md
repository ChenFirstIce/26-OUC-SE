# 后端重构计划

## 目标

统一后端代码结构，消除 `routers/` 和 `modules/` 的重复，建立清晰的分层架构。

## 现状分析

### modules/ 的实际用途

通过代码审查发现：
- `modules/` 目录下的路由文件（`*/router.py`）**未被 main.py 注册**
- `modules/` 中的模型定义已被统一到 `models.py`
- `modules/` 中的 service 部分功能已迁移到 `services/`
- 实际运行的是 `routers/` 中的代码

### 重复文件对比

| modules/ 文件 | routers/ 对应文件 | 状态 |
|---|---|---|
| modules/assignments/router.py | routers/assignments.py | 功能重叠，routers 为准 |
| modules/auth/router.py | routers/auth.py | 功能重叠，routers 为准 |
| modules/patients/router.py | routers/patients.py | 功能重叠，routers 为准 |
| modules/questionnaires/router.py | routers/questionnaires.py | 功能重叠，routers 为准 |
| modules/users/router.py | routers/admin.py (部分) | 已整合到 admin |
| modules/departments/router.py | routers/admin.py (部分) | 已整合到 admin |

## 重构方案

### 方案 A：保留 modules/，重构为领域模块（推荐）

将 modules/ 改造为真正的领域驱动设计模块：

```
server/app/modules/
├── auth/
│   ├── __init__.py
│   ├── models.py      # 从 app/models.py 迁入
│   ├── schemas.py     # Pydantic schemas
│   ├── service.py     # 业务逻辑
│   └── router.py      # API 路由
├── patients/
│   ├── models.py
│   ├── schemas.py
│   ├── service.py
│   └── router.py
├── questionnaires/
│   ├── models.py
│   ├── schemas.py
│   ├── service.py
│   └── router.py
└── ...
```

**优点**：
- 清晰的模块边界
- 每个模块自包含
- 符合 DDD 原则

**缺点**：
- 需要大量文件移动
- 需要修改所有 import 语句
- 风险较高

### 方案 B：删除 modules/，保持扁平结构（稳妥）

完全移除 `modules/`，保持当前的扁平结构：

```
server/app/
├── models.py          # 所有模型
├── routers/           # 所有路由
├── services/          # 所有业务逻辑
└── core/              # 核心功能
```

**优点**：
- 改动最小
- 风险低
- 当前已经在运行

**缺点**：
- models.py 会很大
- 缺少模块隔离

### 方案 C：混合方案

保留 modules/ 用于数据模型和 schemas，路由和服务保持扁平：

```
server/app/
├── modules/           # 仅放模型和 schemas
│   ├── auth/
│   │   ├── models.py
│   │   └── schemas.py
│   ├── patients/
│   │   ├── models.py
│   │   └── schemas.py
│   └── ...
├── routers/           # API 路由（已注册）
├── services/          # 业务逻辑
└── core/              # 核心功能
```

**优点**：
- 模型分组清晰
- 路由和服务保持简单
- 风险中等

**缺点**：
- 仍需移动模型定义
- Import 路径变更

## 推荐执行步骤（方案 B）

考虑到系统已接近完成，推荐采用**方案 B（删除 modules/）**：

### 第一步：确认 modules/ 未被使用

```bash
# 检查是否有代码 import modules/
grep -r "from app.modules" server/app/routers/
grep -r "from app.modules" server/app/services/
grep -r "from ..modules" server/app/
```

### 第二步：备份并删除

```bash
# 创建备份分支
git checkout -b backup/modules-before-cleanup

# 在主分支删除
git checkout main
git rm -rf server/app/modules/
git commit -m "refactor: remove unused modules/ directory"
```

### 第三步：验证系统运行

```bash
# 启动后端
cd server
python -m app.main

# 运行测试
python -m pytest tests/

# 运行端到端测试
cd ../admin-web
npm run test:e2e
```

### 第四步：更新文档

- 更新 ARCHITECTURE.md
- 更新 README.md
- 更新 BACKEND_INTEGRATION.md

## 时间估算

- 方案 A：2-3 天（高风险）
- 方案 B：2-4 小时（低风险）✅
- 方案 C：1 天（中风险）

## 风险评估

### 方案 B 风险

- **低**：modules/ 未被注册，删除不影响运行时
- **中**：可能有隐藏的 import（通过搜索可排除）
- **低**：可随时从 Git 恢复
