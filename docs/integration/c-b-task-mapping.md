# C/B 任务正式资料映射索引

**文档目的**：建立从当前代码实现到来源 PDF 的完整映射关系，明确哪些字段使用临时占位数据，哪些需要替换为正式材料，以及从何处获取。

**更新时间**：2026-09-15  
**维护人**：Claude Code  
**关联**：`docs/integration/cyf-handoff.md` 第 44-47 行建议

---

## 快速查看

| 任务 | 代码位置 | PDF 来源 | 映射状态 | 优先级 |
|------|---------|---------|---------|--------|
| **Boston 命名** | `demo-data.ts:15-19` | 第 16 页 | ⚠️ 占位（3/30） | P0 |
| **STT 连线** | `stt-scale.ts` + `TrailMakingPage.tsx` | 第 17-20 页 | ✅ 来源参考端已接入 JSON 坐标与阈值 | P0 |
| **MoCA-B 开放题** | `moca-open.ts:28-45` | 第 10-12 页 | ⚠️ 部分（2/10+） | P1 |
| **SCD 访谈** | `assisted_tasks.py:21-26` | 第 7-10 页 | ❌ Mock（3 轮） | P0 |

---

## 1. Boston 命名测试

### 代码实现

| 层级 | 文件 | 行号 | 内容 |
|------|------|------|------|
| 前端数据 | `patient-web/c2b/Frontend/src/data/demo-data.ts` | 15-19 | `bostonQuestions` 数组（当前 3 个占位题） |
| 后端逻辑 | `server/app/routers/assisted_tasks.py` | 90-99 | 答案校验、图片展示逻辑 |
| 问卷版本 | `server/app/seed.py` | DEMO_BOSTON | scoring_json 配置 |

### PDF 来源

| 内容 | 文件 | 页码 | 章节 |
|------|------|------|------|
| **30 个题目名称** | `1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf` | 第 16 页 | H5 |
| **施测说明** | `4.最新量表操作说明修订版.pdf` | 第 4 页 | Boston Naming Test |
| **评分规则** | `4.最新量表操作说明修订版.pdf` | 第 4 页 | 教育分层节点值 |
| **文本参考** | `docs/references/lfy/docs/sources/01_SCD基线量表_文本版.md` | H5 章节 | 完整题目列表 |

### 映射表

| 字段 | 当前值 | 正式来源 | 差异 | 状态 |
|------|--------|----------|------|------|
| `questions[].id` | `demo_boston_01`, `demo_boston_02`, `demo_boston_03` | 应为 30 个（boston_01 ~ boston_30） | 占位 3 个 | ❌ |
| `questions[].name` | 雨伞、自行车、苹果 | PDF H5 列表：树、笔、剪刀、花、... | 占位三个不同题目 | ❌ |
| `questions[].image` | SVG emoji (☂️, 🚲, 🍎) | 30 张正式图片或 `2.量表模板.pdf` 扫描 | Demo 占位 | ❌ |
| `questions[].semanticHint` | 无 | PDF 施测说明中的类别提示 | 缺失 | ❌ |
| `administration.namingWindow` | 无 | 20 秒 | 缺失 | ⚠️ |
| `administration.semanticCueAllowed` | 无 | true | 缺失 | ⚠️ |
| `cutoffThresholds.middle_school` | 无 | 19 分 | 缺失 | ⚠️ |
| `cutoffThresholds.high_school` | 无 | 21 分 | 缺失 | ⚠️ |
| `cutoffThresholds.college` | 无 | 22 分 | 缺失 | ⚠️ |

### 网页 AI 映射任务

#### 任务 1A：Boston 题目提取

**输入**：`1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf` 第 16 页  
**Prompt**：
```
请从 PDF 第 16 页的 H5 章节提取 Boston 命名测试的 30 个题目。

输出格式（JSON）：
[
  {"id": "boston_01", "name": "树", "semanticHint": "植物", "order": 1},
  {"id": "boston_02", "name": "笔", "semanticHint": "文具", "order": 2}
  // ... 共 30 个
]

字段说明：
- id: 格式为 boston_01 到 boston_30（两位补零）
- name: 题目中文名称（如无特殊说明，保持原始文本）
- semanticHint: PDF 中的类别/提示（如无则留空字符串）
- order: 题目顺序（1-30）
```

