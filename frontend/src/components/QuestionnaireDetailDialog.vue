<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ modelValue: boolean; questionnaire?: any }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const schema = computed(() => props.questionnaire?.schema_json || {})
const sections = computed(() => schema.value.sections || [])
const scoring = computed(() => props.questionnaire?.scoring_json || {})
const questionCount = computed(() => sections.value.reduce((total: number, section: any) => total + (section.questions?.length || 0), 0))
const modeLabels: Record<string, string> = { patient_self:'患者自评', informant:'知情者填写', clinician:'医生施测' }
const typeLabels: Record<string, string> = {
  single_choice:'单选题', multi_choice:'多选题', yes_no:'是非题', scale:'量表选择',
  number:'数字录入', integer:'整数录入', duration:'时长录入', short_text:'短文本',
  long_text:'长文本', date:'日期', time:'时间', clinician_score:'医生评分',
}

function close() { emit('update:modelValue', false) }
function typeLabel(type: string) { return typeLabels[type] || type || '未指定' }
function optionScore(option: any) { return option.score === undefined || option.score === null ? '' : ` · ${option.score} 分` }
function isSingleChoice(type: string) { return ['single_choice', 'yes_no', 'scale'].includes(type) }
function isNumber(type: string) { return ['number', 'integer', 'duration', 'clinician_score'].includes(type) }
function thresholdText(item: any) {
  const range = item.max === undefined || item.max === null ? `${item.min ?? 0} 分以上` : `${item.min ?? 0}–${item.max} 分`
  const level = { low:'低风险', medium:'中风险', high:'高风险', unknown:'待复核' }[item.level as string] || item.level
  return `${range}：${level}`
}
</script>

