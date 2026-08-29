<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import { patientLabel } from '../utils/patient'

const auth = useAuthStore()
const items = ref<any[]>([])
const loading = ref(true)
const resultLoading = ref(false)
const resultDialog = ref(false)
const selectedAssignment = ref<any>()
const result = ref<any>()
const editDialog = ref(false)
const editing = ref<any>()
const doctors = ref<any[]>([])
const editForm = ref<any>({})
const labels: any = { pending:'未打开', in_progress:'填写中', submitted:'已提交', reviewed:'已复核', expired:'已过期', revoked:'已撤销', not_started:'未开始', draft:'填写中' }
const tags: any = { pending:'info', in_progress:'warning', submitted:'success', reviewed:'success', expired:'danger', revoked:'info' }
const riskLabels: any = { low:'低风险', medium:'中风险', high:'高风险', unknown:'待复核' }

async function load() {
  loading.value = true
  try { items.value = (await api.get('/assignments')).data }
  finally { loading.value = false }
}

function completedItems(assignment: any) {
  return assignment.items.filter((item: any) => ['submitted', 'reviewed'].includes(item.status))
}

function canEdit(assignment: any) {
  return !['submitted', 'reviewed', 'revoked'].includes(assignment.status)
}

async function openResult(assignment: any, itemId?: number) {
  const completed = completedItems(assignment)
  if (!completed.length) return
  selectedAssignment.value = assignment
  resultDialog.value = true
  resultLoading.value = true
  result.value = undefined
  try { result.value = (await api.get(`/assignments/${assignment.id}/items/${itemId || completed[0].id}/result`)).data }
  catch (error) { ElMessage.error((error as Error).message) }
  finally { resultLoading.value = false }
}

async function openEdit(row: any) {
  editing.value = row
  editForm.value = { title:row.title, note:row.note, deadline:row.deadline, doctor_id:row.doctor_id }
  if (auth.user?.role === 'admin' && !doctors.value.length) {
    doctors.value = (await api.get('/admin/users')).data.filter((item: any) => item.role === 'doctor' && item.active)
  }
  editDialog.value = true
}

async function saveEdit() {
  try {
    await api.patch(`/assignments/${editing.value.id}`, editForm.value)
    ElMessage.success('派发任务已更新')
    editDialog.value = false
    load()
  } catch (error) { ElMessage.error((error as Error).message) }
}

async function revoke(row: any) {
  try {
    await api.post(`/assignments/${row.id}/revoke`)
    ElMessage.success('任务已撤销')
    load()
  } catch (error) { ElMessage.error((error as Error).message) }
}