**预期输出**：30 个题目的结构化数据（包括树、笔、剪刀、花、锯子、扫把、蘑菇...）

**映射目标**：
```
→ patient-web/c2b/Frontend/src/data/demo-data.ts: bostonQuestions[]
→ server/app/seed.py: DEMO_BOSTON scoring_json.expected_answers
```

#### 任务 1B：Boston 评分规则提取

**输入**：`4.最新量表操作说明修订版.pdf` 第 4 页  
**Prompt**：
```
请从 PDF 第 4 页提取 Boston 命名测试的评分规则和教育分层节点值。

输出格式（JSON）：
{
  "administration": {
    "namingWindow": 20,
    "namingWindowUnit": "seconds",
    "semanticCueAllowed": true,
    "phoneticCueAllowed": true,
    "multipleChoiceAllowed": true
  },
  "cutoffThresholds": {
    "middle_school": 19,
    "high_school": 21,
    "college": 22
  },
  "scoringNotes": "..."
}
```

**映射目标**：
```
→ server/app/seed.py: DEMO_BOSTON scoring_json
```

### 缺口清单

| 缺口 | 来源类型 | 优先级 | 工作量 | 备注 |
|------|----------|--------|--------|------|
| 30 张题目图片 | 联系项目方/扫描 PDF | P0 | 复杂 | `2.量表模板.pdf` 当前损坏，需从其他渠道获取 |
| 30 个题目名称 | PDF 提取 | P0 | 简单 | 网页 AI 可直接提取 |
| 语义提示映射 | PDF 提取 | P0 | 简单 | 网页 AI 可直接提取 |
| 教育分层节点值 | PDF 提取 | P0 | 简单 | 网页 AI 可直接提取 |

---

## 2. STT 形状连线测试

### 代码实现

| 层级 | 文件 | 行号 | 内容 |
|------|------|------|------|
| 前端数据 | `patient-web/c2b/Frontend/src/data/stt-scale.ts` | - | 读取 STT 坐标 JSON、阈值 JSON 并缩放为网页坐标 |
| 前端页面 | `patient-web/c2b/Frontend/src/pages/TrailMakingPage.tsx` | - | STT-A/B、练习/正式、干扰节点、计时、错误和阈值判读 |
| 后端逻辑 | `server/app/routers/assisted_tasks.py` | 100-137 | 事件校验、坐标验证、错误计算 |
| 问卷版本 | `server/app/seed.py` | DEMO_TRAIL | scoring_json 配置 |

### PDF 来源

| 内容 | 文件 | 页码 | 章节 |
|------|------|------|------|
| **STT-A/B 图形** | `1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf` | 第 17-20 页 | H6 |
| **施测说明** | `4.最新量表操作说明修订版.pdf` | 第 5 页 | STT |
| **参考图片** | `docs/references/lfy/docs/assets/stt_form_a_reference.png` | - | STT-A 完整形态 |
| **参考图片** | `docs/references/lfy/docs/assets/stt_form_b_test_reference.png` | - | STT-B 完整形态 |

### 映射表

| 字段 | 当前值 | 正式来源 | 差异 | 状态 |
|------|--------|----------|------|------|
| `coordinate_system` | `1489 × 2105 px` | PDF 图像坐标系 | 已保留来源并按网页画布缩放 | ✅ |
| `nodes[].id` | `shape-label-x-y` | 来自坐标 JSON 的唯一节点键 | 可区分 STT-B 同数字不同形状节点 | ✅ |
| `nodes[].x/y` | 0-100 百分比 | 由 PDF px 坐标换算 | 网页自适应显示 | ✅ |
| `nodes[].shape` | `circle` / `square` | 坐标 JSON | 已用于节点渲染与下一目标提示 | ✅ |
| `sequence` | STT-A/B practice/test 正确节点序列 | 坐标 JSON | A/B 正式各 25 个目标节点；B 同时渲染干扰节点 | ✅ |
| `STT_A_thresholds` | 50-59:70s, 60-69:80s, 70-79:100s | 年龄阈值 JSON | 已用于结果判读 | ✅ |
| `STT_B_thresholds` | 50-59:180s, 60-69:200s, 70-79:240s | 年龄阈值 JSON | 已用于结果判读 | ✅ |

