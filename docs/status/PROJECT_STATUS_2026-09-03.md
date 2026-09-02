# 项目状态说明

更新时间：2026-09-03

## 当前阶段

项目已完成患者端最小可运行版本（MVP）。

## 已完成任务

- 完成 `Vite + React + TypeScript + Tailwind CSS + React Router` 工程初始化。
- 完成患者端基础页面：`/login`、`/home`、`/admin`、`/assessment/:id`、`/assessment/:id/complete`。
- 建立统一基础布局和面向中老年用户的首版样式。
- 建立 Assessment 基础类型与可扩展目录结构。
- 录入真实 `SCD-Q9` 题目与评分规则，并采用配置驱动实现。
- 实现最小 Assessment Engine：
  - `AssessmentRenderer`
  - `QuestionRenderer`
  - `YesNoQuestion`
  - `SingleChoiceQuestion`
- 实现答题进度、上一题/下一题、禁用状态、防重复提交。
- 实现基于 `localStorage` 的 Mock 数据层：
  - 演示患者
  - 任务派发
  - 草稿保存
  - 提交记录
  - 完成状态
- 打通首条业务闭环：
  - `/admin` 派发 `SCD-Q9`
  - `/home` 查看任务
  - `/assessment/scd-q9` 完成作答
  - `/assessment/scd-q9/complete` 查看提交结果
- 已验证：
  - `npm install`
  - `npm run build`
  - `npm run dev`

## 当前未完成任务

- `GDS-15`
- `ESS`
- 爱丁堡利手量表
- Boston Naming Task
- STT 形状连线
- SCD 结构化访谈 mock
- MoCA-B 开放回答 mock
- 历史记录页 `/history`
- 说明页 `/assessment/:assignmentId/intro`
- 更完整的管理员功能：
  - 批量派发
  - 重置进度
  - 查看全部提交 JSON

## 建议后续顺序

1. 先补 `GDS-15` 与 `ESS`，复用当前量表引擎。
2. 增加 `/history` 和管理员提交查看能力，完善演示闭环。
3. 再进入 `Boston` 与 `STT` 等特殊交互任务。
4. 最后实现 `SCD interview` 与 `MoCA-B` 的 AI mock。

## 当前数据存储方式

- 所有运行数据都保存在浏览器 `localStorage`。
- 不依赖真实后端、数据库或登录系统。
- 后续可通过替换 `src/repositories/mockRepository.ts` 迁移到真实 API。
