<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../../api/client'
import { createIdempotencyKey } from '../../utils/idempotency'

const props = defineProps<{ task: any }>()
const emit = defineEmits<{ complete: []; back: [] }>()
const kind = computed(() => props.task.schema.task_type)
const revision = ref(props.task.revision)
const busy = ref(false)
const startedAt = ref(Date.now() - Number(props.task.answers?.elapsedMs || 0))
const sessionId = `scd-${props.task.id}-${Date.now()}`
const submissionKey = createIdempotencyKey()
const input = ref('')
const openAnswer = ref(props.task.answers?.answer || '')
const messages = ref<any[]>(props.task.answers?.messages || [{ role: 'assistant', content: '最近您是否感觉自己的记忆或思考能力与以前相比发生了变化？' }])
const progress = ref(props.task.answers?.progress || .15)
const boston = [
  { id:'demo_boston_01', emoji:'☂️', title:'这是什么物品？', hint:'下雨时常用的物品' },
  { id:'demo_boston_02', emoji:'🚲', title:'这是什么交通工具？', hint:'通常有两个轮子' },
  { id:'demo_boston_03', emoji:'🍎', title:'这是什么水果？', hint:'一种常见的红色水果' },
]
const legacyNamingItems = (props.task.answers?.items || []).filter((row:any, index:number, rows:any[]) =>
  boston.some(item => item.id === row.questionId) && typeof row.answer === 'string' && row.answer.trim() &&
  rows.findIndex(other => other.questionId === row.questionId && typeof other.answer === 'string') === index,
).slice(0, boston.length - 1)
const namingIndex = ref(legacyNamingItems.length)
const namingItems = ref<any[]>(legacyNamingItems)
const namingAnswer = ref('')
const hintUsed = ref(false)
const questionStartedAt = ref(Date.now())
const trailSequence = ['1','A','2','B','3','C']
const trailNodes = [
  { id:'1', x:12, y:18 }, { id:'A', x:72, y:12 }, { id:'2', x:42, y:38 },
  { id:'B', x:86, y:56 }, { id:'3', x:22, y:78 }, { id:'C', x:68, y:86 },
]
const trailEvents = ref<any[]>(props.task.answers?.events || [])
const trailProgress = ref(props.task.answers?.sequence?.length || 0)
const trailErrors = ref(props.task.answers?.errorCount || 0)
const lastWrongNode = ref('')
const trailLines = computed(() => trailSequence.slice(0, trailProgress.value).map(id => trailNodes.find(node => node.id === id)!).slice(1).map((node,index) => ({ from:trailNodes.find(item => item.id === trailSequence[index])!, to:node })))

