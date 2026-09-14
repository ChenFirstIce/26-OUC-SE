<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../../api/client'
import DynamicQuestion from '../../components/DynamicQuestion.vue'
import { createIdempotencyKey } from '../../utils/idempotency'
import { formatDateTime } from '../../utils/date'

const route = useRoute()
const accessCode = ref('')
const verified = ref(false)
const loading = ref(false)
const packageData = ref<any>()
const current = ref<any>()
const answers = ref<Record<string, any>>({})
const revision = ref(0)
const saveState = ref('已保存')
const busy = ref(false)
const questionIndex = ref(0)
const historyOnly = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined
let hydrating = false
let dirty = false
let saving: Promise<void> | undefined
let submissionKey = ''
const completed = (item: any) => ['submitted', 'reviewed'].includes(item.status)
const visibleQuestions = computed<any[]>(() => current.value?.schema.sections.flatMap((section: any) =>
  section.questions.map((question: any) => ({ ...question, sectionTitle: section.title })))
  .filter((question: any) => !question.show_if || answers.value[question.show_if.question_key] === question.show_if.equals) ?? [])
const activeQuestion = computed(() => visibleQuestions.value[questionIndex.value])
const completedItems = computed<any[]>(() => packageData.value?.items.filter(completed) ?? [])
const listedItems = computed<any[]>(() => historyOnly.value ? completedItems.value : packageData.value?.items ?? [])
const answeredCount = computed(() => visibleQuestions.value.filter(q => hasAnswer(answers.value[q.key])).length)
function hasAnswer(value: any) { return value !== undefined && value !== null && value !== '' && (!Array.isArray(value) || value.length > 0) }
function message(error: unknown) { ElMessage.error(error instanceof Error ? error.message : '操作失败，请重试') }
async function loadTasks() { packageData.value = (await api.get('/patient-session/tasks')).data }
async function verify() {
  loading.value = true
  try {
    const { data } = await api.post('/patient-session/verify', { token: route.params.token, access_code: accessCode.value })
    sessionStorage.setItem('patient_token', data.access_token)
    sessionStorage.setItem('patient_link', String(route.params.token))
    await loadTasks()
    verified.value = true
  } catch (error) { message(error) } finally { loading.value = false }
}
async function openTask(item: any) {
  try {
    const { data } = await api.get(`/patient-session/tasks/${item.id}`)
    hydrating = true
    current.value = data
    answers.value = { ...data.answers }
    revision.value = data.revision
    questionIndex.value = 0
    submissionKey = createIdempotencyKey()
    dirty = false
    saveState.value = '已保存'
    await nextTick()
    hydrating = false
  } catch (error) { message(error) }
}
async function save(): Promise<void> {
  clearTimeout(timer)
  if (saving) await saving
  if (!current.value || completed(current.value) || !dirty) return
  const itemId = current.value.id
  const snapshot = JSON.parse(JSON.stringify(answers.value))
  dirty = false
  saveState.value = '保存中…'
  saving = (async () => {
    try {
      const { data } = await api.put(`/patient-session/tasks/${itemId}/draft`, { answers: snapshot, revision: revision.value })
      revision.value = data.revision
      saveState.value = dirty ? '有未保存修改' : '已自动保存'
    } catch (error) {
      dirty = true
      saveState.value = '保存失败，请重试'
      throw error
    }
  })()
  try { await saving } finally { saving = undefined }
}
watch(answers, () => {
  if (hydrating || !current.value || completed(current.value)) return
  dirty = true
  saveState.value = '有未保存修改'
  clearTimeout(timer)
  timer = setTimeout(() => { save().catch(message) }, 600)
}, { deep: true })
watch(visibleQuestions, questions => { questionIndex.value = Math.min(questionIndex.value, Math.max(0, questions.length - 1)) })
async function submit() {
  const missingIndex = visibleQuestions.value.findIndex(q => q.required && !hasAnswer(answers.value[q.key]))
  if (missingIndex >= 0) { questionIndex.value = missingIndex; ElMessage.warning('请先完成必答题'); return }
  try {
    await ElMessageBox.confirm('提交后不能再修改答案，确认提交吗？', '提交确认', { confirmButtonText: '确认提交', cancelButtonText: '继续检查' })
    busy.value = true
    await save()
    await api.post(`/patient-session/tasks/${current.value.id}/submit`, { answers: answers.value, revision: revision.value }, { headers: { 'Idempotency-Key': submissionKey } })
    current.value = null
    await loadTasks()
    ElMessage.success('问卷提交成功，感谢您的配合')
  } catch (error) { if (error !== 'cancel' && error !== 'close') message(error) } finally { busy.value = false }
}
async function back() {
  busy.value = true
  try { await save(); current.value = null; await loadTasks() } catch (error) { message(error) } finally { busy.value = false }
}
function beforeUnload(event: BeforeUnloadEvent) {
  if (dirty || saving) { event.preventDefault(); event.returnValue = '' }
}
window.addEventListener('beforeunload', beforeUnload)
onBeforeRouteLeave(async () => {
  try { await save(); return true } catch (error) { message(error); return false }
})
watch(() => route.params.token, async token => {
  clearTimeout(timer)
  verified.value = false
  current.value = null
  packageData.value = null
  accessCode.value = token === 'demo-patient-token' ? '123456' : ''
  if (sessionStorage.getItem('patient_link') !== String(token)) {
    sessionStorage.removeItem('patient_token')
    sessionStorage.removeItem('patient_link')
    return
  }
  if (sessionStorage.getItem('patient_token')) {
    try { await loadTasks(); verified.value = true } catch {
      sessionStorage.removeItem('patient_token')
      sessionStorage.removeItem('patient_link')
    }
  }
}, { immediate: true })
onBeforeUnmount(() => { clearTimeout(timer); window.removeEventListener('beforeunload', beforeUnload) })
</script>

