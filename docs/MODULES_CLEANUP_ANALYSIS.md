# modules/ 清理分析

## 发现

经过深入代码审查，发现 `server/app/core/db.py` 中的 `create_tables()` 函数导入了 modules/ 中的模型：

```python
def create_tables() -> None:
    # Importing registers every table with SQLAlchemy metadata.
    from app.modules.assessments import models as _assessment_models  # noqa: F401
    from app.modules.assignments import models as _assignment_models  # noqa: F401
    from app.modules.audit import models as _audit_models  # noqa: F401
    from app.modules.departments import models as _department_models  # noqa: F401
    from app.modules.patients import models as _patient_models  # noqa: F401
    from app.modules.questionnaires import models as _questionnaire_models  # noqa: F401
    from app.modules.users import models as _user_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
```

## 问题

1. **db.py 与 database.py 重复**
   - `server/app/core/db.py` - 定义 Base、engine、SessionLocal、create_tables
   - `server/app/core/database.py` - 定义 Base、engine、SessionLocal、get_db
   - 两个文件定义了相同的内容！

2. **main.py 使用哪个？**
   - 检查 main.py：`from .core.database import Base, SessionLocal, engine`
   - main.py 使用 `database.py`，而不是 `db.py`
   - main.py 直接调用 `Base.metadata.create_all(engine)`，不调用 `create_tables()`

3. **create_tables() 未被使用**
   - `create_tables()` 只在 `db.py` 中定义
   - 没有任何代码 import 或调用它
   - 实际运行使用的是 `database.py` 中的 Base

4. **models.py 已包含所有模型**
   - `server/app/models.py` 包含所有数据库模型
   - main.py 导入了 models: `from . import models`
   - SQLAlchemy 自动从 models.py 发现所有继承 Base 的模型

## 结论

**modules/ 中的模型定义完全未被使用**：
- main.py 使用 `database.py`（不是 `db.py`）
- main.py 从 `models.py` 导入模型（不是 `modules/*/models.py`）
- `create_tables()` 函数从未被调用
- modules/ 是完全独立的死代码

## 修正后的清理计划

### 步骤 1：删除 modules/ 目录

```bash
git rm -rf server/app/modules/
```

### 步骤 2：删除 core/db.py（重复文件）

```bash
git rm server/app/core/db.py
```

### 步骤 3：验证系统运行

实际使用的是：
- `server/app/core/database.py` - 数据库配置
- `server/app/models.py` - 所有模型定义
- `server/app/routers/` - 所有 API 路由
- `server/app/services/` - 业务逻辑

## 风险

**极低**：
- modules/ 和 db.py 从未被 main.py 使用
- 实际运行的代码路径完全独立
- Git 保留完整历史，可随时恢复

## 验证命令

```bash
# 检查 main.py 实际使用的导入
grep "^from" server/app/main.py | grep -E "(database|models|routers)"

# 输出：
# from .core.database import Base, SessionLocal, engine
# from . import models
# from .routers import admin, assignments, ...

# 检查 db.py 是否被导入
grep -r "from.*core.db import" server/app/ --exclude-dir=__pycache__

# 输出：无（db.py 未被使用）
```
