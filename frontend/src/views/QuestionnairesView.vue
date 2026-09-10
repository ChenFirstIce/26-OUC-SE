<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import QuestionnaireDetailDialog from '../components/QuestionnaireDetailDialog.vue'

const auth = useAuthStore()
const list = ref<any[]>([])
const loading = ref(true)
const dialog = ref(false)
const detailDialog = ref(false)
const detailItem = ref<any>()
const tab = ref('catalog')
const catalog = ref<any[]>([])
const selected = ref<string[]>([])
const importing = ref(false)
const packageText = ref('')
const modeLabels: any = { patient_self:'患者自评', informant:'知情者填写', clinician:'医生施测' }
const parsedPackage = computed(() => {
  try {
    const value = JSON.parse(packageText.value)
    const templates = Array.isArray(value) ? value : value.templates || [value]
    return { valid:true, count:templates.length, names:templates.map((item:any) => item.name || item.code).slice(0,4) }
  } catch { return { valid:false, count:0, names:[] } }
})

async function load() {
  loading.value = true
  try { list.value = (await api.get('/questionnaires')).data }
  finally { loading.value = false }
}

function openDetail(item: any) {
  detailItem.value = item
  detailDialog.value = true
}

async function openImport() {
  dialog.value = true
  if (!catalog.value.length) catalog.value = (await api.get('/questionnaires/catalog')).data
}

async function importCatalog() {
  if (!selected.value.length) return
  importing.value = true
  try {
    const { data } = await api.post('/questionnaires/import-catalog', { codes:selected.value, publish:false })
    ElMessage.success(`已导入 ${data.items.length} 个量表草稿`)
    dialog.value = false
    selected.value = []
    load()
  } catch (error) { ElMessage.error((error as Error).message) }
  finally { importing.value = false }
}

async function importJson() {
  if (!parsedPackage.value.valid) return
  importing.value = true
  try {
    const value = JSON.parse(packageText.value)
    const templates = Array.isArray(value) ? value : value.templates || [value]
    const { data } = await api.post('/questionnaires/import-package', { templates, conflict_strategy:value.conflict_strategy || 'new_version', publish:false })
    ElMessage.success(`已校验并导入 ${data.items.length} 个问卷模板`)
    dialog.value = false
    packageText.value = ''
    load()
  } catch (error) { ElMessage.error((error as Error).message) }
  finally { importing.value = false }
}

async function readFile(file: any) {
  try { packageText.value = await file.raw.text() }
  catch { ElMessage.error('文件读取失败') }
}

async function publishTemplate(row: any) {
  try {
    await ElMessageBox.confirm(`发布 ${row.name} v${row.latest_version} 后即可用于派发，确认发布吗？`, '发布确认', { type:'warning' })
    await api.post(`/questionnaires/${row.id}/publish`)
    ElMessage.success('量表已发布')
    load()
  } catch (error) {
    if (error !== 'cancel' && (error as Error).message) ElMessage.error((error as Error).message)
  }
}

