<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import ReviewEvidence from '../components/ReviewEvidence.vue'
import { useAuthStore } from '../stores/auth'
import { patientLabel } from '../utils/patient'
import { formatDateTime } from '../utils/date'

const auth = useAuthStore()
const route = useRoute()
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
const reviewForm = ref<any>({ total_score:null, dimensions:[], risk_level:'unknown', note:'' })
const reviewSaving = ref(false)
const canReview = computed(() => auth.user?.role === 'admin' || auth.user?.permissions?.can_review_results)
const scoreRule = computed(() => result.value?.review_config?.score || { required:true, min:0, max:null })
const dimensionRules = computed<any[]>(() => result.value?.review_config?.dimensions || [])
const riskLevelText:any = { low:'低风险', medium:'中风险', high:'高风险' }
const allowedRiskLevels = computed(() => result.value?.review_config?.risk?.levels || ['low','medium','high'])
const suggestedRisk = computed(() => {
  const score = reviewForm.value.total_score
  if (score == null) return null
  let suggestion = null
  for (const threshold of result.value?.review_config?.risk?.thresholds || []) {
    if (score >= threshold.min && (threshold.max == null || score <= threshold.max)) suggestion = threshold.level
  }
  return suggestion
})
let deepLinkOpened = false
const labels: any = { pending:'未打开', in_progress:'填写中', submitted:'已提交', reviewed:'已复核', expired:'已过期', revoked:'已撤销', not_started:'未开始', draft:'填写中' }
const tags: any = { pending:'info', in_progress:'warning', submitted:'success', reviewed:'success', expired:'danger', revoked:'info' }
const riskLabels: any = { low:'低风险', medium:'中风险', high:'高风险', unknown:'待复核' }

async function load() {
  loading.value = true
  try {
    items.value = (await api.get('/assignments')).data
    if (!deepLinkOpened && route.query.assignment && route.query.item) {
      deepLinkOpened = true
      const assignment = items.value.find((row:any) => row.id === Number(route.query.assignment))
      if (assignment) await openResult(assignment, Number(route.query.item))
    }
  }
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
  try {
    result.value = (await api.get(`/assignments/${assignment.id}/items/${itemId || completed[0].id}/result`)).data
    const assessment = result.value.assessment
    const savedDimensions = Object.entries(assessment.dimension_scores || {}).map(([name, score]) => ({ name, score }))
    reviewForm.value = {
      total_score: assessment.total_score,
      dimensions: savedDimensions.length ? savedDimensions : (result.value.review_config?.dimensions || []).map((row:any) => ({ name:row.key, score:0 })),
      risk_level: assessment.risk_level || 'unknown', note: assessment.review_note || '',
    }
  }
  catch (error) { ElMessage.error((error as Error).message) }
  finally { resultLoading.value = false }
}

function reviewPayload(action: 'save' | 'confirm') {
  const dimension_scores = Object.fromEntries(reviewForm.value.dimensions.filter((row:any) => row.name.trim()).map((row:any) => [row.name.trim(), Number(row.score)]))
  return { action, candidate_result:result.value?.assessment.candidate_result || {}, total_score:reviewForm.value.total_score,
    dimension_scores, risk_level:reviewForm.value.risk_level, note:reviewForm.value.note }
}

function addDimension() { reviewForm.value.dimensions.push({ name:'', score:0 }) }
function removeDimension(index:number) { reviewForm.value.dimensions.splice(index, 1) }
function dimensionRule(name:string) { return dimensionRules.value.find((row:any) => row.key === name) || { min:0, max:null } }
function availableDimensions(index:number) {
  const selected = new Set(reviewForm.value.dimensions.map((row:any, rowIndex:number) => rowIndex === index ? '' : row.name))
  return dimensionRules.value.filter((row:any) => !selected.has(row.key))
}

const fieldLabels:any = { questionId:'题目标识', answer:'患者回答', durationMs:'任务用时', elapsedMs:'单题用时',
  promptUsed:'使用提示', errorCount:'错误次数', completed:'是否完成', sequence:'完成顺序', messages:'访谈记录', items:'逐项回答',
  total_score:'最终总分', dimension_scores:'维度得分', risk_level:'风险等级', note:'复核意见', provisional_total:'程序暂定分' }