<template>
  <el-dialog :model-value="modelValue" width="min(920px,96vw)" top="4vh" destroy-on-close append-to-body @update:model-value="emit('update:modelValue',$event)">
    <template #header>
      <div v-if="questionnaire" class="detail-dialog-title">
        <span>{{questionnaire.code}} · V{{questionnaire.latest_version}}</span>
        <h2>{{questionnaire.name}}</h2>
      </div>
    </template>

    <div v-if="questionnaire" class="questionnaire-detail">
      <section class="detail-summary">
        <div><small>当前状态</small><el-tag :type="questionnaire.status === 'published' ? 'success' : 'warning'">{{questionnaire.status === 'published' ? '已发布' : '草稿待审核'}}</el-tag></div>
        <div><small>填写/施测方式</small><strong>{{modeLabels[schema.administration_mode] || '未指定'}}</strong></div>
        <div><small>结构规模</small><strong>{{sections.length}} 个分区 · {{questionCount}} 题</strong></div>
        <div><small>计分策略</small><strong>{{scoring.strategy === 'metadata_sum' ? '按题目元数据自动计分' : scoring.strategy || '医生录入/待复核'}}</strong></div>
      </section>

      <section class="questionnaire-preview">
        <header class="preview-header">
          <div><span>FORM PREVIEW</span><h3>{{schema.title || questionnaire.name}}</h3><p>以下为实际录入界面的只读预览，可直接核对具体题目与选项。</p></div>
          <el-tag effect="plain">{{modeLabels[schema.administration_mode] || '问卷预览'}}</el-tag>
        </header>
        <div v-if="schema.notice" class="preview-notice">{{schema.notice}}</div>
        <section v-for="(section,sectionIndex) in sections" :key="`preview-${section.key || sectionIndex}`" class="preview-section">
          <h4>{{section.title || `第 ${sectionIndex + 1} 部分`}}</h4>
          <article v-for="(question,questionIndex) in section.questions" :key="`preview-${question.key || questionIndex}`" class="preview-question">
            <label><span>{{sectionIndex + 1}}.{{questionIndex + 1}}</span><b>{{question.label || question.key}}</b><em v-if="question.required">必填</em></label>
            <p v-if="question.help_text">{{question.help_text}}</p>
            <el-radio-group v-if="isSingleChoice(question.type)" model-value="" disabled class="preview-options">
              <el-radio v-for="option in question.options || []" :key="String(option.value)" :value="option.value" border>{{option.label}}</el-radio>
            </el-radio-group>
            <el-checkbox-group v-else-if="question.type === 'multi_choice'" :model-value="[]" disabled class="preview-options">
              <el-checkbox v-for="option in question.options || []" :key="String(option.value)" :value="option.value" border>{{option.label}}</el-checkbox>
            </el-checkbox-group>
            <el-input-number v-else-if="isNumber(question.type)" :model-value="undefined" :min="question.min" :max="question.max" disabled controls-position="right"/>
            <el-date-picker v-else-if="question.type === 'date'" :model-value="''" disabled placeholder="选择日期"/>
            <el-time-picker v-else-if="question.type === 'time'" :model-value="''" disabled placeholder="选择时间"/>
            <el-input v-else :model-value="''" :type="question.type === 'long_text' ? 'textarea' : 'text'" :rows="question.type === 'long_text' ? 3 : undefined" disabled :placeholder="question.type === 'long_text' ? '填写详细内容' : '填写答案'"/>
          </article>
        </section>
        <el-empty v-if="!sections.length" description="该版本尚未配置可预览的题目"/>
      </section>

      <section class="detail-description">
        <h3>用途说明</h3>
        <p>{{questionnaire.description || '暂无说明'}}</p>
        <div v-if="schema.notice" class="detail-notice">{{schema.notice}}</div>
      </section>

      <section v-if="schema.source" class="source-panel">
        <div><small>资料来源</small><strong>{{schema.source.file_name || '未记录文件名'}}</strong></div>
        <div v-if="schema.source.review_note"><small>审核与授权提示</small><p>{{schema.source.review_note}}</p></div>
      </section>

      <section class="question-sections">
        <div class="section-heading"><div><span>QUESTION STRUCTURE</span><h3>问卷内容</h3></div><b>共 {{questionCount}} 题</b></div>
        <article v-for="(section,sectionIndex) in sections" :key="section.key || sectionIndex" class="question-section">
          <header><span>{{String(sectionIndex + 1).padStart(2,'0')}}</span><div><h4>{{section.title || `第 ${sectionIndex + 1} 部分`}}</h4><small>{{section.description || section.key}}</small></div></header>
          <div v-for="(question,questionIndex) in section.questions" :key="question.key || questionIndex" class="question-detail-row">
            <span class="question-number">{{questionIndex + 1}}</span>
            <div class="question-content">
              <div class="question-title"><b>{{question.label || question.key}}</b><div><el-tag size="small" effect="plain">{{typeLabel(question.type)}}</el-tag><el-tag v-if="question.required" size="small" type="danger" effect="plain">必填</el-tag></div></div>
              <p v-if="question.help_text">{{question.help_text}}</p>
              <div v-if="question.options?.length" class="option-preview"><span v-for="option in question.options" :key="String(option.value)">{{option.label}}{{optionScore(option)}}</span></div>
              <div class="question-meta"><span v-if="question.dimension">维度：{{question.dimension}}</span><span v-if="question.min !== undefined">最小值：{{question.min}}</span><span v-if="question.max !== undefined">最大值：{{question.max}}</span><span v-if="question.show_if">条件显示：{{question.show_if.question_key}} = {{question.show_if.equals}}</span></div>
            </div>
          </div>
        </article>
        <el-empty v-if="!sections.length" description="该版本尚未配置结构化题目"/>
      </section>

      <section class="scoring-panel">
        <div><h3>计分与风险规则</h3><p>用于系统自动汇总和风险提示，不替代医生诊断。</p></div>
        <div v-if="scoring.risk_thresholds?.length" class="threshold-list"><span v-for="(item,index) in scoring.risk_thresholds" :key="index">{{thresholdText(item)}}</span></div>
        <span v-else class="manual-score">该问卷需要医生施测、录入或人工复核结果。</span>
      </section>
    </div>

    <template #footer><el-button type="primary" @click="close">关闭详情</el-button></template>
  </el-dialog>
</template>

