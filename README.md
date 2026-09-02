# 患者端项目说明

这是课程项目中的患者端最小可运行版本，当前重点是打通管理员派发到患者答题提交的演示闭环。

## 目录作用

- `src/`
  - 前端源码目录。
- `src/components/`
  - 可复用 UI 与量表渲染组件，例如布局、题目渲染器。
- `src/data/`
  - 配置驱动的数据定义目录。
- `src/data/assessments/`
  - 量表定义与评分配置，目前包含 `SCD-Q9`。
- `src/lib/`
  - 通用工具与浏览器存储封装。
- `src/pages/`
  - 路由页面组件。
- `src/repositories/`
  - 数据访问层，目前为 `mockRepository`，后续可替换成真实 API。
- `src/styles/`
  - 全局样式与主题入口。
- `src/types/`
  - TypeScript 类型定义。
- `assets/`
  - 课程资料中提取的图片参考资源，用于后续特殊任务实现。
- `docs/`
  - 项目原始说明、量表规格、交互任务与补充状态文档。
- `docs/sources/`
  - 从课程 PDF 中整理出的文本材料。
- `docs/status/`
  - 项目阶段状态和任务完成情况说明。
- `dist/`
  - 生产构建输出目录。
- `node_modules/`
  - 依赖安装目录，不提交到仓库。

## 关键文件

- `package.json`
  - 项目依赖与脚本定义。
- `vite.config.ts`
  - Vite 构建配置。
- `tsconfig.json`
  - TypeScript 工程入口配置。
- `tsconfig.app.json`
  - 前端应用编译配置。
- `index.html`
  - Vite 入口 HTML。
- `00_CODEX_START.md`
  - Codex 执行指令文件，仅用于本地协作，不建议提交到公共仓库。
- `README_FIRST.md`
  - 启动包说明文件，仅用于本地协作，不建议提交到公共仓库。

## 当前实现范围

- 已实现：登录入口、管理员派发、患者任务中心、SCD-Q9 答题、提交完成页。
- 未实现：GDS-15、ESS、历史记录、Boston、STT、AI mock。

## 运行方式

见 [STARTUP.md](/mnt/d/Workspace/NCS/Project/Patient/STARTUP.md)。
