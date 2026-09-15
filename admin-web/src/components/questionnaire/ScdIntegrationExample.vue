<template>
  <div class="integration-example">
    <!-- 示例：在 AssistedTask.vue 中如何集成 SCD 问卷 -->

    <!-- 方式 1: 作为辅助任务类型 -->
    <ScdQuestionnaire
      v-if="task.schema.task_type === 'scd_structured_interview'"
      :task="task"
      @complete="handleScdComplete"
      @back="emit('back')"
    />

    <!-- 方式 2: 独立页面路由 -->
    <!--
    在 router/index.ts 中添加：
    {
      path: '/patient/scd/:taskId',
      name: 'ScdInterview',
      component: () => import('../components/questionnaire/ScdQuestionnaire.vue')
    }
    -->

    <!-- 方式 3: 作为问卷列表项 -->
    <!--
    在 QuestionnairesView.vue 中添加 SCD 问卷类型：
    {
      id: 'scd_structured',
      title: 'SCD 主观认知下降结构性问卷',
      description: 'E 部分：完整结构性访谈问卷',
      category: 'cognitive'
    }
    -->
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ScdQuestionnaire from './ScdQuestionnaire.vue'
import { ElMessage } from 'element-plus'
import { api } from '../../api/client'

const props = defineProps<{ task: any }>()
const emit = defineEmits<{ complete: []; back: [] }>()

async function handleScdComplete() {
  try {
    // 提交到后端
    const response = await api.post(`/assisted-tasks/${props.task.id}/submit`, {
      taskType: 'scd_structured_interview',
      results: {
        // SCD 问卷结果已经在 ScdQuestionnaire 组件内部处理
      }
    })

    ElMessage.success('SCD 问卷已提交')
    emit('complete')
  } catch (error) {
    ElMessage.error('提交失败')
    console.error(error)
  }
}
</script>

<style scoped>
.integration-example {
  /* 集成示例样式 */
}
</style>

<!--
集成步骤清单：

1. 在 AssistedTask.vue 中添加任务类型判断
   - 找到现有的 v-if/v-else-if 链
   - 添加: <ScdQuestionnaire v-else-if="kind === 'scd_structured_interview'" />

2. 在后端添加任务类型支持
   server/app/routers/assisted_tasks.py:
   - 添加 'scd_structured_interview' 到 VALID_TASK_TYPES
   - 实现专门的处理逻辑

3. 在数据库中创建 SCD 任务
   server/app/seed.py:
   - 添加 SCD 问卷的 schema 定义
   - 包含所有认知域和问题结构

4. 医生端结果展示
   admin-web/src/components/ReviewEvidence.vue:
   - 添加 SCD 结果的展示逻辑
   - 格式化显示受访者答案和知情者信息

5. 更新 API 契约
   contracts/API.md:
   - 文档化 SCD 问卷的提交格式
   - 定义返回结果的结构

示例数据结构：

// 任务 Schema
{
  "task_type": "scd_structured_interview",
  "title": "SCD 主观认知下降结构性问卷",
  "instructions": "请根据受访者的实际情况完成问卷",
  "domains": ["memory", "language", "planning", "attention", "other_cognition"]
}

// 提交结果
{
  "selectedDomains": ["memory", "attention"],
  "mainAnswers": {
    "memory": true,
    "attention": true
  },
  "followUpAnswers": {
    "memory": {
      "A": 1,
      "B": 2,
      "C": 1,
      "D": 0,
      "E": "6月前"
    }
  },
  "informant": {
    "available": true,
    "relation": "配偶",
    "answers": {
      "inform_1": true,
      "inform_2": false
    },
    "onsets": {
      "inform_1": 2
    }
  },
  "additionalInformation": {
    "additional_1": "否",
    "additional_2": "否",
    "additional_3": "慢性的",
    "additional_4": "缓慢"
  },
  "completedAt": "2026-09-15T10:30:00Z"
}
-->
