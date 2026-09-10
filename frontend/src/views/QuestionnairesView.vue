<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import QuestionnaireDetailDialog from '../components/QuestionnaireDetailDialog.vue'

const auth = useAuthStore()
const list = ref<any[]>([])
const loading = ref(true)
const importDialog = ref(false)
const detailDialog = ref(false)
const detailItem = ref<any>()
const tab = ref('catalog')
const catalog = ref<any[]>([])
const selected = ref<string[]>([])
const importing = ref(false)
const packageText = ref('')
const previewItems = ref<any[]>([])
const governanceDialog = ref(false)
const governanceTemplate = ref<any>()
const versions = ref<any[]>([])
const governanceLoading = ref(false)
const diffDialog = ref(false)
const diffData = ref<any>()
const diffTitle = ref('')
const publishDialog = ref(false)
const publishTarget = ref<any>()
const publishForm = ref({ confirmation_code:'', change_summary:'', acknowledge_warnings:false })
const retireDialog = ref(false)
const retireTarget = ref<any>()
const retireForm = ref({ confirmation_code:'', reason:'' })
const modeLabels: any = { patient_self:'患者自评', informant:'知情者填写', clinician:'医生施测' }
const statusLabels: any = { draft:'草稿待审核', published:'当前可派发', retired:'已停用' }
const statusTypes: any = { draft:'warning', published:'success', retired:'info' }

const parsedPackage = computed(() => {
  try {
    const value = JSON.parse(packageText.value)
    const templates = Array.isArray(value) ? value : value.templates || [value]
    return { valid:true, templates, count:templates.length, names:templates.map((item:any) => item.name || item.code).slice(0,4), conflictStrategy:value.conflict_strategy || 'new_version' }
  } catch { return { valid:false, templates:[], count:0, names:[], conflictStrategy:'new_version' } }
})
const previewValid = computed(() => previewItems.value.length > 0 && previewItems.value.every(item => item.valid))

watch([selected, packageText, tab], () => { previewItems.value = [] }, { deep:true })

async function load() {
  loading.value = true
  try { list.value = (await api.get('/questionnaires')).data }
  finally { loading.value = false }
}

function openDetail(item: any) {
  detailItem.value = { ...item, status:item.latest_version_status || item.status }
  detailDialog.value = true
}

async function openImport() {
  importDialog.value = true
  previewItems.value = []
  if (!catalog.value.length) catalog.value = (await api.get('/questionnaires/catalog')).data
}

async function previewCatalog() {
  if (!selected.value.length) return
  importing.value = true
  try { previewItems.value = (await api.post('/questionnaires/import-preview/catalog', { codes:selected.value })).data.items }
  catch (error) { ElMessage.error((error as Error).message) }
  finally { importing.value = false }
}

async function importCatalog() {
  importing.value = true
  try {
    const { data } = await api.post('/questionnaires/import-catalog', { codes:selected.value, publish:false })
    ElMessage.success(`已导入 ${data.items.length} 个量表草稿`)
    importDialog.value = false
    selected.value = []
    previewItems.value = []
    await load()
  } catch (error) { ElMessage.error((error as Error).message) }
  finally { importing.value = false }
}

async function previewJson() {
  if (!parsedPackage.value.valid) return
  importing.value = true
  try {
    previewItems.value = (await api.post('/questionnaires/import-preview', {
      templates:parsedPackage.value.templates, conflict_strategy:parsedPackage.value.conflictStrategy, publish:false,
    })).data.items
  } catch (error) { ElMessage.error((error as Error).message) }
  finally { importing.value = false }
}

async function importJson() {
  importing.value = true
  try {
    const preview_hashes = Object.fromEntries(previewItems.value.map(item => [item.code, item.content_hash]))
    const preview_versions = Object.fromEntries(previewItems.value.map(item => [item.code, item.current_version]))
    const { data } = await api.post('/questionnaires/import-package', {
      templates:parsedPackage.value.templates, conflict_strategy:parsedPackage.value.conflictStrategy,
      publish:false, preview_hashes, preview_versions,
    })
    ElMessage.success(`已导入 ${data.items.length} 个问卷草稿`)
    importDialog.value = false
    packageText.value = ''
    previewItems.value = []
    await load()
  } catch (error) { ElMessage.error((error as Error).message) }
  finally { importing.value = false }
}

