<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
const route = useRoute(); const patient = ref<any>(); const loading = ref(true)
const riskText: any = { low: '低风险', medium: '中风险', high: '高风险', unknown: '待复核' }
onMounted(async () => { try { patient.value = (await api.get(`/patients/${route.params.id}`)).data } finally { loading.value = false } })
</script>
<template><div v-loading="loading"><template v-if="patient"><div class="page-heading"><div><span class="eyebrow">PATIENT PROFILE</span><h1>{{ patient.patient_code }}</h1><p>{{ patient.department_name }} · {{ patient.doctor_name }}</p></div><router-link :to="`/assignments/create?patient=${patient.id}`"><el-button type="primary">派发新问卷</el-button></router-link></div>
<div class="profile-grid"><article class="panel"><h3>基本档案</h3><dl class="detail-list"><dt>性别</dt><dd>{{ patient.sex === 'male' ? '男' : patient.sex === 'female' ? '女' : '未填写' }}</dd><dt>出生日期</dt><dd>{{ patient.birth_date || '未填写' }}</dd><dt>教育程度</dt><dd>{{ patient.education_level || '未填写' }}</dd><dt>居住类型</dt><dd>{{ patient.residence_type || '未填写' }}</dd></dl></article>
<article class="panel"><h3>评估时间线</h3><el-empty v-if="!patient.assessments.length" description="尚无已提交评估"/><div v-for="a in patient.assessments" :key="a.id" class="timeline-item"><div><b>{{ a.questionnaire_code }}</b><span>{{ new Date(a.assessed_at).toLocaleString() }}</span></div><div><el-tag :type="a.risk_level==='high'?'danger':a.risk_level==='medium'?'warning':'success'">{{ riskText[a.risk_level] }}</el-tag><strong>{{ a.total_score ?? '—' }} 分</strong></div></div></article></div></template></div></template>