function readableValue(value:any, key?:string):string {
  if (value == null || value === '') return '未填写'
  if (key?.toLowerCase().endsWith('ms') && typeof value === 'number') return `${(value / 1000).toFixed(1)} 秒`
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (Array.isArray(value)) return value.map((item, index) => typeof item === 'object' ? `第 ${index + 1} 项：${readableValue(item)}` : String(item)).join('\n')
  if (typeof value === 'object') return Object.entries(value).map(([name, item]) => `${fieldLabels[name] || name}：${readableValue(item, name)}`).join('；')
  return String(value)
}
function readableRows(data:any) {
  return Object.entries(data || {}).map(([key, value]) => ({ label:fieldLabels[key] || (key === '_metrics' ? '过程指标' : key), value:readableValue(value, key) }))
}

async function submitReview(action: 'save' | 'confirm') {
  if (!result.value) return
  try {
    const payload = reviewPayload(action)
    if (action === 'confirm') {
      if (scoreRule.value.required && payload.total_score == null) throw new Error('请填写最终总分')
      if (payload.total_score != null && payload.total_score < scoreRule.value.min) throw new Error(`最终总分不能低于 ${scoreRule.value.min}`)
      if (scoreRule.value.max != null && payload.total_score > scoreRule.value.max) throw new Error(`最终总分不能超过 ${scoreRule.value.max}`)
      for (const row of reviewForm.value.dimensions) {
        if (!row.name) continue
        const rule = dimensionRule(row.name)
        if (row.score == null || row.score < (rule.min ?? 0) || (rule.max != null && row.score > rule.max)) {
          throw new Error(`${rule.label || row.name}得分应在 ${rule.min ?? 0}${rule.max == null ? ' 分以上' : `–${rule.max} 分`}`)
        }
      }
      if (payload.risk_level === 'unknown') throw new Error('请选择最终风险等级')
      if (payload.note.trim().length < 2) throw new Error('请填写复核意见')
    }
    if (action === 'confirm') await ElMessageBox.confirm('确认后将形成最终结果；如需重新作答，应使用“退回重做”。是否继续？', '确认最终结果', { type:'warning' })
    reviewSaving.value = true
    await api.patch(`/assignments/${result.value.assignment_id}/items/${result.value.item_id}/review`, payload)
    ElMessage.success(action === 'confirm' ? '最终结果已确认' : '候选结果与复核意见已保存')
    await load()
    const assignment = items.value.find((row:any) => row.id === result.value.assignment_id) || selectedAssignment.value
    await openResult(assignment, result.value.item_id)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error((error as Error).message)
  } finally { reviewSaving.value = false }
}

async function reopenResult() {
  if (!result.value) return
  try {
    const { value } = await ElMessageBox.prompt('请填写退回原因。原提交与复核快照会保留在历史记录中。', '退回患者重做', {
      confirmButtonText:'确认退回', cancelButtonText:'取消', inputValidator:(text:string) => text.trim().length >= 2 || '至少填写 2 个字',
    })
    await api.post(`/assignments/${result.value.assignment_id}/items/${result.value.item_id}/reopen`, { reason:value.trim() })
    ElMessage.success('任务已退回，患者可以继续作答')
    resultDialog.value = false
    await load()
  } catch (error) { if (error !== 'cancel') ElMessage.error((error as Error).message) }
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
  if (seconds <= 0) return '历史记录未计时'
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
}