async function readFile(file: any) {
  try { packageText.value = await file.raw.text() }
  catch { ElMessage.error('文件读取失败') }
}

async function openGovernance(row: any) {
  governanceTemplate.value = row
  governanceDialog.value = true
  governanceLoading.value = true
  try { versions.value = (await api.get(`/questionnaires/${row.id}/versions`)).data }
  finally { governanceLoading.value = false }
}

async function showDiff(version: any, index: number) {
  const base = versions.value[index + 1]
  if (!base) return
  diffTitle.value = `${governanceTemplate.value.code} · v${base.version} → v${version.version}`
  diffData.value = (await api.get(`/questionnaires/versions/${version.id}/diff`, { params:{ base_version_id:base.id } })).data
  diffDialog.value = true
}

function openPublish(version: any) {
  publishTarget.value = version
  publishForm.value = { confirmation_code:'', change_summary:'', acknowledge_warnings:false }
  publishDialog.value = true
}

async function submitPublish() {
  try {
    await api.post(`/questionnaires/versions/${publishTarget.value.id}/publish`, {
      expected_content_hash:publishTarget.value.content_hash, ...publishForm.value,
    })
    ElMessage.success(`v${publishTarget.value.version} 已发布，原可派发版本已自动停用`)
    publishDialog.value = false
    await openGovernance(governanceTemplate.value)
    await load()
  } catch (error) { ElMessage.error((error as Error).message) }
}

function openRetire(version: any) {
  retireTarget.value = version
  retireForm.value = { confirmation_code:'', reason:'' }
  retireDialog.value = true
}

async function submitRetire() {
  try {
    await api.post(`/questionnaires/versions/${retireTarget.value.id}/retire`, retireForm.value)
    ElMessage.success(`v${retireTarget.value.version} 已停止新派发，历史任务不受影响`)
    retireDialog.value = false
    await openGovernance(governanceTemplate.value)
    await load()
  } catch (error) { ElMessage.error((error as Error).message) }
}