### 网页 AI 映射任务

#### 任务 2A：STT 序列提取

**输入**：`1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf` 第 17-20 页  
**Prompt**：
```
请从 PDF 第 17-20 页提取 STT-A 和 STT-B 的完整序列。

输出格式（JSON）：
{
  "STT_A_practice": ["1", "2", "3", ...],
  "STT_A_test": ["1", "2", "3", ...],
  "STT_B_practice": ["1", "circle", "2", "square", ...],
  "STT_B_test": ["1", "circle", "2", "square", ...]
}

字段说明：
- 数字用字符串表示（如 "1", "2"）
- 形状用英文标识：圆形="circle", 正方形="square"
- 如无明确标注，根据 PDF 图示推断
```

**预期输出**：4 个数组，包含完整的节点序列

**映射目标**：
```
→ patient-web/c2b/Frontend/src/data/demo-data.ts: trailSequence
→ server/app/seed.py: DEMO_TRAIL scoring_json.sequence
```

#### 任务 2B：STT 年龄分层节点值提取

**输入**：`4.最新量表操作说明修订版.pdf` 第 5 页  
**Prompt**：
```
请从 PDF 第 5 页提取 STT 的年龄分层节点值（异常阈值）。

输出格式（JSON）：
{
  "STT_A_thresholds": {"50-59": 70, "60-69": 80, "70-79": 100},
  "STT_B_thresholds": {"50-59": 180, "60-69": 200, "70-79": 240},
  "unit": "seconds",
  "interpretation": "超过对应年龄阈值为异常"
}
```

**映射目标**：
```
→ server/app/seed.py: DEMO_TRAIL scoring_json
```

### 坐标提取方法

**当前坐标接入**：
1. 原始文件：`patient-web/stt_sequences_with_coordinates.json`，坐标系为 PDF `1489 × 2105 px`、左上角原点、节点中心点。
2. 适配文件：`patient-web/c2b/Frontend/src/data/stt-scale.ts`，将 `x / 1489 * 100`、`y / 2105 * 100` 转为 SVG 百分比坐标，同时保留 `sourceX/sourceY` 便于追溯。
3. STT-B 使用 `*_all_nodes` 渲染全部节点，使用 `STT_B_practice` / `STT_B_test` 判定正确路径，因此同一数字的圆形/方形节点不会冲突。
4. 年龄阈值来自 `patient-web/stt_age_thresholds.json`，页面按 50-59、60-69、70-79 岁分层判读“达到或超过对应阈值为异常”。

### 缺口清单

| 缺口 | 来源类型 | 优先级 | 工作量 | 备注 |
|------|----------|--------|--------|------|
| STT-A/B 完整序列 | JSON 接入 | P0 | 已完成 | React 来源参考端已使用完整序列 |
| 节点坐标提取 | JSON 接入 | P0 | 已完成 | 已从 PDF px 坐标缩放至网页 SVG |
| 年龄分层节点值 | JSON 接入 | P0 | 已完成 | 页面已判读阈值 |
| 正式患者端同步 | 代码开发 | P0 | 待办 | 统一 Vue 患者入口的 DEMO_TRAIL 仍需按同一 JSON 替换锁定版本配置 |

---

## 3. MoCA-B 开放题

### 代码实现

| 层级 | 文件 | 行号 | 内容 |
|------|------|------|------|
| 前端数据 | `patient-web/c2b/Frontend/src/data/moca-open.ts` | 28-45 | `mocaOpenTasks` 数组（当前 2 个） |
| 后端规则 | `server/app/services/moca_open.py` | 5-90 | 本地评分规则 |
| 问卷版本 | `server/app/seed.py` | DEMO_MOCA_OPEN | MoCA-B 问卷配置 |

### PDF 来源

| 内容 | 文件 | 页码 | 章节 |
|------|------|------|------|
| **MoCA-B 模板** | `3.量表MoCA模板.pdf` | 1 页 | 完整量表视图 |
| **施测说明** | `4.最新量表操作说明修订版.pdf` | 第 10-12 页 | H15（MoCA-B） |
| **评分规则** | `docs/references/lfy/docs/sources/04_评分手册_文本版.md` | 第 10-12 页 | 完整评分规则 |
| **视觉素材** | `docs/references/lfy/docs/assets/moca_b_template.png` | - | MoCA-B 完整图示 |