<style scoped>
.detail-dialog-title span{color:#1686d9;font-size:10px;font-weight:700;letter-spacing:.16em}.detail-dialog-title h2{margin:6px 0 0;color:#142640;font-size:23px}.questionnaire-detail{display:flex;flex-direction:column;gap:16px;max-height:72vh;padding-right:5px;overflow:auto}.detail-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.detail-summary>div{min-height:76px;padding:14px;background:#f4f8fc;border:1px solid #e4edf6;border-radius:10px}.detail-summary small,.detail-summary strong{display:block}.detail-summary small{margin-bottom:9px;color:#8090a5;font-size:10px}.detail-summary strong{color:#203650;font-size:12px;line-height:1.5}.detail-description,.source-panel,.scoring-panel{padding:17px 19px;border:1px solid #e0e9f3;border-radius:12px}.detail-description h3,.scoring-panel h3{margin:0;color:#203650;font-size:15px}.detail-description>p,.scoring-panel p{margin:7px 0 0;color:#63748c;font-size:12px;line-height:1.7}.detail-notice{padding:10px 12px;margin-top:12px;color:#795b2c;font-size:11px;line-height:1.6;background:#fff8eb;border-radius:8px}.source-panel{display:grid;grid-template-columns:1fr 1.2fr;gap:18px;background:#f8fbfe}.source-panel small,.source-panel strong{display:block}.source-panel small{margin-bottom:6px;color:#8090a5;font-size:10px}.source-panel strong,.source-panel p{margin:0;color:#405875;font-size:11px;line-height:1.65;overflow-wrap:anywhere}.section-heading{display:flex;align-items:flex-end;justify-content:space-between;margin:4px 0 10px}.section-heading span{color:#1686d9;font-size:9px;font-weight:700;letter-spacing:.17em}.section-heading h3{margin:4px 0 0;color:#203650}.section-heading>b{color:#7c8ea5;font-size:11px}.question-section{margin-bottom:12px;overflow:hidden;border:1px solid #dfe8f2;border-radius:12px}.question-section>header{display:flex;align-items:center;gap:12px;padding:13px 16px;background:linear-gradient(90deg,#edf8fc,#f5f8fd)}.question-section>header>span{display:grid;place-items:center;width:31px;height:31px;color:#1686d9;font-size:11px;font-weight:700;background:#fff;border-radius:9px}.question-section h4{margin:0;color:#203650}.question-section header small{display:block;margin-top:3px;color:#8998ab;font-size:9px}.question-detail-row{display:grid;grid-template-columns:28px 1fr;gap:11px;padding:14px 16px;border-top:1px solid #edf1f6}.question-number{display:grid;place-items:center;width:25px;height:25px;color:#1686d9;font-size:10px;font-weight:700;background:#eaf6fb;border-radius:50%}.question-title{display:flex;align-items:flex-start;justify-content:space-between;gap:15px}.question-title>b{color:#263b56;font-size:12px;line-height:1.65}.question-title>div{display:flex;flex:none;gap:5px}.question-content>p{margin:6px 0;color:#74849a;font-size:11px}.option-preview{display:flex;flex-wrap:wrap;gap:6px;margin-top:9px}.option-preview span{padding:5px 8px;color:#536a86;font-size:10px;background:#f2f6fa;border:1px solid #e1e9f1;border-radius:6px}.question-meta{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px;color:#8b99aa;font-size:9px}.scoring-panel{display:flex;align-items:center;justify-content:space-between;gap:18px;background:#fbfcfe}.threshold-list{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:7px}.threshold-list span,.manual-score{padding:7px 9px;color:#49647f;font-size:10px;background:#edf5fa;border-radius:7px}.manual-score{color:#9b6a34;background:#fff5e5}@media(max-width:760px){.detail-summary{grid-template-columns:1fr 1fr}.source-panel{grid-template-columns:1fr}.scoring-panel{align-items:flex-start;flex-direction:column}.threshold-list{justify-content:flex-start}.question-title{flex-direction:column}.question-title>div{flex-wrap:wrap}}@media(max-width:480px){.detail-summary{grid-template-columns:1fr}}
.questionnaire-preview{padding:20px;background:#f6f9fd;border:1px solid #dbe6f1;border-radius:14px}.preview-header{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;padding-bottom:15px;border-bottom:1px solid #dfe8f2}.preview-header span{color:#1686d9;font-size:9px;font-weight:700;letter-spacing:.17em}.preview-header h3{margin:5px 0 4px;color:#172c48;font-size:20px}.preview-header p{margin:0;color:#788aa0;font-size:11px}.preview-notice{padding:11px 13px;margin:14px 0;color:#775b2c;font-size:11px;line-height:1.65;background:#fff8e9;border:1px solid #f3e5c7;border-radius:8px}.preview-section{margin-top:16px}.preview-section>h4{padding:0 0 10px;margin:0;color:#2b425e;font-size:14px;border-bottom:1px solid #dfe7f0}.preview-question{padding:16px;margin-top:10px;background:#fff;border:1px solid #e0e8f1;border-radius:10px}.preview-question>label{display:flex;align-items:flex-start;gap:8px;color:#253b56;line-height:1.65}.preview-question>label>span{color:#1686d9;font-size:10px;font-weight:700}.preview-question>label>b{font-size:13px}.preview-question>label>em{flex:none;padding:1px 5px;color:#d45b66;font-size:9px;font-style:normal;background:#fff0f1;border-radius:4px}.preview-question>p{margin:6px 0;color:#7c8da3;font-size:10px}.preview-options{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.preview-options :deep(.el-radio),.preview-options :deep(.el-checkbox){height:auto;margin:0;padding:9px 12px}.preview-question :deep(.el-input),.preview-question :deep(.el-input-number),.preview-question :deep(.el-date-editor){width:100%;margin-top:12px}
</style>