async function saveDraft(answers: any) {
  const { data } = await api.put(`/patient-session/tasks/${props.task.id}/draft`, { answers, revision: revision.value })
  revision.value = data.revision
}
async function finish(answers: any) {
  await ElMessageBox.confirm('提交后不能修改，确认完成该任务吗？', '提交确认', { confirmButtonText:'确认提交', cancelButtonText:'继续检查' })
  busy.value = true
  try {
    await api.post(`/patient-session/tasks/${props.task.id}/assisted-submit`, {
      answers, revision: revision.value, metrics: { durationMs: Date.now() - startedAt.value },
    }, { headers: { 'Idempotency-Key': submissionKey } })
    ElMessage.success('任务已提交，将由专业人员复核')
    emit('complete')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') ElMessage.error(error instanceof Error ? error.message : '提交失败')
  } finally { busy.value = false }
}
async function sendInterview() {
  const value = input.value.trim(); if (!value || busy.value) return
  busy.value = true
  try {
    messages.value.push({ role:'user', content:value }); input.value = ''
    const { data } = await api.post(`/patient-session/tasks/${props.task.id}/llm/sessions/${sessionId}/messages`, { message:value })
    messages.value.push({ role:'assistant', content:data.reply }); progress.value = data.progress
    await saveDraft({ messages:messages.value, progress:progress.value })
    if (data.completed) await finish({ messages:messages.value, progress:progress.value })
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '发送失败') }
  finally { busy.value = false }
}
async function submitOpen() {
  if (!openAnswer.value.trim()) return
  await saveDraft({ questionId:'demo-open-01', answer:openAnswer.value.trim() })
  await finish({ questionId:'demo-open-01', answer:openAnswer.value.trim() })
}
async function submitNaming() {
  if (!namingAnswer.value.trim()) return
  const currentQuestion = boston[namingIndex.value]
  if (!currentQuestion) return
  const nextItems = [...namingItems.value, {
    questionId:currentQuestion.id, answer:namingAnswer.value.trim(),
    hintUsed:hintUsed.value, durationMs:Date.now()-questionStartedAt.value,
  }]
  if (namingIndex.value === boston.length - 1) {
    try { await finish({ items:nextItems }) } catch (error) {
      if (error !== 'cancel' && error !== 'close') throw error
    }
    return
  }
  await saveDraft({ items:nextItems })
  namingItems.value = nextItems
  namingIndex.value++
  namingAnswer.value=''
  hintUsed.value=false
  questionStartedAt.value=Date.now()
}
async function clickTrail(nodeId:string) {
  if (busy.value || trailProgress.value >= trailSequence.length) return
  busy.value = true
  const node = trailNodes.find(item => item.id === nodeId)!
  const expectedNode = trailSequence[trailProgress.value]
  const correct = nodeId === trailSequence[trailProgress.value]
  const elapsedMs = Date.now()-startedAt.value
  trailEvents.value.push({ nodeId, timestampMs:elapsedMs, correct, expectedNode, x:node.x, y:node.y })
  if (correct) { trailProgress.value++; lastWrongNode.value = '' } else { trailErrors.value++; lastWrongNode.value = nodeId }
  const answers = { events:trailEvents.value, sequence:trailSequence.slice(0,trailProgress.value), errorCount:trailErrors.value, elapsedMs }
  try {
    await saveDraft(answers)
    busy.value = false
    if (trailProgress.value === trailSequence.length) await finish(answers)
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : '保存失败') }
  finally { busy.value = false }
}
</script>

<template>
  <div class="assisted-task">
    <button class="text-back" :disabled="busy" @click="emit('back')">← 返回任务列表</button>
    <span class="task-badge">{{ kind === 'boston_naming' || kind === 'trail_making' ? 'B 类 · 程序辅助' : 'C 类 · AI 辅助' }}</span>
    <h1>{{ task.name }}</h1><p class="notice-inline">{{ task.schema.notice }}</p>

    <section v-if="kind === 'scd_interview'" class="cb-card">
      <div class="cb-progress"><i :style="{width:`${progress*100}%`}"></i></div>
      <div class="chat-list"><div v-for="(message,index) in messages" :key="index" :class="['chat-message',message.role]">{{ message.content }}</div></div>
      <el-input v-model="input" type="textarea" :rows="3" placeholder="请按实际感受回答" :disabled="busy" />
      <el-button type="primary" size="large" class="full" :loading="busy" :disabled="!input.trim()" @click="sendInterview">发送回答</el-button>
    </section>

    <section v-else-if="kind === 'moca_open_answer'" class="cb-card">
      <h2>请用一句话说明“火车”和“自行车”有什么共同之处。</h2>
      <p>没有唯一表达方式，请使用自然语言回答。</p>
      <el-input v-model="openAnswer" type="textarea" :rows="6" maxlength="500" show-word-limit />
      <el-button type="primary" size="large" class="full" :loading="busy" :disabled="!openAnswer.trim()" @click="submitOpen">确认提交</el-button>
    </section>

    <section v-else-if="kind === 'boston_naming'" class="cb-card naming-card">
      <p>第 {{ namingIndex + 1 }} 题，共 {{ boston.length }} 题</p><h2>{{ boston[namingIndex].title }}</h2>
      <div class="demo-object" aria-label="演示图片">{{ boston[namingIndex].emoji }}</div>
      <el-input v-model="namingAnswer" placeholder="请输入图片中的物品名称" @keyup.enter="submitNaming" />
      <p v-if="hintUsed" class="hint">提示：{{ boston[namingIndex].hint }}</p>
      <el-button v-else @click="hintUsed=true">使用提示</el-button>
      <el-button type="primary" size="large" :loading="busy" :disabled="!namingAnswer.trim()" @click="submitNaming">{{ namingIndex === boston.length-1 ? '完成任务' : '确认并继续' }}</el-button>
    </section>

    <section v-else-if="kind === 'trail_making'" class="cb-card">
      <h2>请依次点击 1 → A → 2 → B → 3 → C</h2>
      <p>下一目标：<b>{{ trailSequence[trailProgress] || '已完成' }}</b>　错误次数：{{ trailErrors }}</p>
      <div class="trail-board" aria-label="形状连线任务画布">
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><line v-for="(line,index) in trailLines" :key="index" :x1="line.from.x" :y1="line.from.y" :x2="line.to.x" :y2="line.to.y"/></svg>
        <button v-for="node in trailNodes" :key="node.id" :style="{left:`${node.x}%`,top:`${node.y}%`}" :class="{done:trailSequence.slice(0,trailProgress).includes(node.id),wrong:lastWrongNode===node.id}" :disabled="busy || trailSequence.slice(0,trailProgress).includes(node.id)" @click="clickTrail(node.id)">{{ node.id }}</button>
      </div>
      <div class="trail-legend"><span><i class="done"></i>已完成路径</span><span><i class="wrong"></i>最近一次错误</span><span>进度 {{trailProgress}} / {{trailSequence.length}}</span></div>
    </section>
  </div>
