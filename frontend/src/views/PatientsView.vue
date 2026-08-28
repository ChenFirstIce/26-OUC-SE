<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const patients = ref<any[]>([])
const total = ref(0)
const keyword = ref('')
const loading = ref(false)
const dialog = ref(false)
const form = reactive({ patient_code: '', sex: '', birth_date: '', education_level: '', residence_type: '' })
async function load() { loading.value = true; try { const { data } = await api.get('/patients', { params: { keyword: keyword.value } }); patients.value = data.items; total.value = data.total } finally { loading.value = false } }
async function create() {
  try { await api.post('/patients', { ...form, birth_date: form.birth_date || null, sex: form.sex || null, education_level: form.education_level || null, residence_type: form.residence_type || null }); ElMessage.success('患者档案创建成功'); dialog.value = false; Object.assign(form, { patient_code: '', sex: '', birth_date: '', education_level: '', residence_type: '' }); load() }
  catch (error) { ElMessage.error((error as Error).message) }
}
onMounted(load)
</script>
<template>
  <div>
    <div class="page-heading"><div><span class="eyebrow">PATIENTS</span><h1>患者管理</h1><p>使用匿名患者编码管理筛查任务与历史结果。</p></div><el-button type="primary" @click="dialog=true">+ 新建患者</el-button></div>
    <article class="panel table-panel">
      <div class="toolbar"><el-input v-model="keyword" placeholder="搜索患者编码" clearable @keyup.enter="load"/><el-button @click="load">查询</el-button><span class="muted">共 {{ total }} 人</span></div>
      <el-table :data="patients" v-loading="loading" stripe>
        <el-table-column prop="patient_code" label="患者编码" min-width="120"><template #default="scope"><router-link class="table-link" :to="`/patients/${scope.row.id}`">{{ scope.row.patient_code }}</router-link></template></el-table-column>
        <el-table-column prop="sex" label="性别" width="90"><template #default="s">{{ s.row.sex === 'male' ? '男' : s.row.sex === 'female' ? '女' : '未填写' }}</template></el-table-column>
        <el-table-column prop="birth_date" label="出生日期" min-width="120" />
        <el-table-column prop="education_level" label="教育程度" min-width="120" />
        <el-table-column prop="department_name" label="科室" min-width="120" />
        <el-table-column prop="doctor_name" label="负责医生" min-width="110" />
        <el-table-column label="操作" width="100"><template #default="s"><router-link :to="`/assignments/create?patient=${s.row.id}`"><el-button link type="primary">派发问卷</el-button></router-link></template></el-table-column>
      </el-table>
    </article>
    <el-dialog v-model="dialog" title="新建匿名患者档案" width="520px">
      <el-form label-position="top">
        <el-form-item label="患者编码（必填）"><el-input v-model="form.patient_code" placeholder="例如 P0101" /></el-form-item>
        <div class="form-grid"><el-form-item label="性别"><el-select v-model="form.sex" clearable><el-option label="男" value="male"/><el-option label="女" value="female"/></el-select></el-form-item><el-form-item label="出生日期"><el-date-picker v-model="form.birth_date" value-format="YYYY-MM-DD" /></el-form-item></div>
        <div class="form-grid"><el-form-item label="教育程度"><el-input v-model="form.education_level" /></el-form-item><el-form-item label="居住类型"><el-input v-model="form.residence_type" /></el-form-item></div>
      </el-form>
      <template #footer><el-button @click="dialog=false">取消</el-button><el-button type="primary" :disabled="!form.patient_code" @click="create">保存患者</el-button></template>
    </el-dialog>
  </div>
</template>