function durationText(seconds: number | null) {
  if (seconds == null) return '—'
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-heading">
      <div><span class="eyebrow">ASSIGNMENT OPERATIONS</span><h1>任务与派发</h1><p>跟踪移动端填写进度，查看原始答案，并管理未完成任务。</p></div>
      <div class="heading-actions"><el-button @click="load">刷新</el-button><router-link to="/assignments/create"><el-button type="primary">+ 新建派发</el-button></router-link></div>
    </div>
    <article class="panel table-panel">
      <el-table :data="items" v-loading="loading">
        <el-table-column prop="title" label="任务" min-width="180"><template #default="s"><b>{{s.row.title}}</b><small class="table-sub">{{s.row.doctor_name}}</small></template></el-table-column>
        <el-table-column label="患者" min-width="150"><template #default="s"><b>{{s.row.patient_name || '姓名待补充'}}</b><small class="table-sub">{{s.row.patient_code}}</small></template></el-table-column>
        <el-table-column label="问卷与进度" min-width="240"><template #default="s"><div class="item-status-list"><span v-for="item in s.row.items" :key="item.id"><b>{{item.questionnaire_name}}</b><small>{{labels[item.status] || item.status}}</small></span></div></template></el-table-column>
        <el-table-column label="状态" width="100"><template #default="s"><el-tag :type="tags[s.row.status]">{{labels[s.row.status]}}</el-tag></template></el-table-column>
        <el-table-column label="截止时间" min-width="155"><template #default="s">{{s.row.deadline ? new Date(s.row.deadline).toLocaleString() : '不限时'}}</template></el-table-column>
        <el-table-column label="操作" width="225" fixed="right"><template #default="s"><el-button v-if="completedItems(s.row).length" link type="primary" @click="openResult(s.row)">查看结果</el-button><el-button v-if="canEdit(s.row)" link type="primary" @click="openEdit(s.row)">修改/转交</el-button><el-button v-if="canEdit(s.row)" link type="danger" @click="revoke(s.row)">撤销</el-button></template></el-table-column>
      </el-table>
    </article>

    <el-dialog v-model="resultDialog" title="患者填写结果" width="min(820px,94vw)" destroy-on-close>
      <div v-loading="resultLoading" class="result-dialog">
        <div v-if="selectedAssignment && completedItems(selectedAssignment).length > 1" class="result-tabs"><el-button v-for="item in completedItems(selectedAssignment)" :key="item.id" :type="result?.item_id === item.id ? 'primary' : 'default'" @click="openResult(selectedAssignment,item.id)">{{item.questionnaire_name}}</el-button></div>
        <template v-if="result">
          <div class="result-title"><div><span class="eyebrow">{{result.questionnaire_code}} · V{{result.questionnaire_version}}</span><h2>{{result.questionnaire_name}}</h2><p>患者 {{patientLabel(result)}} · {{new Date(result.submitted_at).toLocaleString()}} 提交</p></div><el-tag size="large" :type="result.assessment.risk_level === 'high' ? 'danger' : result.assessment.risk_level === 'medium' ? 'warning' : 'success'">{{riskLabels[result.assessment.risk_level]}}</el-tag></div>
          <div class="result-summary"><div><small>总分</small><strong>{{result.assessment.total_score ?? '待复核'}}</strong></div><div><small>填写用时</small><strong>{{durationText(result.duration_seconds)}}</strong></div><div><small>复核状态</small><strong>{{result.assessment.review_status === 'pending' ? '待医生复核' : '自动计分'}}</strong></div></div>
          <div v-if="Object.keys(result.assessment.dimension_scores || {}).length" class="dimension-row"><b>维度得分</b><el-tag v-for="(score,name) in result.assessment.dimension_scores" :key="name">{{name}}：{{score}}</el-tag></div>
          <h3 class="answer-heading">逐题答案</h3>
          <div class="answer-list"><div v-for="(answer,index) in result.answers" :key="answer.question_key" class="answer-row"><span class="answer-index">{{index + 1}}</span><div><b>{{answer.label}}</b><p>{{answer.display_value}}</p></div></div></div>
          <div class="notice-card"><b>结果说明</b><p>问卷筛查结果不等同于医学诊断，需由医生结合临床资料综合判断。</p></div>
        </template>
      </div>
    </el-dialog>

    <el-dialog v-model="editDialog" title="修改派发任务" width="560px">
      <el-form label-position="top">
        <el-form-item label="任务名称"><el-input v-model="editForm.title"/></el-form-item>
        <el-form-item label="医生说明"><el-input v-model="editForm.note" type="textarea" :rows="3"/></el-form-item>
        <el-form-item label="截止时间"><el-date-picker v-model="editForm.deadline" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ" clearable class="full"/></el-form-item>
        <el-form-item v-if="auth.user?.role === 'admin'" label="转交负责医生"><el-select v-model="editForm.doctor_id" class="full"><el-option v-for="doctor in doctors" :key="doctor.id" :label="`${doctor.display_name} · ${doctor.department_name || '未分科'}`" :value="doctor.id"/></el-select><small class="form-help">管理员可将未完成任务转交给其他在岗医生。</small></el-form-item>
      </el-form>
      <template #footer><el-button @click="editDialog=false">取消</el-button><el-button type="primary" @click="saveEdit">保存修改</el-button></template>
    </el-dialog>
  </div>
</template>