function downloadExample() {
  const sample = { templates:[{ code:'CUSTOM_SCALE', name:'自定义问卷', description:'机构自定义问卷', questionnaire_schema:{ title:'自定义问卷', administration_mode:'patient_self', notice:'请按实际情况填写', sections:[{ key:'basic', title:'基本问题', questions:[{ key:'q1', type:'single_choice', label:'示例单选题', required:true, options:[{value:'yes',label:'是',score:1},{value:'no',label:'否',score:0}] }] }] }, scoring_json:{strategy:'metadata_sum',risk_thresholds:[]} }] }
  const blob = new Blob([JSON.stringify(sample,null,2)], { type:'application/json' })
  const anchor = document.createElement('a')
  anchor.href = URL.createObjectURL(blob)
  anchor.download = 'questionnaire-import-example.json'
  anchor.click()
  URL.revokeObjectURL(anchor.href)
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-heading">
      <div><span class="eyebrow">QUESTIONNAIRE LIBRARY</span><h1>问卷模板</h1><p>点击问卷可查看完整内容；管理员可通过标准 JSON 包或内置量表目录导入。</p></div>
      <el-button v-if="auth.user?.role === 'admin'" type="primary" @click="openImport">+ 导入量表</el-button>
    </div>

    <div class="import-flow"><span><b>1</b>选择来源</span><i></i><span><b>2</b>结构校验</span><i></i><span><b>3</b>生成草稿/新版本</span><i></i><span><b>4</b>管理员发布</span></div>

    <div class="template-grid" v-loading="loading">
      <article v-for="questionnaire in list" :key="questionnaire.id" class="template-card questionnaire-card" tabindex="0" role="button" @click="openDetail(questionnaire)" @keyup.enter="openDetail(questionnaire)">
        <div class="template-top"><span class="template-code">{{questionnaire.code}}</span><el-tag :type="questionnaire.status === 'published' ? 'success' : 'warning'">{{questionnaire.status === 'published' ? '已发布' : '待审核草稿'}}</el-tag></div>
        <h3>{{questionnaire.name}}</h3>
        <p>{{questionnaire.description}}</p>
        <div v-if="questionnaire.schema_json?.source" class="source-line"><span>{{modeLabels[questionnaire.schema_json.administration_mode] || '未指定方式'}}</span><span>来源：{{questionnaire.schema_json.source.file_name}}</span></div>
        <div class="template-foot"><span>版本 v{{questionnaire.latest_version}}</span><span>{{questionnaire.schema_json?.sections?.reduce((total:number,section:any) => total + section.questions.length,0) || 0}} 题</span><span class="detail-link">查看详情 →</span><el-button v-if="auth.user?.role === 'admin' && questionnaire.status !== 'published'" link type="primary" @click.stop="publishTemplate(questionnaire)">审核并发布</el-button></div>
      </article>
    </div>

    <div class="notice-card"><b>正式量表与授权</b><p>MoCA-B、ADAS-Cog 等含视觉或操作任务的量表以“医生结果录入版”导入，原始材料仍需由机构按授权要求获取和施测；系统不会把扫描图误识别后直接发布给患者。</p></div>

    <QuestionnaireDetailDialog v-model="detailDialog" :questionnaire="detailItem"/>

    <el-dialog v-model="dialog" title="导入问卷模板" width="min(920px,96vw)" top="4vh">
      <el-tabs v-model="tab">
        <el-tab-pane label="OUC 量表目录" name="catalog">
          <div class="catalog-intro"><b>已适配你提供的 oucwy/ad-ouc 仓库</b><span>SCD-Q9、MMSE、FAQ 可结构化填写；MoCA-B、CDR、ADAS-Cog 按医生施测/结果录入方式适配。</span></div>
          <el-checkbox-group v-model="selected" class="catalog-grid">
            <label v-for="item in catalog" :key="item.code" class="catalog-item">
              <el-checkbox :value="item.code"/>
              <div><div class="catalog-title"><b>{{item.name}}</b><el-tag size="small">{{modeLabels[item.administration_mode]}}</el-tag></div><p>{{item.description}}</p><small>{{item.question_count}} 个结构化字段 · {{item.source.file_name}}</small><em>{{item.source.review_note}}</em></div>
            </label>
          </el-checkbox-group>
          <div class="dialog-actions"><span>已选择 {{selected.length}} 个；重复编码会自动建立新版本。</span><el-button type="primary" :loading="importing" :disabled="!selected.length" @click="importCatalog">导入为草稿</el-button></div>
        </el-tab-pane>
        <el-tab-pane label="标准 JSON 包" name="json">
          <div class="json-toolbar"><el-upload :auto-upload="false" :show-file-list="false" accept=".json,application/json" :on-change="readFile"><el-button>选择 JSON 文件</el-button></el-upload><el-button link type="primary" @click="downloadExample">下载导入示例</el-button></div>
          <el-input v-model="packageText" type="textarea" :rows="16" placeholder="选择 JSON 文件，或在此粘贴问卷包内容"/>
          <div class="package-state" :class="{ok:parsedPackage.valid}"><span v-if="parsedPackage.valid">✓ JSON 格式有效，包含 {{parsedPackage.count}} 个模板：{{parsedPackage.names.join('、')}}</span><span v-else>等待有效 JSON；后端还会校验题型、题目 key 和分区结构。</span></div>
          <div class="dialog-actions"><span>支持单模板、templates 数组和相同编码自动新增版本。</span><el-button type="primary" :loading="importing" :disabled="!parsedPackage.valid" @click="importJson">校验并导入草稿</el-button></div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<style scoped>
.questionnaire-card{cursor:pointer;transition:transform .2s,border-color .2s,box-shadow .2s}.questionnaire-card:hover,.questionnaire-card:focus-visible{border-color:#66c8e5;box-shadow:0 16px 40px rgba(26,99,150,.12);outline:none;transform:translateY(-2px)}.detail-link{margin-left:auto;color:#1686d9;font-weight:700}.import-flow{display:flex;align-items:center;gap:12px;padding:12px 18px;margin-bottom:18px;color:#5d708b;font-size:12px;background:#fff;border:1px solid #e0e9f3;border-radius:12px}.import-flow span{display:flex;align-items:center;gap:7px}.import-flow b{display:grid;place-items:center;width:22px;height:22px;color:#1788ba;background:#e8f6fb;border-radius:50%}.import-flow i{flex:1;height:1px;background:#dfe8f2}.source-line{display:flex;flex-direction:column;gap:4px;padding:9px;margin:12px 0;color:#637690;font-size:10px;background:#f4f8fc;border-radius:7px}.catalog-intro{display:flex;flex-direction:column;gap:6px;padding:14px 16px;margin-bottom:16px;background:#eef8fc;border:1px solid #d6ecf5;border-radius:10px}.catalog-intro span{color:#587187;font-size:12px;line-height:1.65}.catalog-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-items:stretch;gap:12px;max-height:53vh;padding:1px 6px 1px 1px;overflow:auto}.catalog-item{display:flex;align-items:flex-start;gap:12px;min-height:196px;height:auto;padding:16px;overflow:hidden;cursor:pointer;background:#fff;border:1px solid #dce7f3;border-radius:12px;transition:border-color .2s,background-color .2s,box-shadow .2s}.catalog-item:hover{background:#f8fcfe;border-color:#69c6e3;box-shadow:0 8px 22px rgba(38,116,161,.08)}.catalog-item :deep(.el-checkbox){flex:none;align-self:flex-start;height:auto;margin:3px 0 0}.catalog-item>div{display:flex;flex:1;flex-direction:column;min-width:0;height:100%}.catalog-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;min-height:28px}.catalog-title b{color:#203650;font-size:14px;line-height:1.55}.catalog-title :deep(.el-tag){flex:none}.catalog-item p{min-height:42px;margin:10px 0;color:#63748c;font-size:12px;line-height:1.7}.catalog-item small{display:block;padding-top:9px;color:#8494a9;font-size:10px;line-height:1.65;overflow-wrap:anywhere;border-top:1px solid #edf2f7}.catalog-item em{display:block;margin-top:8px;color:#a86620;font-size:10px;font-style:normal;line-height:1.65;overflow-wrap:anywhere}.dialog-actions,.json-toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:16px}.dialog-actions span{color:#71819a;font-size:11px}.json-toolbar{justify-content:flex-start;margin:0 0 12px}.package-state{padding:10px 12px;margin-top:10px;color:#9b6a34;font-size:11px;background:#fff7e9;border-radius:7px}.package-state.ok{color:#25755a;background:#edf9f4}@media(max-width:720px){.catalog-grid{grid-template-columns:1fr;max-height:58vh}.catalog-item{min-height:0}.import-flow i{display:none}.import-flow{flex-wrap:wrap}.dialog-actions{align-items:stretch;flex-direction:column}}
</style>