### 当前实现状态

#### ✅ 已实现任务（2/10+）

**1. 计算（付款方式，moca_payment_13）**

| 项 | 值 |
|----|-----|
| PDF 来源 | `4.最新量表操作说明修订版.pdf` 第 11 页 |
| 指导语 | "如果买东西需要付 13 元，请写出 3 种不同的付款方式" |
| 满分 | 3 分 |
| 评分规则 | 3 种=3 分，2 种=2 分，1 种=1 分 |
| 代码实现 | `server/app/services/moca_open.py:45-50` 使用正则识别 |
| 映射状态 | ✅ 指导语、评分规则已对齐 |

**2. 抽象（分类，moca_abstraction）**

| 项 | 值 |
|----|-----|
| PDF 来源 | `4.最新量表操作说明修订版.pdf` 第 11 页 |
| 指导语 | "请分别说明以下三组词语的共同类别：火车/轮船、锣鼓/笛子、南方/北方" |
| 满分 | 3 分（每组 1 分） |
| 正确答案 | 交通工具/旅行/运输 · 乐器/娱乐 · 方向/地点/地理位置 |
| 代码实现 | `server/app/services/moca_open.py:52-65` 关键词匹配 |
| 映射状态 | ✅ 三组关键词已覆盖（但有变体如"车船"） |

#### ❌ 未实现任务（8/10+）

| 序号 | 任务 | PDF 来源 | 满分 | 状态 |
|------|------|----------|------|------|
| 1 | 执行功能（连线） | PDF H15.1 | 1 | ❌ |
| 2 | 即刻回忆（5 词） | PDF H15.2 (马、红、桌子、帽子、飞机) | 5 | ❌ |
| 3 | 词语流畅性（水果） | PDF H15.3 (60 秒说水果名) | 1 | ❌ |
| 4 | 定向 | PDF H15.4 (日期、地点等) | 6 | ❌ |
| ✅ | **计算（付款）** | **PDF H15.5** | **3** | **✅** |
| ✅ | **抽象（分类）** | **PDF H15.6** | **3** | **✅** |
| 7 | 延迟回忆 | PDF H15.7 (回忆前 5 词) | 5 | ❌ |
| 8 | 视知觉（重叠物） | PDF H15.8 (识别 3 个重叠图) | 3 | ❌ |
| 9 | 命名（动物） | PDF H15.9 (斑马、孔雀、老虎、蝴蝶) | 4 | ❌ |
| 10 | 注意（数字选择） | PDF H15.10 (点击目标数字) | 1 | ❌ |

**总分**：当前 6 分（2 个任务），正式 30 分（10+ 个任务）

### 网页 AI 映射任务

#### 任务 3A：MoCA-B 完整任务列表提取

**输入**：`4.最新量表操作说明修订版.pdf` 第 10-12 页  
**Prompt**：
```
请从 PDF 第 10-12 页提取 MoCA-B 的完整任务列表、指导语、评分规则和教育分层节点值。

输出格式（JSON）：
{
  "tasks": [
    {
      "id": "moca_trail",
      "name": "执行功能（连线）",
      "instruction": "请按顺序连接数字和字母",
      "maxScore": 1,
      "scoringRule": "完成计 1 分"
    },
    // ... 共 10+ 个任务
  ],
  "cutoffThresholds": {
    "illiterate_primary": 19,
    "middle_school": 22,
    "college": 24
  },
  "totalMaxScore": 30
}
```

**预期输出**：10 个认知任务的完整定义

**映射目标**：
```
→ server/app/seed.py: 新建完整 MoCA-B 问卷版本配置
→ server/app/services/moca_open.py: 扩展任务定义
```

### 缺口清单

| 缺口 | 来源类型 | 优先级 | 工作量 | 备注 |
|------|----------|--------|--------|------|
| 8 个任务定义 | PDF 提取 | P1 | 简单 | 网页 AI 可直接提取 |
| 视觉图片素材 | 图片提取/设计 | P1 | 复杂 | 需从 `moca_b_template.png` 提取或新设计 |
| 教育分层节点值 | PDF 提取 | P1 | 简单 | 网页 AI 可直接提取 |
| 前端交互实现 | 代码开发 | P1 | 复杂 | 8 个任务需前端页面支持 |

