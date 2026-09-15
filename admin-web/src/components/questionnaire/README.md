# SCD 主观认知下降结构性问卷

## 概述

本组件实现了完整的 SCD（Subjective Cognitive Decline，主观认知下降）结构性问卷，用于评估受访者的认知功能主观感受。

## 数据来源

- 源数据文件：`/scd_structured_interview.json`
- 数据模型：`/admin-web/src/data/scd-questionnaire.ts`
- 组件实现：`/admin-web/src/components/questionnaire/ScdQuestionnaire.vue`

## 问卷结构

### 1. 初始筛查阶段（Screening）

受访者从以下认知域中选择自己感觉有问题的方面：

- **记忆力**
- **语言 / 找词困难**
- **组织能力 / 计划能力**
- **注意力 / 专心**
- **其他认知功能方面**

### 2. 认知域问卷阶段（Questioning）

对于每个被选中的认知域，依次询问：

#### 主要问题（必答）
- 例如："你是否觉得你的记性变差了？"
- 选项：是 / 否

#### 追加问题（仅当主要问题回答"是"时显示）

**A. 担忧程度**
- "如果是，你是否会担心？"
- 选项：否(0) / 是(1)

**B. 变化时间**
- "如果是，你觉得什么时候情况变差的？"
- 选项：
  - 近6个月内(1)
  - 近6个月-2年(2)
  - 2-5年(3)
  - 超过5年(4)
  - 不清楚(5)

**C. 同龄比较**
- "如果是：你是否觉得你这方面表现的比同龄人差？"
- 选项：否(0) / 是(1)

**D. 就医情况**
- "如果是：你是否因为这些问题去看过医生？或者你是否同你的医生谈过这个问题（在你来记忆门诊之前）？"
- 选项：否(0) / 是(1)

**E. 首次就医时间**
- "如果是：你第一次跟你的医生谈这些问题是什么时候？"
- 类型：文本输入
- 格式：□□月前 / NA

### 3. 知情者问卷阶段（Informant）

#### 知情者可用性检查
- 是否有知情者可以提供信息？
- 选项：有 / 无知情者 / 受访者不希望知情者提供信息

#### 知情者关系（如有知情者）
- 配偶 / 孩子 / 兄弟姐妹 / 朋友 / 其他

#### 知情者观察问题（6题）
1. 你是否觉得受访者的记性变差了？
2. 受访者是否比以前要找词困难？
3. 受访者是否越来越难做计划、有序安排事情？
4. 如果受访者不专心做一件事情时是否比以前更容易犯错？
5. 受访者在其他认知方面是否变差？是哪些方面？
6. 受访者行为或性格是否有变化？

每题回答"是"时，追问：
- "减退是从什么时候开始的？"
- 选项：近6个月内(1) / 6个月-2年前(2) / 2-5年内(3) / 5年前(4) / 不清楚(5)

### 4. 补充信息阶段（Additional）

1. **是否存在其他已知导致认知障碍的病因？**
   - 选项：是 / 否

2. **认知表现是否存在明显波动？**
   - 选项：是 / 否

3. **认知主诉的出现形式**
   - 选项：突然的 / 不知道 / 慢性的

4. **认知损害的进展特点**
   - 选项：迅速 / 不知道 / 缓慢 / 阶梯式

## 组件使用

### 基本用法

```vue
<template>
  <ScdQuestionnaire
    :task="currentTask"
    @complete="handleComplete"
    @back="handleBack"
  />
</template>

<script setup>
import ScdQuestionnaire from '@/components/questionnaire/ScdQuestionnaire.vue'

function handleComplete() {
  console.log('问卷完成')
}

function handleBack() {
  console.log('返回上一步')
}
</script>
```

### Props

| 属性名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| task | Object | 是 | 任务对象，包含问卷相关信息 |

### Events

| 事件名 | 参数 | 说明 |
|--------|------|------|
| complete | - | 问卷完成时触发 |
| back | - | 返回时触发 |

## 数据结构

### 输出结果格式

```typescript
{
  selectedDomains: string[],              // 选中的认知域 ID
  mainAnswers: Record<string, boolean>,   // 主要问题答案
  followUpAnswers: Record<string, Record<string, any>>, // 追加问题答案
  informant: {
    available: boolean | null,            // 知情者是否可用
    unavailableReason: string,            // 不可用原因
    relation: string,                     // 知情者关系
    answers: Record<string, boolean>,     // 知情者问题答案
    onsets: Record<string, number>        // 各项减退开始时间
  },
  additionalInformation: Record<string, string>, // 补充信息答案
  completedAt: string                     // 完成时间（ISO 8601 格式）
}
```

## 分支逻辑

根据 JSON 数据中的 `branchRule`：
> 主要的问题（1-5）中若受访者回答是，应提问额外的 A-E。

组件实现了以下分支逻辑：
1. 只有当主要问题回答"是"时，才显示该认知域的追加问题 A-E
2. 知情者问题中，只有当某题回答"是"时，才追问减退开始时间
3. 知情者可用性检查通过后，才显示知情者关系和问题列表

## 进度追踪

组件提供实时进度显示：
- 总步骤数 = 1（筛查）+ 选中认知域数量 + 1（知情者）+ 1（补充信息）
- 进度条自动更新，显示当前完成百分比
- 支持前后导航（在认知域问卷阶段）

## 样式特点

遵循项目设计规范：
- 渐变进度条（蓝色到绿色）
- 圆角按钮和卡片设计
- 响应式布局
- 选中状态的视觉反馈
- 层次清晰的问题嵌套显示

## 后续集成

当前组件输出到控制台，需要集成到后端 API：

```typescript
// 在 submitQuestionnaire 函数中
const response = await api.post(`/assisted-tasks/${props.task.id}/submit`, {
  results,
  revision: props.task.revision
})
```

## 注意事项

1. **答案验证**：当前未强制要求所有问题必答，根据实际需求可添加验证逻辑
2. **数据持久化**：问卷进度暂未保存到后端，刷新页面将丢失
3. **打印支持**：如需打印功能，需添加打印样式和导出功能
4. **多语言**：当前仅支持中文，如需多语言可引入 i18n