</template>

<style scoped>
.task-badge{display:inline-block;padding:6px 10px;color:#246b5b;background:#e2f0ea;border-radius:999px;font-size:12px;font-weight:700}.cb-card{display:flex;flex-direction:column;gap:16px;margin-top:20px;padding:22px;background:#fff;border:1px solid var(--line);border-radius:16px}.cb-card h2{margin:0;line-height:1.5}.cb-card>p{margin:0;color:var(--muted)}.cb-progress{height:8px;overflow:hidden;background:#e3e8e4;border-radius:9px}.cb-progress i{display:block;height:100%;background:var(--green);transition:width .25s}.chat-list{display:flex;flex-direction:column;gap:10px;max-height:360px;overflow:auto}.chat-message{max-width:86%;padding:12px 14px;border-radius:13px;line-height:1.65}.chat-message.assistant{background:#edf2ef}.chat-message.user{align-self:flex-end;color:#fff;background:var(--green)}.demo-object{display:grid;place-items:center;height:230px;font-size:100px;background:#edf7f2;border-radius:14px}.hint{padding:11px;color:#795b2c!important;background:#fff6e8;border-radius:8px}.attempt-list{display:grid;gap:7px}.attempt-list span{display:flex;justify-content:space-between;padding:9px 11px;background:#f2f6f4;border-radius:8px}.attempt-list small{color:var(--muted)}.naming-actions{display:flex;justify-content:flex-end;gap:9px;flex-wrap:wrap}.trail-board{position:relative;height:420px;overflow:hidden;background:linear-gradient(145deg,#f4f8f6,#e8f1ed);border:1px solid #d8e5df;border-radius:14px}.trail-board svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.trail-board line{stroke:#2f7b66;stroke-width:1.1;stroke-linecap:round;vector-effect:non-scaling-stroke}.trail-board button{position:absolute;display:grid;place-items:center;width:58px;height:58px;transform:translate(-50%,-50%);border:2px solid #8ca99e;border-radius:50%;color:var(--deep);background:#fff;font-size:22px;font-weight:700;box-shadow:0 5px 14px #183d3020;cursor:pointer;transition:.2s}.trail-board button.done{color:#fff;background:var(--green);border-color:var(--green)}.trail-board button.wrong{color:#fff;background:#c85d5d;border-color:#c85d5d;animation:wrong-pulse .45s}.trail-legend{display:flex;flex-wrap:wrap;gap:14px;color:var(--muted);font-size:12px}.trail-legend span{display:flex;align-items:center;gap:5px}.trail-legend i{width:9px;height:9px;background:#2f7b66;border-radius:50%}.trail-legend i.wrong{background:#c85d5d}@keyframes wrong-pulse{50%{transform:translate(-50%,-50%) scale(1.15)}}@media(max-width:600px){.trail-board{height:340px}.trail-board button{width:50px;height:50px}.naming-actions{align-items:stretch;flex-direction:column}}
</style>