<template>
  <div class="patient-page">
    <header class="patient-header"><div class="patient-brand"><span class="brand-mark">认</span><div><b>认知筛查问卷</b><small>移动填写端</small></div></div><span v-if="current" class="save-state" aria-live="polite">{{ saveState }}</span></header>
    <main class="patient-main">
      <section v-if="!verified" class="verify-card">
        <h1>开始填写问卷</h1><p>请输入医生提供的 6 位访问码。链接与访问码共同用于保护您的问卷信息。</p>
        <el-input v-model="accessCode" maxlength="6" inputmode="numeric" size="large" class="code-input" aria-label="6 位访问码" placeholder="6 位访问码" @keyup.enter="verify" />
        <el-button type="primary" size="large" class="full" :loading="loading" :disabled="accessCode.length !== 6" @click="verify">验证并进入</el-button>
        <div class="privacy-note">本系统用于信息收集和筛查，不提供医学诊断。</div>
      </section>
      <section v-else-if="current" class="questionnaire-page">
        <button class="text-back" :disabled="busy" @click="back">← 返回任务列表</button>
        <h1>{{ current.name }}</h1><p class="notice-inline">{{ current.schema.notice }}</p>
        <p aria-live="polite">已回答 {{ answeredCount }} / {{ visibleQuestions.length }} 题</p>
        <form @submit.prevent>
          <fieldset :disabled="busy" class="question-fieldset">
            <template v-if="activeQuestion">
              <p>第 {{ questionIndex + 1 }} 题，共 {{ visibleQuestions.length }} 题</p>
              <h3 class="section-title">{{ activeQuestion.sectionTitle }}</h3>
              <DynamicQuestion :key="activeQuestion.key" :question="activeQuestion" v-model="answers[activeQuestion.key]" />
            </template>
            <div class="patient-actions">
              <el-button size="large" :disabled="questionIndex === 0 || busy" @click="questionIndex--">上一题</el-button>
              <el-button v-if="questionIndex < visibleQuestions.length - 1" type="primary" size="large" :disabled="busy" @click="questionIndex++">下一题</el-button>
              <el-button size="large" :disabled="busy" @click="save().catch(message)">暂存</el-button>
              <el-button v-if="questionIndex === visibleQuestions.length - 1" type="primary" size="large" :loading="busy" @click="submit">提交问卷</el-button>
            </div>
          </fieldset>
        </form>
      </section>
      <section v-else-if="packageData" class="task-home">
        <h1>{{ packageData.assignment.title }}</h1><p>{{ packageData.assignment.note }}</p>
        <div class="task-meta"><span>患者编码 {{ packageData.assignment.patient_code }}</span><span>负责医生 {{ packageData.assignment.doctor_name }}</span></div>
        <div class="progress-summary"><b>{{ completedItems.length }} / {{ packageData.items.length }}</b><span>已完成问卷</span></div>
        <div class="patient-actions"><el-button :type="!historyOnly ? 'primary' : 'default'" @click="historyOnly = false">全部任务</el-button><el-button :type="historyOnly ? 'primary' : 'default'" @click="historyOnly = true">已完成记录</el-button></div>
        <p v-if="historyOnly">仅显示本次授权任务包的已完成记录。</p>
        <p v-if="!listedItems.length">暂无已完成记录。</p>
        <div class="task-list">
          <article v-for="item in listedItems" :key="item.id" class="patient-task" :class="item.status">
            <div><span class="status-dot"></span><div><h3>{{ item.name }}</h3><p>{{ item.description }}</p><p v-if="completed(item)">提交时间 {{ formatDateTime(item.submitted_at) }} · 用时 {{ item.duration_seconds ?? '—' }} 秒</p></div></div>
            <el-button v-if="!completed(item)" type="primary" @click="openTask(item)">{{ item.status === 'draft' ? '继续填写' : '开始填写' }}</el-button><el-tag v-else type="success">已提交</el-tag>
          </article>
        </div>
        <div v-if="packageData.items.length && packageData.items.every(completed)" class="complete-banner">✓ 全部问卷已提交，感谢您的配合。医生将结合其他信息进行专业评估。</div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.question-fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
.patient-actions { flex-wrap: wrap; gap: 8px; }
</style>
