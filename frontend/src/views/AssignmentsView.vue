<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const items = ref<any[]>([])
const loading = ref(true)
const resultLoading = ref(false)
const resultDialog = ref(false)
const selectedAssignment = ref<any>()
const result = ref<any>()
const labels: Record<string, string> = { pending:'未打开', in_progress:'填写中', submitted:'已提交', reviewed:'已复核', expired:'已过期', revoked:'已撤销', not_started:'未开始', draft:'填写中' }
const tags: Record<string, string> = { pending:'info', in_progress:'warning', submitted:'success', reviewed:'success', expired:'danger', revoked:'info' }
const riskLabels: Record<string, string> = { low:'低风险', medium:'中风险', high:'高风险', unknown:'待复核' }

async function load() { loading.value=true; try { items.value=(await api.get('/assignments')).data } finally { loading.value=false } }
function completedItems(assignment:any) { return assignment.items.filter((item:any)=>['submitted','reviewed'].includes(item.status)) }
async function openResult(assignment:any,itemId?:number) {
  const completed=completedItems(assignment); if(!completed.length)return
  selectedAssignment.value=assignment;resultDialog.value=true;resultLoading.value=true;result.value=undefined
  try { result.value=(await api.get(`/assignments/${assignment.id}/items/${itemId||completed[0].id}/result`)).data }
  catch(error){ElMessage.error((error as Error).message)} finally{resultLoading.value=false}
}
function durationText(seconds:number|null){if(seconds==null)return '—';if(seconds<60)return `${seconds} 秒`;return `${Math.floor(seconds/60)} 分 ${seconds%60} 秒`}
onMounted(load)
</script>

<template><div>
  <div class="page-heading"><div><span class="eyebrow">ASSIGNMENTS</span><h1>问卷派发</h1><p>跟踪填写进度，查看患者原始答案、得分和风险分析。</p></div><div class="heading-actions"><el-button @click="load">刷新数据</el-button><router-link to="/assignments/create"><el-button type="primary">+ 新建派发</el-button></router-link></div></div>
  <article class="panel table-panel"><el-table :data="items" v-loading="loading" stripe>
    <el-table-column prop="title" label="任务" min-width="180"/><el-table-column prop="patient_code" label="患者" width="110"/>
    <el-table-column label="问卷与进度" min-width="250"><template #default="scope"><div class="item-status-list"><span v-for="item in scope.row.items" :key="item.id"><b>{{item.questionnaire_name}}</b><small>{{labels[item.status]||item.status}}</small></span></div></template></el-table-column>
    <el-table-column label="状态" width="100"><template #default="scope"><el-tag :type="tags[scope.row.status] as any">{{labels[scope.row.status]}}</el-tag></template></el-table-column>
    <el-table-column prop="deadline" label="截止时间" min-width="155"><template #default="scope">{{scope.row.deadline?new Date(scope.row.deadline).toLocaleString():'不限时'}}</template></el-table-column>
    <el-table-column label="操作" width="130" fixed="right"><template #default="scope"><el-button v-if="completedItems(scope.row).length" link type="primary" @click="openResult(scope.row)">查看填写结果</el-button><span v-else class="muted">等待提交</span></template></el-table-column>
  </el-table></article>
  <el-dialog v-model="resultDialog" title="患者填写结果" width="min(820px, 94vw)" destroy-on-close><div v-loading="resultLoading" class="result-dialog">
    <div v-if="selectedAssignment&&completedItems(selectedAssignment).length>1" class="result-tabs"><el-button v-for="item in completedItems(selectedAssignment)" :key="item.id" :type="result?.item_id===item.id?'primary':'default'" @click="openResult(selectedAssignment,item.id)">{{item.questionnaire_name}}</el-button></div>
    <template v-if="result"><div class="result-title"><div><span class="eyebrow">{{result.questionnaire_code}} · V{{result.questionnaire_version}}</span><h2>{{result.questionnaire_name}}</h2><p>患者 {{result.patient_code}} · {{new Date(result.submitted_at).toLocaleString()}} 提交</p></div><el-tag size="large" :type="result.assessment.risk_level==='high'?'danger':result.assessment.risk_level==='medium'?'warning':'success'">{{riskLabels[result.assessment.risk_level]}}</el-tag></div>
      <div class="result-summary"><div><small>总分</small><strong>{{result.assessment.total_score??'待复核'}}</strong></div><div><small>填写用时</small><strong>{{durationText(result.duration_seconds)}}</strong></div><div><small>复核状态</small><strong>{{result.assessment.review_status==='pending'?'待医生复核':'自动计分'}}</strong></div></div>
      <div v-if="Object.keys(result.assessment.dimension_scores||{}).length" class="dimension-row"><b>维度得分</b><el-tag v-for="(score,name) in result.assessment.dimension_scores" :key="name">{{name}}：{{score}}</el-tag></div>
      <h3 class="answer-heading">逐题答案</h3><div class="answer-list"><div v-for="(answer,index) in result.answers" :key="answer.question_key" class="answer-row"><span class="answer-index">{{index+1}}</span><div><b>{{answer.label}}</b><p>{{answer.display_value}}</p></div></div></div>
      <div class="notice-card"><b>结果说明</b><p>此处为问卷筛查结果和患者原始回答，不等同于医学诊断，需由医生结合临床资料综合判断。</p></div>
    </template></div></el-dialog>
</div></template>
