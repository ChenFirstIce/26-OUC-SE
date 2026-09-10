<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'
import StatCard from '../components/StatCard.vue'
import ChartPanel from '../components/ChartPanel.vue'

const loading = ref(true)
const overview = ref<any>({})
const funnel = ref<any>({ counts: {} })
const questionnaires = ref<any[]>([])
const risks = ref<any[]>([])
const scoreSummary = ref<any[]>([])
const riskLabels: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', unknown: '待复核' }
const funnelLabels: Record<string, string> = { pending: '未打开', in_progress: '填写中', submitted: '已提交', reviewed: '已复核', expired: '已过期', revoked: '已撤销' }
const questionnaireOption = computed(() => ({
  tooltip: { trigger: 'axis' }, legend: { bottom: 0 }, grid: { left: 40, right: 20, top: 25, bottom: 55 },
  xAxis: { type: 'category', data: questionnaires.value.map(i => i.name), axisLabel: { interval: 0, rotate: 12 } },
  yAxis: { type: 'value', minInterval: 1 },
  series: [
    { name: '已派发', type: 'bar', data: questionnaires.value.map(i => i.assigned), itemStyle: { color: '#b8c8c0' } },
    { name: '已提交', type: 'bar', data: questionnaires.value.map(i => i.submitted), itemStyle: { color: '#246b5b' } },
  ],
}))
const riskOption = computed(() => ({
  tooltip: { trigger: 'item' }, legend: { bottom: 0 },
  series: [{ type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'],
    data: risks.value.map(i => ({ name: riskLabels[i.level] || i.level, value: i.count })),
    color: ['#76a58f', '#e5b35d', '#c8655a', '#a8a6a0'], label: { formatter: '{b}\n{c}' } }],
}))
const funnelData = computed(() => Object.entries(funnel.value.counts || {}).map(([key, value]) => `${funnelLabels[key] || key} ${value}`).join(' · '))
async function load() {
  loading.value = true
  try {
    const [a,b,c,d,e] = await Promise.all([api.get('/statistics/overview'), api.get('/statistics/funnel'), api.get('/statistics/questionnaires'), api.get('/statistics/risks'), api.get('/statistics/score-summary')])
    overview.value = a.data; funnel.value = b.data; questionnaires.value = c.data; risks.value = d.data; scoreSummary.value = e.data
  } finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-heading"><div><span class="eyebrow">DATA CENTER</span><h1>数据中心</h1><p>查看患者筛查流程、完成情况与需关注结果。</p></div><router-link to="/assignments/create"><el-button type="primary" size="large">+ 派发问卷</el-button></router-link></div>
    <div class="stats-grid">
      <StatCard label="负责患者" :value="overview.patient_count || 0" hint="当前数据权限范围" />
      <StatCard label="问卷派发" :value="overview.assignment_count || 0" hint="包含进行中与已完成" tone="warm" />
      <StatCard label="已提交评估" :value="overview.assessment_count || 0" hint="患者完成并提交" tone="blue" />
      <StatCard label="需关注患者" :value="overview.high_risk_patients || 0" :hint="`高风险占比 ${overview.high_risk_rate || 0}%`" tone="danger" />
    </div>
    <div class="funnel-strip"><b>派发流程</b><span>{{ funnelData || '暂无派发记录' }}</span><strong>完成率 {{ funnel.completion_rate || 0 }}%</strong></div>
    <div class="chart-grid"><ChartPanel title="各问卷派发与提交" :option="questionnaireOption" /><ChartPanel title="筛查风险分布" :option="riskOption" /></div>
    <article class="panel analysis-panel"><div class="panel-head"><div><h3>量表结果分析</h3><p>已提交问卷的得分范围和风险数量</p></div><router-link to="/assignments"><el-button link type="primary">查看患者原始答案 →</el-button></router-link></div><el-table :data="scoreSummary" empty-text="患者提交问卷后将在此形成分析"><el-table-column prop="questionnaire_name" label="问卷" min-width="180"/><el-table-column prop="assessment_count" label="样本数" width="90"/><el-table-column prop="average_score" label="平均分" width="100"/><el-table-column label="分数范围" width="120"><template #default="scope">{{ scope.row.minimum_score ?? '—' }} ～ {{ scope.row.maximum_score ?? '—' }}</template></el-table-column><el-table-column prop="medium_risk_count" label="中风险" width="90"/><el-table-column prop="high_risk_count" label="高风险" width="90"/></el-table></article>
    <div class="notice-card"><b>医学使用提示</b><p>本系统展示的是问卷筛查和风险提示，不能替代医生面诊、完整认知评估或医学诊断。</p></div>
  </div>
</template>