function reviewActionText(action: string) {
  return ({ save:'保存候选', confirm:'确认结果', reopen:'退回重做' } as any)[action] || action
}
function reviewStatusText(status:string) {
  return ({ pending:'待医生复核', reviewed:'已由医生确认', auto:'自动计分' } as any)[status] || status
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
        <el-table-column label="截止时间" min-width="155"><template #default="s">{{s.row.deadline ? formatDateTime(s.row.deadline) : '不限时'}}</template></el-table-column>
        <el-table-column label="操作" width="225" fixed="right"><template #default="s"><el-button v-if="completedItems(s.row).length" link type="primary" @click="openResult(s.row)">查看结果</el-button><el-button v-if="canEdit(s.row)" link type="primary" @click="openEdit(s.row)">修改/转交</el-button><el-button v-if="canEdit(s.row)" link type="danger" @click="revoke(s.row)">撤销</el-button></template></el-table-column>
      </el-table>
    </article>

    <el-dialog v-model="resultDialog" title="患者填写结果" width="min(820px,94vw)" destroy-on-close>
      <div v-loading="resultLoading" class="result-dialog">
        <div v-if="selectedAssignment && completedItems(selectedAssignment).length > 1" class="result-tabs"><el-button v-for="item in completedItems(selectedAssignment)" :key="item.id" :type="result?.item_id === item.id ? 'primary' : 'default'" @click="openResult(selectedAssignment,item.id)">{{item.questionnaire_name}}</el-button></div>
        <template v-if="result">
          <div class="result-title"><div><span class="eyebrow">{{result.questionnaire_code}} · V{{result.questionnaire_version}}</span><h2>{{result.questionnaire_name}}</h2><p>患者 {{patientLabel(result)}} · {{formatDateTime(result.submitted_at)}} 提交</p></div><el-tag size="large" :type="result.assessment.risk_level === 'high' ? 'danger' : result.assessment.risk_level === 'medium' ? 'warning' : 'success'">{{riskLabels[result.assessment.risk_level]}}</el-tag></div>
          <div class="result-summary"><div><small>总分</small><strong>{{result.assessment.total_score ?? '待复核'}}</strong></div><div><small>填写用时</small><strong>{{durationText(result.duration_seconds)}}</strong></div><div><small>复核状态</small><strong>{{reviewStatusText(result.assessment.review_status)}}</strong></div></div>
          <div v-if="Object.keys(result.assessment.dimension_scores || {}).length" class="dimension-row"><b>维度得分</b><el-tag v-for="(score,name) in result.assessment.dimension_scores" :key="name">{{name}}：{{score}}</el-tag></div>
          <h3 class="answer-heading">逐题答案</h3>
          <div class="answer-list"><div v-for="(answer,index) in result.answers" :key="answer.question_key" class="answer-row"><span class="answer-index">{{index + 1}}</span><div><b>{{answer.label}}</b><p>{{answer.display_value}}</p></div></div></div>
          <template v-if="result.raw_answers">
            <ReviewEvidence :code="result.questionnaire_code" :answers="result.raw_answers" :auto-result="result.assessment.auto_result"/>
            <div v-if="Object.keys(result.assessment.candidate_result || {}).length" class="dimension-row"><b>AI 候选状态</b><span>已生成候选结果，等待医生复核；不会自动写入最终评分。</span></div>
          </template>
          <section v-if="canReview && ['pending','reviewed'].includes(result.assessment.review_status)" class="review-panel">
            <div class="panel-head"><div><span class="eyebrow">CLINICIAN REVIEW</span><h3>医生复核</h3></div><el-tag :type="result.assessment.review_status === 'reviewed' ? 'success' : 'warning'">{{result.assessment.review_status === 'reviewed' ? '已确认' : '待复核'}}</el-tag></div>
            <template v-if="result.assessment.review_status !== 'reviewed'">
              <el-form label-position="top">
                <div v-if="Object.keys(result.assessment.candidate_result || {}).length" class="candidate-summary"><b>系统候选状态</b><span>候选分析已经生成，请结合原始数据填写最终结果。</span></div>
                <div class="review-grid"><el-form-item :label="`最终总分${scoreRule.max != null ? `（${scoreRule.min}–${scoreRule.max}）` : `（≥${scoreRule.min}）`}`"><el-input-number v-model="reviewForm.total_score" :min="scoreRule.min" :max="scoreRule.max ?? undefined" :controls="false" class="full"/></el-form-item><el-form-item label="风险等级"><el-select v-model="reviewForm.risk_level" class="full"><el-option label="待判断" value="unknown"/><el-option v-for="level in allowedRiskLevels" :key="level" :label="riskLevelText[level]" :value="level"/></el-select><small v-if="suggestedRisk" class="form-help">配置建议：{{riskLevelText[suggestedRisk]}} <el-button link type="primary" @click="reviewForm.risk_level=suggestedRisk">采用建议</el-button></small><small v-else class="form-help">当前版本未配置自动风险建议，请由医生综合判断。</small></el-form-item></div>
                <el-form-item v-if="dimensionRules.length" label="维度得分（可选）"><div class="dimension-editor"><div v-for="(dimension,index) in reviewForm.dimensions" :key="index"><el-select v-model="dimension.name" placeholder="选择维度" class="full"><el-option v-for="rule in availableDimensions(index)" :key="rule.key" :label="rule.label || rule.key" :value="rule.key"/></el-select><div><el-input-number v-model="dimension.score" :min="dimensionRule(dimension.name).min ?? 0" :max="dimensionRule(dimension.name).max ?? undefined" :disabled="!dimension.name" :controls="false" placeholder="分数" class="full"/><small v-if="dimension.name" class="dimension-range">范围：{{dimensionRule(dimension.name).min ?? 0}}{{dimensionRule(dimension.name).max == null ? ' 分以上' : `–${dimensionRule(dimension.name).max} 分`}}</small></div><el-button link type="danger" @click="removeDimension(index)">删除</el-button></div><el-button v-if="reviewForm.dimensions.length < dimensionRules.length" link type="primary" @click="addDimension">+ 添加维度</el-button></div></el-form-item>
                <el-form-item label="复核意见"><el-input v-model="reviewForm.note" type="textarea" :rows="3" maxlength="2000" show-word-limit/></el-form-item>
              </el-form>
              <div class="review-actions"><el-button type="danger" plain @click="reopenResult">退回重做</el-button><span></span><el-button :loading="reviewSaving" @click="submitReview('save')">保存候选</el-button><el-button type="primary" :loading="reviewSaving" @click="submitReview('confirm')">确认最终结果</el-button></div>
            </template>
            <div v-else class="confirmed-result"><p><b>复核人：</b>{{result.assessment.reviewed_by_name || '—'}}　<b>复核时间：</b>{{formatDateTime(result.assessment.reviewed_at)}}</p><p><b>复核意见：</b>{{result.assessment.review_note || '无'}}</p><div class="readable-data"><div v-for="row in readableRows(result.assessment.final_result)" :key="row.label"><b>{{row.label}}</b><span>{{row.value}}</span></div></div><el-button type="danger" plain @click="reopenResult">退回重做</el-button></div>
          </section>
          <section v-if="result.review_history?.length" class="review-history"><h3>复核历史</h3><div v-for="event in result.review_history" :key="event.id"><b>{{reviewActionText(event.action)}}</b><span>{{event.reviewer_name || '未知人员'}} · {{formatDateTime(event.created_at)}}</span><p>{{event.note || '无备注'}}</p></div></section>
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

<style scoped>.readable-data{display:grid;gap:8px;padding:14px;margin-bottom:10px;color:#29453d;background:#f3f6f4;border-radius:10px;font-size:12px}.readable-data>div{display:grid;grid-template-columns:110px 1fr;gap:12px}.readable-data span{white-space:pre-wrap;line-height:1.7}.review-panel,.review-history{padding:18px;margin-top:18px;border:1px solid #dce7f3;border-radius:12px}.review-panel h3,.review-history h3{margin:5px 0}.candidate-summary{display:flex;gap:14px;padding:12px;margin-bottom:16px;color:#66563e;background:#faf4e8;border-radius:8px;font-size:12px}.boston-review{display:grid;gap:8px;margin-bottom:16px}.boston-review>div{display:grid;grid-template-columns:1fr 190px;gap:12px;align-items:center;padding:10px 12px;background:#f5f8f6;border-radius:8px}.boston-review span,.boston-review small{display:block}.boston-review small{margin-top:4px;color:#718299}.review-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.dimension-editor{display:grid;width:100%;gap:8px}.dimension-editor>div{display:grid;grid-template-columns:1fr 150px 50px;gap:8px}.dimension-range{display:block;margin-top:4px;color:#718299}.review-actions{display:flex;align-items:center;gap:10px}.review-actions span{flex:1}.confirmed-result p{color:#53677f;font-size:12px;line-height:1.7}.confirmed-result pre{padding:12px;background:#f5f8fb;border-radius:8px;white-space:pre-wrap}.review-history>div{display:grid;grid-template-columns:100px 1fr;gap:6px 12px;padding:12px 0;border-top:1px solid #edf1f6}.review-history span{color:#718299;font-size:11px}.review-history p{grid-column:1/-1;margin:0;color:#53677f;font-size:12px}@media(max-width:600px){.review-grid{grid-template-columns:1fr}.review-actions{align-items:stretch;flex-direction:column}.review-actions span{display:none}.readable-data>div,.dimension-editor>div,.boston-review>div{grid-template-columns:1fr}}</style>
