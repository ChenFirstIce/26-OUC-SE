# 代码清理提案

## 背景

经过代码审查，发现 `server/app/modules/` 目录**未被实际使用**：
- main.py 只注册了 routers/ 中的路由
- 没有任何 routers/ 或 services/ 代码 import modules/
- modules/ 中的模型已统一到 models.py
- modules/ 中的服务已迁移到 services/

## 提案：删除 server/app/modules/

### 理由

1. **减少混淆**：新人不会疑惑该看哪个文件
2. **降低维护成本**：不需要维护两份相似的代码
3. **保持一致性**：代码结构与实际运行一致
4. **Git 保留历史**：删除后仍可从 Git 历史恢复

### 验证结果

```bash
# 检查 import 依赖
$ grep -r "from app.modules" server/app/routers/ server/app/services/ server/app/core/
# 结果：0 个匹配

$ grep -r "from ..modules" server/app/
# 结果：0 个匹配
```

**结论**：modules/ 完全独立，删除不影响运行。

### 执行计划

**第一步：备份**
```bash
git checkout -b backup/before-cleanup-modules
git push origin backup/before-cleanup-modules
```

**第二步：删除 modules/**
```bash
git checkout main
git rm -rf server/app/modules/
```

**第三步：验证**
- 启动后端服务
- 运行后端测试
- 运行前端 E2E 测试

**第四步：提交**
```bash
git commit -m "refactor: remove unused modules/ directory

modules/ 目录来自 yjj 分支的模块化尝试，但实际运行使用的是 routers/。
- modules/ 中的路由未在 main.py 注册
- modules/ 中的模型已统一到 models.py
- modules/ 中的服务已迁移到 services/
- 无任何代码 import modules/

删除以消除混淆，保持代码结构清晰。历史可通过 Git 恢复。"
```

### 风险评估

- **技术风险**：极低（已验证无依赖）
- **回滚成本**：极低（`git revert` 即可）
- **收益**：清晰的代码结构，减少维护负担

### 替代方案

如果担心直接删除，可以：
1. 重命名为 `server/app/_archived_modules/`
2. 添加 README 说明这是未使用的历史代码
3. 在下个版本再删除

但考虑到 Git 已完整保留历史，直接删除更干净。