---

## 4. SCD 结构化访谈

### 代码实现

| 层级 | 文件 | 行号 | 内容 |
|------|------|------|------|
| 前端初始消息 | `patient-web/c2b/Frontend/src/data/demo-data.ts` | 32 | 硬编码初始问题 |
| 后端对话逻辑 | `server/app/routers/assisted_tasks.py` | 21-26 | `MOCK_REPLIES` 临时对话 |
| LLM 调用 | `server/app/services/deepseek.py` | - | 未实现（当前空）|

### PDF 来源

| 内容 | 文件 | 页码 | 章节 |
|------|------|------|------|
| **完整问卷结构** | `1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf` | 第 7-10 页 | Section D (E 章节) |
| **文本参考** | `docs/references/lfy/docs/sources/01_SCD基线量表_文本版.md` | E 章节 | 完整问题树 |

### 当前实现状态

**临时 Mock 对话**（`assisted_tasks.py:21-26`）：
```python
MOCK_REPLIES = [
    ("这种变化大约从什么时候开始？请按实际感受回答。", .4, False),
    ("这种变化是否影响过日常安排？可以简单举一个例子。", .7, False),
    ("感谢您的回答，本次访谈记录已完成，后续由专业人员查看。", 1.0, True),
]
```

**状态**：❌ 仅 3 轮对话，缺少完整的状态机

### 访谈完整结构

#### 1. 初始问题（5 个认知域）

| 域 | 初始问题 | PDF 来源 | 状态 |
|----|---------|----------|------|
| 记忆力 | "最近您是否感觉自己的记忆力与以前相比发生了变化？" | E.1 | ❌ |
| 语言/找词困难 | "最近您是否感觉说话时找词困难？" | E.2 | ❌ |
| 组织能力/计划能力 | "最近您是否感觉做事计划和安排比以前困难？" | E.3 | ❌ |
| 注意力/专心 | "最近您是否感觉注意力难以集中？" | E.4 | ❌ |
| 其他认知功能 | "除了上述方面，您是否还有其他认知方面的变化？" | E.5 | ❌ |

#### 2. 主要问题（1-5，每域 5 个问题）

| 问题位置 | 示例（记忆域） | PDF 来源 | 说明 |
|---------|-------------|----------|------|
| 主要 1 | "具体是什么样的变化？" | E.1.Q1 | 初步了解具体症状 |
| 主要 2 | "这种变化大约从什么时候开始？" | E.1.Q2 | 发病时间 |
| 主要 3 | "这种变化是否影响过日常安排？" | E.1.Q3 | 功能影响 |
| 主要 4 | "您能举一个具体例子吗？" | E.1.Q4 | 具体实例 |
| 主要 5 | "这种情况是一直存在还是时好时坏？" | E.1.Q5 | 波动特征 |

**状态**：❌ 每个认知域需配置 5 个主要问题

#### 3. 额外问题（A-E，若主要问题回答"是"）

| 问题 | 指导语 | 选项 | 值 | PDF 来源 |
|------|--------|------|-----|----------|
| **A** | 您是否为此担心？ | 否/是 | 0/1 | E.A |
| **B** | 什么时候开始变差？ | 近 6 个月/6 月-2 年/2-5 年/超 5 年/不清楚 | 1/2/3/4/5 | E.B |
| **C** | 是否比同龄人差？ | 否/是 | 0/1 | E.C |
| **D** | 是否因此看过医生？ | 否/是 | 0/1 | E.D |
| **E** | 第一次与医生谈是何时？ | 开放文本 (月数) | - | E.E |

**状态**：❌ 需配置状态转移规则（何时触发 A-E 子问题）

#### 4. 知情者问卷（6 个问题）

| 序号 | 问题 | PDF 来源 |
|------|------|----------|
| 1 | 您有没有观察到患者记忆力的变化？ | E 知情者部分 |
| 2 | 您有没有观察到患者语言表达的变化？ | E 知情者部分 |
| 3 | 您有没有观察到患者做事计划能力的变化？ | E 知情者部分 |
| 4 | 您有没有观察到患者注意力的变化？ | E 知情者部分 |
| 5 | 您有没有观察到患者其他认知方面的变化？ | E 知情者部分 |
| 6 | 这些变化对患者日常生活造成了多大影响？ | E 知情者部分 |

