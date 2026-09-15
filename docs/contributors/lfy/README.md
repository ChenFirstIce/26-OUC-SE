# lfy 贡献文档

时间：2026-09-03

## 主要贡献

### 患者端 React 原型
- 患者端 MVP 骨架
- 逐题填写交互
- 答题进度跟踪
- 完成记录历史页面

### 量表配置
- SCD-Q9 量表
- GDS-15 量表（含反向计分）
- ESS 量表
- Edinburgh 利手量表

### 原始资料与参考
- assets/ - 图片素材
- docs/ - 量表说明文档
  - INTERACTIVE_TASKS.md - 交互任务规范
  - PATIENT_SCALE_SPEC.md - 患者量表规范
  - PROJECT_SPEC.md - 项目规范
  - TEMPLATE_REFERENCES.md - 模板参考
  - sources/ - 量表来源说明
  - status/ - 项目状态快照

## 技术栈
- React + TypeScript
- Zustand (状态管理)
- 浏览器本地存储

## 相关 Git 提交
```
91e923b - 2026-09-03 04:01 - feat: add patient app MVP skeleton
32e5acc - 2026-09-03 04:06 - docs: move status and startup documentation
5225ab6 - 2026-09-03 15:52 - feat: expand patient MVP assessment flow
```

## 注意
lfy 原型使用浏览器本地存储和 Mock 数据，未连接后端。正式系统已将其交互模式迁移到 Vue + 后端 API。