function downloadExample() {
  const sample = { templates:[{ code:'CUSTOM_SCALE', name:'自定义问卷', description:'机构自定义问卷', questionnaire_schema:{ title:'自定义问卷', administration_mode:'patient_self', source:{file_name:'内部审核稿',review_note:'发布前确认授权和计分规则'}, notice:'请按实际情况填写', sections:[{ key:'basic', title:'基本问题', questions:[{ key:'q1', type:'single_choice', label:'示例单选题', required:true, options:[{value:'yes',label:'是',score:1},{value:'no',label:'否',score:0}] }] }] }, scoring_json:{strategy:'metadata_sum',risk_thresholds:[]} }] }
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
      <div><span class="eyebrow">QUESTIONNAIRE LIBRARY</span><h1>问卷模板</h1><p>问卷按版本审核发布；停用只阻止新派发，不影响已有任务和历史结果。</p></div>
      <el-button v-if="auth.user?.role === 'admin'" type="primary" @click="openImport">+ 导入量表</el-button>
    </div>

    <div class="import-flow"><span><b>1</b>导入预览</span><i></i><span><b>2</b>生成草稿版本</span><i></i><span><b>3</b>核对版本差异</span><i></i><span><b>4</b>二次确认发布</span></div>

    <div class="template-grid" v-loading="loading">
      <article v-for="questionnaire in list" :key="questionnaire.id" class="template-card questionnaire-card" tabindex="0" role="button" @click="openDetail(questionnaire)" @keyup.enter="openDetail(questionnaire)">
        <div class="template-top"><span class="template-code">{{questionnaire.code}}</span><el-tag :type="statusTypes[questionnaire.status]">{{statusLabels[questionnaire.status] || questionnaire.status}}</el-tag></div>
        <h3>{{questionnaire.name}}</h3>
        <p>{{questionnaire.description}}</p>
        <div v-if="questionnaire.schema_json?.source" class="source-line"><span>{{modeLabels[questionnaire.schema_json.administration_mode] || '未指定方式'}}</span><span>来源：{{questionnaire.schema_json.source.file_name}}</span></div>
        <div class="template-foot"><span>最新 v{{questionnaire.latest_version}} · {{statusLabels[questionnaire.latest_version_status]}}</span><span v-if="questionnaire.active_version">可派发 v{{questionnaire.active_version}}</span><span>{{questionnaire.total_versions}} 个版本</span><span class="detail-link">查看详情 →</span><el-button v-if="auth.user?.role === 'admin'" link type="primary" @click.stop="openGovernance(questionnaire)">版本治理</el-button></div>
      </article>
    </div>

    <div class="notice-card"><b>正式量表与授权</b><p>MoCA-B、ADAS-Cog 等含视觉或操作任务的量表以“医生结果录入版”导入，原始材料仍需由机构按授权要求获取和施测；系统不会把扫描图误识别后直接发布给患者。</p></div>

    <QuestionnaireDetailDialog v-model="detailDialog" :questionnaire="detailItem"/>

    <el-dialog v-model="importDialog" title="导入问卷模板" width="min(980px,96vw)" top="3vh">
      <el-tabs v-model="tab">
        <el-tab-pane label="OUC 量表目录" name="catalog">
          <div class="catalog-intro"><b>先预览校验，再写入草稿</b><span>系统会显示新建/升级、问题和警告；目录量表仍需管理员核对授权与计分规则。</span></div>
          <el-checkbox-group v-model="selected" class="catalog-grid">
            <label v-for="item in catalog" :key="item.code" class="catalog-item"><el-checkbox :value="item.code"/><div><div class="catalog-title"><b>{{item.name}}</b><el-tag size="small">{{modeLabels[item.administration_mode]}}</el-tag></div><p>{{item.description}}</p><small>{{item.question_count}} 个结构化字段 · {{item.source.file_name}}</small><em>{{item.source.review_note}}</em></div></label>
          </el-checkbox-group>
          <div class="dialog-actions"><span>已选择 {{selected.length}} 个</span><el-button :loading="importing" :disabled="!selected.length" @click="previewCatalog">生成导入预览</el-button><el-button type="primary" :loading="importing" :disabled="!previewValid" @click="importCatalog">确认导入草稿</el-button></div>
        </el-tab-pane>
        <el-tab-pane label="标准 JSON 包" name="json">
          <div class="json-toolbar"><el-upload :auto-upload="false" :show-file-list="false" accept=".json,application/json" :on-change="readFile"><el-button>选择 JSON 文件</el-button></el-upload><el-button link type="primary" @click="downloadExample">下载导入示例</el-button></div>
          <el-input v-model="packageText" type="textarea" :rows="12" placeholder="选择 JSON 文件，或在此粘贴问卷包内容"/>
          <div class="package-state" :class="{ok:parsedPackage.valid}"><span v-if="parsedPackage.valid">✓ JSON 格式有效，包含 {{parsedPackage.count}} 个模板：{{parsedPackage.names.join('、')}}</span><span v-else>等待有效 JSON；正式导入前还必须通过后端治理校验。</span></div>
          <div class="dialog-actions"><span>预览后若内容发生变化，必须重新预览。</span><el-button :loading="importing" :disabled="!parsedPackage.valid" @click="previewJson">治理校验与预览</el-button><el-button type="primary" :loading="importing" :disabled="!previewValid" @click="importJson">确认导入草稿</el-button></div>
        </el-tab-pane>
      </el-tabs>
      <section v-if="previewItems.length" class="preview-results">
        <h3>导入预览</h3>
        <article v-for="item in previewItems" :key="item.code" :class="['preview-result',{invalid:!item.valid}]">
          <header><b>{{item.code}} · {{item.name}}</b><el-tag :type="item.valid ? 'success' : 'danger'">{{item.valid ? '可导入' : '禁止导入'}}</el-tag><span>{{item.action === 'create' ? '新建 v1' : `v${item.current_version} → v${item.proposed_version}`}}</span></header>
          <p>新增 {{item.diff.added_questions.length}} 题 · 删除 {{item.diff.removed_questions.length}} 题 · 修改 {{item.diff.changed_questions.length}} 题<span v-if="item.diff.scoring_changed"> · 计分规则有变化</span></p>
          <ul v-if="item.errors.length"><li v-for="message in item.errors" :key="message" class="error">错误：{{message}}</li></ul>
          <ul v-if="item.warnings.length"><li v-for="message in item.warnings" :key="message" class="warning">警告：{{message}}</li></ul>
        </article>
      </section>
    </el-dialog>

    <el-dialog v-model="governanceDialog" :title="`${governanceTemplate?.code || ''} 版本治理`" width="min(1040px,96vw)">
      <el-table :data="versions" v-loading="governanceLoading">
        <el-table-column label="版本" width="80"><template #default="scope"><b>v{{scope.row.version}}</b></template></el-table-column>
        <el-table-column label="状态" width="120"><template #default="scope"><el-tag :type="statusTypes[scope.row.status]">{{statusLabels[scope.row.status]}}</el-tag></template></el-table-column>
        <el-table-column prop="change_summary" label="发布说明" min-width="180"><template #default="scope">{{scope.row.change_summary || '尚未填写'}}</template></el-table-column>
        <el-table-column label="治理检查" min-width="190"><template #default="scope"><span v-if="scope.row.errors.length" class="error">{{scope.row.errors.length}} 项错误</span><span v-else-if="scope.row.warnings.length" class="warning">{{scope.row.warnings.length}} 项警告待确认</span><span v-else class="ok-text">检查通过</span></template></el-table-column>
        <el-table-column label="操作" width="250"><template #default="scope"><el-button v-if="versions[scope.$index + 1]" link @click="showDiff(scope.row,scope.$index)">版本差异</el-button><el-button v-if="scope.row.status === 'draft'" link type="primary" :disabled="scope.row.errors.length" @click="openPublish(scope.row)">审核发布</el-button><el-button v-if="scope.row.status === 'published'" link type="danger" @click="openRetire(scope.row)">停止新派发</el-button></template></el-table-column>
      </el-table>
      <p class="governance-note">发布新版本会自动停用旧版本；已派发任务继续使用当时锁定的版本。</p>
    </el-dialog>

    <el-dialog v-model="diffDialog" :title="diffTitle" width="min(680px,94vw)">
      <div v-if="diffData" class="diff-panel"><p :class="diffData.risk_level === 'high' ? 'error' : 'ok-text'">{{diffData.risk_level === 'high' ? '高风险变更：包含删题或计分规则变化' : '常规结构变更'}}</p><div><b>新增题目</b><span>{{diffData.added_questions.join('、') || '无'}}</span></div><div><b>删除题目</b><span>{{diffData.removed_questions.join('、') || '无'}}</span></div><div><b>修改题目</b><span>{{diffData.changed_questions.join('、') || '无'}}</span></div><div><b>问卷属性</b><span>{{diffData.schema_fields_changed.join('、') || '无'}}</span></div><div><b>计分规则</b><span>{{diffData.scoring_changed ? '已变化' : '未变化'}}</span></div></div>
    </el-dialog>

    <el-dialog v-model="publishDialog" :title="`发布 ${governanceTemplate?.code || ''} v${publishTarget?.version || ''}`" width="min(620px,94vw)">
      <p>发布后即可用于新派发，原可派发版本会自动停用。请输入问卷编号确认。</p>
      <el-form label-position="top"><el-form-item label="问卷编号"><el-input v-model="publishForm.confirmation_code" :placeholder="governanceTemplate?.code"/></el-form-item><el-form-item label="版本变更说明"><el-input v-model="publishForm.change_summary" type="textarea" :rows="3" placeholder="说明题目、计分或使用范围的变化"/></el-form-item><el-checkbox v-if="publishTarget?.warnings?.length" v-model="publishForm.acknowledge_warnings">我已核对并接受 {{publishTarget.warnings.length}} 项治理警告</el-checkbox></el-form>
      <template #footer><el-button @click="publishDialog=false">取消</el-button><el-button type="primary" :disabled="publishForm.confirmation_code !== governanceTemplate?.code || publishForm.change_summary.length < 2 || (publishTarget?.warnings?.length && !publishForm.acknowledge_warnings)" @click="submitPublish">确认发布</el-button></template>
    </el-dialog>

    <el-dialog v-model="retireDialog" :title="`停止 ${governanceTemplate?.code || ''} v${retireTarget?.version || ''} 新派发`" width="min(620px,94vw)">
      <p>已有任务和历史结果不会删除。请输入问卷编号并填写原因。</p>
      <el-form label-position="top"><el-form-item label="问卷编号"><el-input v-model="retireForm.confirmation_code" :placeholder="governanceTemplate?.code"/></el-form-item><el-form-item label="停用原因"><el-input v-model="retireForm.reason" type="textarea" :rows="3"/></el-form-item></el-form>
      <template #footer><el-button @click="retireDialog=false">取消</el-button><el-button type="danger" :disabled="retireForm.confirmation_code !== governanceTemplate?.code || retireForm.reason.length < 2" @click="submitRetire">确认停止新派发</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.questionnaire-card{cursor:pointer;transition:transform .2s,border-color .2s,box-shadow .2s}.questionnaire-card:hover,.questionnaire-card:focus-visible{border-color:#66c8e5;box-shadow:0 16px 40px rgba(26,99,150,.12);outline:none;transform:translateY(-2px)}.detail-link{margin-left:auto;color:#1686d9;font-weight:700}.import-flow{display:flex;align-items:center;gap:12px;padding:12px 18px;margin-bottom:18px;color:#5d708b;font-size:12px;background:#fff;border:1px solid #e0e9f3;border-radius:12px}.import-flow span{display:flex;align-items:center;gap:7px}.import-flow b{display:grid;place-items:center;width:22px;height:22px;color:#1788ba;background:#e8f6fb;border-radius:50%}.import-flow i{flex:1;height:1px;background:#dfe8f2}.source-line{display:flex;flex-direction:column;gap:4px;padding:9px;margin:12px 0;color:#637690;font-size:10px;background:#f4f8fc;border-radius:7px}.catalog-intro{display:flex;flex-direction:column;gap:6px;padding:14px 16px;margin-bottom:16px;background:#eef8fc;border:1px solid #d6ecf5;border-radius:10px}.catalog-intro span{color:#587187;font-size:12px;line-height:1.65}.catalog-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));align-items:stretch;gap:12px;max-height:43vh;padding:1px 6px 1px 1px;overflow:auto}.catalog-item{display:flex;align-items:flex-start;gap:12px;min-height:170px;padding:16px;overflow:hidden;cursor:pointer;background:#fff;border:1px solid #dce7f3;border-radius:12px}.catalog-item :deep(.el-checkbox){flex:none;align-self:flex-start;height:auto;margin:3px 0 0}.catalog-item>div{display:flex;flex:1;flex-direction:column;min-width:0}.catalog-title{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.catalog-item p{margin:10px 0;color:#63748c;font-size:12px;line-height:1.7}.catalog-item small{padding-top:9px;color:#8494a9;font-size:10px;border-top:1px solid #edf2f7}.catalog-item em{margin-top:8px;color:#a86620;font-size:10px;font-style:normal;line-height:1.65}.dialog-actions,.json-toolbar{display:flex;align-items:center;justify-content:flex-end;gap:12px;margin-top:16px}.dialog-actions span{margin-right:auto;color:#71819a;font-size:11px}.json-toolbar{justify-content:flex-start;margin:0 0 12px}.package-state{padding:10px 12px;margin-top:10px;color:#9b6a34;font-size:11px;background:#fff7e9;border-radius:7px}.package-state.ok{color:#25755a;background:#edf9f4}.preview-results{margin-top:18px;padding-top:14px;border-top:1px solid #e2eaf2}.preview-results h3{margin:0 0 10px}.preview-result{padding:12px 14px;margin-top:8px;background:#f5faf8;border:1px solid #dcece5;border-radius:9px}.preview-result.invalid{background:#fff7f7;border-color:#f0d7d7}.preview-result header{display:flex;align-items:center;gap:10px}.preview-result header span{margin-left:auto;color:#6d7d91;font-size:11px}.preview-result p,.preview-result ul{margin:7px 0 0;color:#687b92;font-size:11px}.error{color:#c34e58}.warning{color:#aa6b1f}.ok-text{color:#25805e}.governance-note{color:#718199;font-size:11px}.diff-panel{display:grid;gap:11px}.diff-panel>div{display:grid;grid-template-columns:100px 1fr;gap:12px;padding:10px;background:#f5f8fb;border-radius:8px}.diff-panel span{color:#60728a}.governance-note,.diff-panel,.preview-results{line-height:1.6}@media(max-width:720px){.catalog-grid{grid-template-columns:1fr}.import-flow i{display:none}.import-flow{flex-wrap:wrap}.dialog-actions{align-items:stretch;flex-direction:column}.dialog-actions span{margin:0}.diff-panel>div{grid-template-columns:1fr}}
</style>