**状态**：❌ 当前未实现

### 网页 AI 映射任务

#### 任务 4A：SCD 完整问题树提取

**输入**：`1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf` 第 7-10 页  
**Prompt**：
```
请从 PDF 第 7-10 页的 Section D（SCD 结构化访谈）提取完整问题树。

输出格式（JSON）：
{
  "cognitiveDomains": [
    {
      "id": "memory",
      "label": "记忆力",
      "initialQuestion": "最近您是否感觉自己的记忆力与以前相比发生了变化？",
      "mainQuestions": [
        "具体是什么样的变化？",
        "这种变化大约从什么时候开始？",
        "这种变化是否影响过日常安排？",
        "您能举一个具体例子吗？",
        "这种情况是一直存在还是时好时坏？"
      ],
      "followUpQuestions": {
        "A": {"question": "您是否为此担心？", "options": ["否", "是"], "values": [0, 1]},
        "B": {"question": "什么时候开始变差？", "options": ["近6个月", "6个月-2年", "2-5年", "超过5年", "不清楚"], "values": [1, 2, 3, 4, 5]},
        "C": {"question": "是否比同龄人差？", "options": ["否", "是"], "values": [0, 1]},
        "D": {"question": "是否因此看过医生？", "options": ["否", "是"], "values": [0, 1]},
        "E": {"question": "第一次与医生谈是什么时候？", "type": "text"}
      }
    },
    // ... 其余 4 个认知域
  ],
  "informantQuestionnaire": [
    {"id": "inform_1", "question": "您有没有观察到患者记忆力的变化？"},
    // ... 共 6 个问题
  ]
}
```

**预期输出**：5 个认知域的完整问题树 + 6 个知情者问卷

**映射目标**：
```
→ 新建 server/app/services/scd_interview.py: 状态机配置
→ server/app/routers/assisted_tasks.py: 替换 MOCK_REPLIES
```

### 缺口清单

| 缺口 | 来源类型 | 优先级 | 工作量 | 备注 |
|------|----------|--------|--------|------|
| 完整问题树 | PDF 提取 | P0 | 简单 | 网页 AI 可直接提取 |
| 状态机实现 | 手动编码 | P0 | 复杂 | 设计状态转移规则、A-E 子问题触发逻辑 |
| LLM 替换 Mock | 代码开发 | P1 | 复杂 | 接入真实 LLM（DeepSeek）或保留本地规则 |
| 知情者问卷 UI | 前端开发 | P1 | 中等 | 设计知情者问卷收集界面 |

---

## 5. 评分节点配置

### 汇总表

| 任务 | 字段 | 分层维度 | 值范围 | PDF 来源 | 存储位置 |
|------|------|---------|--------|----------|----------|
| Boston | cutoffThresholds | 教育程度 | 中学 19/高中 21/大学 22 | 第 4 页 | `seed.py` scoring_json |
| STT-A | age_thresholds | 年龄 | 50-59:70s/60-69:80s/70-79:100s | 第 5 页 | `seed.py` scoring_json |
| STT-B | age_thresholds | 年龄 | 50-59:180s/60-69:200s/70-79:240s | 第 5 页 | `seed.py` scoring_json |
| MoCA-B | cutoffThresholds | 教育程度 | 文盲/小学 19/中学 22/大学 24 | 第 10 页 | `seed.py` scoring_json |

### 网页 AI 映射任务

#### 任务 5A：评分节点值汇总提取

**输入**：`4.最新量表操作说明修订版.pdf` 第 4、5、10-12 页  
**Prompt**：
```
请从 PDF 相应页码提取所有任务的评分节点值（教育/年龄分层的正常值或异常阈值）。

输出格式（JSON）：
{
  "Boston": {
    "fieldName": "cutoffThresholds",
    "dimension": "education",
    "thresholds": {
      "middle_school": 19,
      "high_school": 21,
      "college": 22
    }
  },
  "STT_A": {...},
  "STT_B": {...},
  "MoCA_B": {...}
}
```

**映射目标**：
```
→ server/app/seed.py: 所有问卷的 scoring_json 配置
```

---

## 执行路径

### 第 0 步：网页 AI 映射提取（并行执行）

