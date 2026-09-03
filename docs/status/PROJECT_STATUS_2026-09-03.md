# 项目状态说明

更新时间：2026-09-03

## 当前阶段

项目已完成患者端最小可运行版本（MVP）。

## 本次更新进度

- 已完成 `GDS-15` 量表定义、评分函数与接入。
- 已完成 `ESS` 量表定义、评分函数与接入。
- 已完成 `爱丁堡利手量表` 定义、利手指数计算与接入。
- 已完成管理员模式扩展，支持派发 `SCD-Q9`、`GDS-15`、`ESS`，并支持一键派发全部 A 类演示量表。
- 已完成页面样式第二轮收口，新增统一的卡片、按钮、指标卡组件，进一步贴近计划中的模板化方向。
- 已补齐 MVP 范围内的 `History` 页面、量表说明页、管理员重置演示数据与提交 JSON 查看能力。

## 已完成任务

- 完成 `Vite + React + TypeScript + Tailwind CSS + React Router` 工程初始化。
- 完成患者端基础页面：`/login`、`/home`、`/history`、`/admin`、`/assessment/:id/intro`、`/assessment/:id`、`/assessment/:id/complete`。
- 建立统一基础布局和面向中老年用户的首版样式。
- 建立 Assessment 基础类型与可扩展目录结构。
- 录入真实 `SCD-Q9` 题目与评分规则，并采用配置驱动实现。
- 录入真实 `GDS-15` 题目与评分规则，并采用配置驱动实现。
- 录入真实 `ESS` 场景题与评分规则，并采用配置驱动实现。
- 录入真实 `爱丁堡利手量表` 动作题与评分规则，并采用配置驱动实现。
- 实现最小 Assessment Engine：
  - `AssessmentRenderer`
  - `QuestionRenderer`
  - `YesNoQuestion`
  - `SingleChoiceQuestion`
- 扩展管理员测试模式：
  - 可选择派发 `SCD-Q9`
  - 可选择派发 `GDS-15`
  - 可选择派发 `ESS`
  - 可选择派发 `爱丁堡利手量表`
  - 可一键派发全部首批 A 类演示量表
- 建立统一 UI 原语：
  - `GlassCard`
  - `SurfaceCard`
  - `ActionButton`
  - `MetricCard`
  - `StatusPill`
- 实现答题进度、上一题/下一题、禁用状态、防重复提交。
- 实现基于 `localStorage` 的 Mock 数据层：
  - 演示患者
  - 任务派发
  - 草稿保存
  - 提交记录
  - 完成状态
- 打通首条业务闭环：
  - `/admin` 派发 `SCD-Q9` / `GDS-15` / `ESS` / `爱丁堡利手量表`
  - `/home` 查看任务
  - `/assessment/:id/intro` 查看说明
  - `/assessment/:id` 完成作答
  - `/assessment/:id/complete` 查看提交结果
  - `/history` 查看历史提交
- 已验证：
  - `npm install` 于 2026-09-03 在当前 WSL 环境执行成功
  - `npm run build` 于 2026-09-03 在当前 WSL 环境执行成功
  - `npm run dev` 于 2026-09-03 在当前 WSL 环境启动成功，Vite 输出 `http://localhost:5173/`
- 当前环境说明：
  - 当前 Codex 执行环境的 `git` 缺少 `remote-https`，因此无法直接 `git clone` 计划中的在线参考模板到 `.references/`。

## 当前未完成任务

- Boston Naming Task
- STT 形状连线
- SCD 结构化访谈 mock
- MoCA-B 开放回答 mock
- 更完整的管理员功能：
  - 更细粒度的任务状态切换
  - 更完整的提交筛选与查看

## 建议后续顺序

1. 先补 `GDS-15` 与 `ESS`，复用当前量表引擎。
2. 进入 `Boston` 与 `STT` 等特殊交互任务。
3. 最后实现 `SCD interview` 与 `MoCA-B` 的 AI mock。

## 当前数据存储方式

- 所有运行数据都保存在浏览器 `localStorage`。
- 不依赖真实后端、数据库或登录系统。
- 后续可通过替换 `src/repositories/mockRepository.ts` 迁移到真实 API。
