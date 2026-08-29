<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const route=useRoute(); const router=useRouter();const auth=useAuthStore(); const patients=ref<any[]>([]); const questionnaires=ref<any[]>([]);const doctors=ref<any[]>([]); const result=ref<any>(); const qr=ref(''); const saving=ref(false)
const form=reactive({ patient_id: Number(route.query.patient)||undefined as number|undefined, questionnaire_version_ids: [] as number[], title:'认知筛查任务', note:'请根据真实感受完成问卷。', deadline:'',doctor_id:undefined as number|undefined })
onMounted(async()=>{ const requests:any[]=[api.get('/patients',{params:{page_size:100}}),api.get('/questionnaires')];if(auth.user?.role==='admin')requests.push(api.get('/admin/users'));const [p,q,u]=await Promise.all(requests); patients.value=p.data.items; questionnaires.value=q.data;doctors.value=(u?.data||[]).filter((i:any)=>i.role==='doctor'&&i.active) })
async function submit(){ saving.value=true; try { const {data}=await api.post('/assignments',{...form,deadline:form.deadline||null}); result.value=data; qr.value=await QRCode.toDataURL(data.patient_link,{width:220,margin:1,color:{dark:'#163d34',light:'#ffffff'}}); ElMessage.success('问卷派发成功') } catch(e){ElMessage.error((e as Error).message)} finally{saving.value=false} }
async function copy(text:string){await navigator.clipboard.writeText(text);ElMessage.success('已复制')}
</script>
<template><div><div class="page-heading"><div><span class="eyebrow">NEW ASSIGNMENT</span><h1>派发问卷</h1><p>选择患者和已发布问卷，生成专属移动端填写入口。</p></div></div>
<div v-if="!result" class="form-page"><article class="panel form-card"><el-form label-position="top">
<el-form-item label="选择患者"><el-select v-model="form.patient_id" filterable placeholder="患者编码" class="full"><el-option v-for="p in patients" :key="p.id" :label="`${p.patient_code} · ${p.doctor_name}`" :value="p.id"/></el-select></el-form-item>
<el-form-item v-if="auth.user?.role==='admin'" label="指定负责医生（不选则沿用患者主诊医生）"><el-select v-model="form.doctor_id" clearable class="full"><el-option v-for="d in doctors" :key="d.id" :label="`${d.display_name} · ${d.department_name||'未分科'}`" :value="d.id"/></el-select></el-form-item>
<el-form-item label="选择问卷（可多选）"><el-checkbox-group v-model="form.questionnaire_version_ids" class="questionnaire-select"><el-checkbox v-for="q in questionnaires" :key="q.latest_version_id" :value="q.latest_version_id"><div><b>{{ q.name }}</b><small>{{ q.description }}</small></div></el-checkbox></el-checkbox-group></el-form-item>
<el-form-item label="任务名称"><el-input v-model="form.title"/></el-form-item><el-form-item label="医生说明"><el-input v-model="form.note" type="textarea" :rows="3"/></el-form-item><el-form-item label="截止时间（可选）"><el-date-picker v-model="form.deadline" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ"/></el-form-item>
<div class="actions"><el-button @click="router.back()">取消</el-button><el-button type="primary" size="large" :loading="saving" :disabled="!form.patient_id||!form.questionnaire_version_ids.length" @click="submit">生成填写入口</el-button></div>
</el-form></article></div>
<article v-else class="success-card"><div class="success-icon">✓</div><h2>问卷派发成功</h2><p>将二维码或链接和访问码交给患者。访问码请通过独立方式告知。</p><img :src="qr" alt="患者填写二维码" class="qr"/><div class="secret-row"><div><small>访问码</small><strong>{{ result.access_code }}</strong></div><el-button @click="copy(result.access_code)">复制</el-button></div><div class="link-box"><span>{{ result.patient_link }}</span><el-button link type="primary" @click="copy(result.patient_link)">复制链接</el-button></div><div class="actions center"><router-link to="/assignments"><el-button>查看派发列表</el-button></router-link><el-button type="primary" @click="result=null">继续派发</el-button></div></article>
</div></template>