使用规划中提供的 6 个 Prompt，通过网页 AI（Claude、GPT-4）上传 PDF 并提取结构化数据：

1. ✅ Task 1A：Boston 题目（输出 30 个题目 JSON）
2. ✅ Task 1B：Boston 评分规则（输出评分配置 JSON）
3. ✅ Task 2A：STT 序列（输出 4 个序列数组）
4. ✅ Task 2B：STT 节点值（输出年龄分层配置）
5. ✅ Task 3A：MoCA-B 任务（输出 10 个任务定义）
6. ✅ Task 4A：SCD 问题树（输出 5 域 + 知情者配置）

**输出**：6 份 JSON 数据，共可直接映射的内容

### 第 1 步：建立映射文档引用

更新以下文件中的相关部分，指向本映射文档：

- `docs/integration/cyf-handoff.md` 第 44-47 行：添加"已完成：创建 C/B 任务映射索引文档"
- `docs/integration/coverage.md`：更新 C/B 任务状态为"P0：获取正式资料中"

### 第 2 步：优先 P0 缺口处理（分阶段）

#### 立即处理（1-2 天内）
- ✅ 网页 AI 提取 6 项数据
- ⚠️ Boston 图片：联系项目方或尝试修复 PDF（可能需外部协调）
- ✅ STT 序列 + 节点值：直接映射到代码

#### 短期处理（1 周内）
- ✅ SCD 状态机：手动编码，设计决策树
- ⚠️ STT 坐标提取：从 PNG 图片手工标注或用脚本提取

#### 中期处理（2-4 周）
- ✅ MoCA-B 其余任务：前端页面开发
- ⚠️ 视觉素材：从 `moca_b_template.png` 提取或设计

### 第 3 步：代码映射更新

#### 前端（`patient-web/c2b/Frontend/src/data/demo-data.ts`）
- Boston：将 3 个占位题更新为 30 个正式题目
- STT：将 6 个占位节点更新为完整序列和坐标
- SCD：将硬编码初始消息更新为状态机配置

#### 后端（`server/app/seed.py`）
- Boston：更新 `scoring_json` 配置
- STT：更新 `scoring_json` 配置
- MoCA-B：新建完整问卷版本配置
- SCD：新增访谈元数据配置

#### 后端逻辑（`server/app/routers/assisted_tasks.py`）
- SCD 对话逻辑：替换 `MOCK_REPLIES`，使用正式状态机

### 第 4 步：验证与测试

对照此映射文档验证：
- ✅ 每个 DEMO 字段都已追溯到 PDF 页码
- ✅ 网页 AI 提取的 JSON 数据已正确映射到代码
- ✅ P0 缺口（图片、坐标）已获取或有明确替代方案
- ✅ 团队成员可根据本文档独立完成后续改动

---

## 附录：PDF 文件位置

### 原始 PDF

```
docs/requirements/ad-ouc-master/ad-ouc-master/
├── 1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf (33 页)
├── 2.量表模板.pdf (31 页，当前损坏，包含 Boston 图片)
├── 3.量表MoCA模板.pdf (1 页)
├── 4.最新量表操作说明修订版.pdf (12 页)
├── 5.CDR.pdf
└── 6.ADAS-cog.pdf
```

### 文本参考

```
docs/references/lfy/docs/sources/
├── 01_SCD基线量表_文本版.md (E 章节：完整问卷)
└── 04_评分手册_文本版.md (完整评分规则)
```

### 图片资源

```
docs/references/lfy/docs/assets/
├── stt_form_a_reference.png (STT-A 参考图)
├── stt_form_b_practice_reference.png (STT-B 练习图)
├── stt_form_b_test_reference.png (STT-B 测试图)
└── moca_b_template.png (MoCA-B 完整模板)
```

---

## 维护记录

| 日期 | 维护者 | 变更 |
|------|--------|------|
| 2026-09-15 | Claude Code | 初稿：建立映射索引框架，标注 6 项网页 AI 映射任务 |
| 2026-09-15 | Codex | 更新 STT 状态：React 来源参考端已接入坐标 JSON、年龄阈值 JSON、A/B 练习与正式任务 |

---

**下一步**：将规划中 6 个 Prompt 输入网页 AI，获取结构化数据，填充本文档的各缺口清单。
