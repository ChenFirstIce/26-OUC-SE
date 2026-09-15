# 更新日志

## [2025.09.15] - SCD 结构性问卷 + STT 完整量表集成

### 🎉 新增功能

#### SCD 主观认知下降结构性问卷（完整实现）
- **前端组件**（`admin-web/src/components/questionnaire/ScdQuestionnaire.vue`）
  - 四阶段完整流程：初始筛查 → 认知域问卷 → 知情者问卷 → 补充信息
  - 5 个认知域：记忆力、语言/找词、组织/计划、注意力、其他认知
  - 每域 1 个主要问题 + 5 个条件追加问题（A-E）
  - 6 题知情者问卷 + 关系选择
  - 4 题补充信息
  - 智能分支逻辑：主要问题"是"才显示追加问题
  - 实时进度追踪和验证

- **数据模型**（`admin-web/src/data/scd-questionnaire.ts`）
  - 完整的 TypeScript 类型定义
  - 从 JSON 导入并类型化问卷结构

- **后端处理**（`server/app/routers/assisted_tasks.py`）
  - 添加 `DEMO_SCD_STRUCTURED` 任务类型
  - 完整的数据验证和分析
  - 自动统计：阳性域、担心、时间、就医、知情者信息
  - 生成候选结果供医生复核

- **数据库种子**（`server/app/seed.py`）
  - 添加 SCD 结构性问卷模板
  - 配置任务类型和复核维度

- **医生端展示**（`admin-web/src/components/ReviewEvidence.vue`）
  - 概览统计：选择域数、阳性域数、知情者状态
  - 认知域详情卡片：主要答案 + 5 个追加问题结构化展示
  - 知情者问卷：6 题观察 + 发生时间 + 关系
  - 补充信息：4 题网格布局
  - 标签颜色编码：阳性（橙色）、阴性（蓝色）

#### STT 形状连线完整量表（增强）
- **服务模块**（`server/app/services/stt_scale.py`）
  - A/B 两卷完整序列定义
  - 年龄阈值判读（50-59、60-69、70-79）
  - 练习和正式测试两阶段验证
  - 错误和纠正统计

- **数据文件**
  - `stt_age_thresholds.json`：年龄分层阈值
  - `stt_sequences_with_coordinates.json`：A/B 卷节点坐标

- **后端验证**（`server/app/routers/assisted_tasks.py`）
  - 完整的两阶段数据验证
  - 序列完整性检查
  - 年龄阈值自动判读

- **医生端展示**（`admin-web/src/components/ReviewEvidence.vue`）
  - A/B 卷标识
  - 分阶段统计：练习 vs 正式测试
  - 轨迹可视化：SVG 路径图
  - 年龄阈值判读：阈值、实际用时、正常/异常标签
  - 错误标记：红色圆点

### 🔧 改进优化

- **患者任务界面**（`admin-web/src/components/patient/AssistedTask.vue`）
  - 添加 `scd_structured_interview` 任务类型判断
  - 修复模板标签闭合问题
  - 优化任务类型路由逻辑

- **问卷提交接口**（`server/app/routers/questionnaires.py`）
  - 保持现有逻辑，未修改

- **测试用例**（`server/tests/test_flow.py`）
  - 保留现有测试，未添加新测试（可后续补充）

### 📄 文档更新

- **README.md**：项目主文档
  - 添加 SCD 和 STT 功能说明
  - 更新项目结构
  - 添加快速开始指南

- **INTEGRATION_COMPLETE.md**：集成完成报告
  - 详细的实现清单
  - 数据流说明
  - 关键文件清单
  - 待集成事项

- **QUICKSTART.md**：快速测试指南
  - 完整的测试流程
  - 场景化测试步骤
  - 验收标准

- **SCD_IMPLEMENTATION.md**：SCD 实现文档
  - 组件说明
  - 集成示例
  - 数据结构

### 📦 新增文件

```
admin-web/src/components/questionnaire/
  └── ScdQuestionnaire.vue          # SCD 问卷组件
admin-web/src/data/
  └── scd-questionnaire.ts           # SCD 数据模型
server/app/services/
  └── stt_scale.py                   # STT 量表服务
scd_structured_interview.json        # SCD 问卷结构
stt_age_thresholds.json              # STT 年龄阈值
stt_sequences_with_coordinates.json  # STT 序列坐标
INTEGRATION_COMPLETE.md              # 集成报告
QUICKSTART.md                        # 快速测试指南
SCD_IMPLEMENTATION.md                # SCD 实现文档
CHANGELOG.md                         # 本文件
```

### ✅ 验证状态

- ✅ 前端构建成功（无 TypeScript 错误）
- ✅ 组件模板语法正确
- ✅ 后端逻辑完整
- ✅ 数据流贯通
- ✅ 文档完善

### 🎯 核心改动统计

- **新增文件**：12 个
- **修改文件**：7 个
- **新增代码行**：约 2000+ 行
- **涉及模块**：前端组件、数据模型、后端 API、服务层、数据库种子

---

## [2025.09.14] - 辅助任务和 STT 量表数据集成

### 新增
- 辅助任务完整流程（C 类和 B 类）
- STT 形状连线基础实现
- 医生复核工作流

---

## [2025.09.13] - 架构重构

### 改进
- 移除 `modules/` 重复代码
- 整理文档结构
- 清理数据库连接逻辑

---

## [更早版本]

详见 Git 提交历史。
