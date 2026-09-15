# SCD 结构性问卷实现清单

## 已完成文件

### 1. 数据模型
**文件**: `admin-web/src/data/scd-questionnaire.ts`
- 定义完整的 TypeScript 类型
- 导入并导出 JSON 数据
- 提供认知域标签映射
- 知情者关系和可用性选项

### 2. Vue 组件
**文件**: `admin-web/src/components/questionnaire/ScdQuestionnaire.vue`
- 完整的四阶段问卷流程
- 响应式进度追踪
- 分支逻辑实现
- 样式符合项目设计规范

### 3. 文档
**文件**: `admin-web/src/components/questionnaire/README.md`
- 详细的组件使用说明
- 问卷结构文档
- 数据格式规范
- 集成指南

### 4. 项目文档更新
**文件**: `README.md`
- 添加 SCD 结构性问卷说明

## 核心功能

### ✓ 初始筛查阶段
- 多选认知域选择
- 可视化选中状态
- 至少选择一项验证

### ✓ 认知域问卷阶段
- 主要问题（是/否）
- 条件显示追加问题 A-E
- 支持单选和文本输入
- 前后导航

### ✓ 知情者问卷阶段
- 可用性检查
- 关系选择
- 6 题观察问题
- 条件追问开始时间

### ✓ 补充信息阶段
- 4 题补充问题
- 所有选项单选

### ✓ 进度管理
- 实时进度条
- 步骤计数显示
- 百分比计算

### ✓ 数据收集
- 结构化答案存储
- 完整数据输出
- 时间戳记录

## 待集成事项

### 后端 API 集成
需要在 `server/app/routers/` 添加端点处理 SCD 问卷提交：

```python
@router.post("/assisted-tasks/{task_id}/scd-submit")
async def submit_scd_questionnaire(
    task_id: int,
    results: dict,
    db: Session = Depends(get_db)
):
    # 保存 SCD 问卷结果
    # 更新任务状态
    pass
```

### 数据库模型
可能需要专门的表存储 SCD 结果，或扩展现有的 `assisted_tasks` 表。

### 任务类型注册
在 `AssistedTask.vue` 中添加 SCD 任务类型判断：

```vue
<ScdQuestionnaire v-else-if="kind === 'scd_structured'" :task="task" @complete="emit('complete')" />
```

### 医生端查看
在 `ReviewEvidence.vue` 中添加 SCD 结果展示逻辑。

## 技术特点

1. **类型安全**: 完整 TypeScript 类型定义
2. **响应式**: Vue 3 Composition API
3. **可维护**: 清晰的组件结构和注释
4. **可扩展**: 易于添加新问题或修改逻辑
5. **设计一致**: 遵循项目设计系统

## 数据流

```
JSON 数据源
    ↓
scd-questionnaire.ts (类型化数据模型)
    ↓
ScdQuestionnaire.vue (UI 和交互逻辑)
    ↓
提交到后端 API (待实现)
    ↓
数据库存储 (待实现)
    ↓
医生端查看 (待实现)
```

## 测试建议

1. **单元测试**: 测试分支逻辑和数据验证
2. **集成测试**: 测试完整流程和 API 集成
3. **用户测试**: 验证问卷流程的用户体验
4. **数据验证**: 确保输出格式符合预期

## 下一步

1. 实现后端 API 端点
2. 更新数据库模型
3. 在 AssistedTask.vue 中注册任务类型
4. 实现医生端结果查看
5. 添加数据验证和错误处理
6. 编写自动化测试
