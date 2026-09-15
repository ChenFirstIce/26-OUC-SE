<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ code: string; answers: any; autoResult?: any }>()
const metrics = computed(() => props.answers?._metrics || {})
const seconds = (milliseconds:any) => milliseconds == null ? '—' : `${(Number(milliseconds) / 1000).toFixed(1)} 秒`
const roleText:any = { assistant:'访谈助手', user:'患者' }
const objectNames:any = { demo_boston_01:'雨伞图', demo_boston_02:'自行车图', demo_boston_03:'苹果图' }
const mocaQuestionLabels:any = { moca_payment_13:'付款方式', moca_abstraction:'抽象分类' }
const mocaQuestionPrompts:any = {
  moca_payment_13:'如果买东西需要付 13 元，请写出 3 种不同的付款方式。',
  moca_abstraction:'请分别说明以下三组词语的共同类别：火车/轮船、锣鼓/笛子、南方/北方。',
}
const bostonScores = computed(() => Object.fromEntries((props.autoResult?.item_scores || []).map((row:any) => [row.question_id, row.score])))
const trailEvents = computed(() => props.answers?.events || [])
// STT 完整版：按 A/B 卷两阶段展示；旧提交（单阶段固定序列）走 legacy 分支。
const sttForm = computed(() => props.answers?.form as string | undefined)
const sttStageViews = computed(() => {
  const stages = props.autoResult?.stages || {}
  const names:any = { practice:'练习', test:'正式测试' }
  return Object.entries(stages).map(([key, stage]: [string, any]) => ({
    key,
    label: `${String(key)[0]} 卷${names[key.split('-')[1]] || key.split('-')[1]}`,
    summary: stage,
    events: stage.events || [],
    lines: (stage.events || []).slice(1).map((event:any, index:number) => ({ from:(stage.events || [])[index], to:event, correct:event.correct })),
    threshold: key.endsWith('-test') ? { ageBand:stage.age_band, seconds:stage.threshold_seconds,
      duration:stage.duration_seconds, abnormal:stage.duration_seconds >= stage.threshold_seconds,
      text:stage.threshold_interpretation } : null,
  }))
})
const isLegacyTrail = computed(() => !sttForm.value)
const trailPositions:any = { '1':{x:12,y:18}, A:{x:72,y:12}, '2':{x:42,y:38}, B:{x:86,y:56}, '3':{x:22,y:78}, C:{x:68,y:86} }
const replayEvents = computed(() => (props.autoResult?.events?.length ? props.autoResult.events : trailEvents.value).map((event:any) => {
  const nodeId = event.node_id ?? event.nodeId
  return { nodeId, timestampMs:event.timestamp_ms ?? event.timestampMs, correct:event.correct,
    expectedNode:event.expected_node ?? event.expectedNode, x:event.x ?? trailPositions[nodeId]?.x, y:event.y ?? trailPositions[nodeId]?.y }
}).filter((event:any) => event.x != null && event.y != null))
const replayLines = computed(() => replayEvents.value.slice(1).map((event:any,index:number) => ({ from:replayEvents.value[index], to:event, correct:event.correct })))

const domainLabels:any = { memory:'记忆力', language:'语言/找词困难', planning:'组织能力/计划能力', attention:'注意力/专心', other_cognition:'其他认知功能' }
const onsetLabels:any = { 1:'近6个月内', 2:'近6个月-2年', 3:'2-5年', 4:'超过5年', 5:'不清楚' }
const informantLabels:any = {
  inform_1:'记性变差', inform_2:'找词困难', inform_3:'计划安排困难',
  inform_4:'容易犯错', inform_5:'其他认知变差', inform_6:'行为性格变化'
}
const additionalLabels:any = {
  additional_1:'其他病因', additional_2:'认知波动', additional_3:'出现形式', additional_4:'进展特点'
}
</script>

<template>
  <section class="evidence">
    <div class="evidence-head"><div><span>SUBMISSION EVIDENCE</span><h3>原始数据</h3></div><small>总用时 {{seconds(metrics.durationMs)}}</small></div>

    <div v-if="code === 'SCD_INTERVIEW'" class="conversation">
      <div v-for="(message,index) in answers.messages || []" :key="index" :class="['message',message.role]"><b>{{roleText[message.role] || message.role}}</b><p>{{message.content}}</p></div>
      <el-empty v-if="!answers.messages?.length" description="没有访谈消息" :image-size="54"/>
    </div>

    <div v-else-if="code === 'MOCA_OPEN_ANSWER'" class="open-answer">
      <div v-for="(answer, questionId) in answers.answers || {}" :key="String(questionId)">
        <small>{{ mocaQuestionLabels[questionId] || questionId }}</small><b>{{ mocaQuestionPrompts[questionId] || 'MoCA-B 开放题' }}</b>
        <small>患者回答</small><p>{{answer || '未填写'}}</p>
      </div>
      <template v-if="!answers.answers">
        <small>患者回答</small><p>{{answers.answer || '未填写'}}</p>
      </template>
    </div>

    <el-table v-else-if="code === 'BOSTON_NAMING'" :data="answers.items || []" empty-text="没有逐题回答" class="evidence-table">
      <el-table-column label="题目" min-width="120"><template #default="s">{{objectNames[s.row.questionId] || s.row.questionId}}</template></el-table-column>
      <el-table-column prop="answer" label="患者回答" min-width="140"/>
      <el-table-column label="使用提示" width="95"><template #default="s">{{s.row.hintUsed ? '是' : '否'}}</template></el-table-column>
      <el-table-column label="单题用时" width="110"><template #default="s">{{seconds(s.row.durationMs)}}</template></el-table-column>
      <el-table-column label="程序核验" width="105"><template #default="s"><el-tag :type="bostonScores[s.row.questionId] ? 'success' : 'warning'">{{bostonScores[s.row.questionId] ? '匹配' : '待确认'}}</el-tag></template></el-table-column>
    </el-table>

    <div v-else-if="code === 'STT_SHAPE_TRAIL_MAKING' && !isLegacyTrail" class="trail-review">
      <div class="stt-forms-tag"><el-tag>STT {{ sttForm }} 卷</el-tag><span class="stt-age">年龄组 {{ answers.ageBand }}</span></div>
      <div v-for="stage in sttStageViews" :key="stage.key" class="stt-stage">
        <h4>{{ stage.label }}
          <el-tag v-if="stage.threshold" :type="stage.threshold.abnormal ? 'danger' : 'success'" size="small">
            {{ stage.threshold.text }}：{{ stage.threshold.duration }}s / 阈值 {{ stage.threshold.seconds }}s（{{ stage.threshold.ageBand }} 岁组）
          </el-tag>
        </h4>
        <div class="trail-summary"><span><small>错误 / 纠正</small><b>{{stage.summary.error_count}} / {{stage.summary.correction_count}}</b></span><span><small>首次点击 / 阶段用时</small><b>{{seconds(stage.summary.first_click_ms)}} / {{seconds(stage.summary.duration_ms)}}</b></span><span><small>完成节点数</small><b>{{stage.summary.sequence?.length || 0}}</b></span></div>
        <div class="trail-replay"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><line v-for="(line,index) in stage.lines" :key="`line-${index}`" :x1="line.from.x" :y1="line.from.y" :x2="line.to.x" :y2="line.to.y" :class="{error:!line.correct}"/><g v-for="(event,index) in stage.events" :key="`point-${index}`"><circle :cx="event.x" :cy="event.y" r="3.4" :class="{error:!event.correct}"/><text :x="event.x" :y="event.y+1.2" text-anchor="middle">{{index+1}}</text></g></svg></div>
      </div>
    </div>

    <div v-else-if="code === 'STT_SHAPE_TRAIL_MAKING'" class="trail-review">
      <div class="trail-summary"><span><small>完成顺序</small><b>{{(answers.sequence || []).join(' → ') || '—'}}</b></span><span><small>错误 / 纠正</small><b>{{autoResult?.error_count ?? answers.errorCount ?? 0}} / {{autoResult?.correction_count ?? 0}}</b></span><span><small>首次点击 / 总用时</small><b>{{seconds(autoResult?.first_click_ms)}} / {{seconds(autoResult?.duration_ms ?? metrics.durationMs)}}</b></span></div>
      <div class="trail-replay"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><line v-for="(line,index) in replayLines" :key="`line-${index}`" :x1="line.from.x" :y1="line.from.y" :x2="line.to.x" :y2="line.to.y" :class="{error:!line.correct}"/><g v-for="(event,index) in replayEvents" :key="`point-${index}`"><circle :cx="event.x" :cy="event.y" r="4" :class="{error:!event.correct}"/><text :x="event.x" :y="event.y+1.4" text-anchor="middle">{{index+1}}</text></g></svg><span v-for="node in Object.keys(trailPositions)" :key="node" :style="{left:`${trailPositions[node].x}%`,top:`${trailPositions[node].y}%`}">{{node}}</span></div>
      <div class="trail-events"><span v-for="(event,index) in trailEvents" :key="index" :class="{error:!event.correct}"><i>{{event.nodeId}}</i><small>{{seconds(event.timestampMs)}} · {{event.correct ? '正确' : '错误点击'}}</small></span></div>
    </div>

    <div v-else-if="code === 'SCD_STRUCTURED_INTERVIEW'" class="scd-structured-review">
      <div class="scd-summary">
        <span><small>选择认知域</small><b>{{ answers.selectedDomains?.length || 0 }} 个</b></span>
        <span><small>阳性域数</small><b>{{ autoResult?.positive_domains?.length || 0 }} 个</b></span>
        <span><small>知情者</small><b>{{ autoResult?.informant_available ? '有' : '无' }}</b></span>
      </div>

      <div v-if="answers.selectedDomains?.length" class="scd-domains">
        <h4>认知域详情</h4>
        <div v-for="domain in answers.selectedDomains" :key="domain" class="domain-card">
          <div class="domain-header">
            <b>{{ domainLabels[domain] || domain }}</b>
            <el-tag :type="answers.mainAnswers?.[domain] ? 'warning' : 'info'" size="small">
              {{ answers.mainAnswers?.[domain] ? '是' : '否' }}
            </el-tag>
          </div>
          <div v-if="answers.mainAnswers?.[domain] && answers.followUpAnswers?.[domain]" class="follow-up">
            <span v-if="answers.followUpAnswers[domain].A !== undefined">
              <small>是否担心</small>{{ answers.followUpAnswers[domain].A === 1 ? '是' : '否' }}
            </span>
            <span v-if="answers.followUpAnswers[domain].B !== undefined">
              <small>变差时间</small>{{ onsetLabels[answers.followUpAnswers[domain].B] || '—' }}
            </span>
            <span v-if="answers.followUpAnswers[domain].C !== undefined">
              <small>比同龄人差</small>{{ answers.followUpAnswers[domain].C === 1 ? '是' : '否' }}
            </span>
            <span v-if="answers.followUpAnswers[domain].D !== undefined">
              <small>看过医生</small>{{ answers.followUpAnswers[domain].D === 1 ? '是' : '否' }}
            </span>
            <span v-if="answers.followUpAnswers[domain].E">
              <small>首次就诊</small>{{ answers.followUpAnswers[domain].E }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="answers.informant" class="scd-informant">
        <h4>知情者问卷</h4>
        <div class="informant-info">
          <span><small>可用性</small><b>{{ answers.informant.available ? '有知情者' : '无知情者' }}</b></span>
          <span v-if="answers.informant.relation"><small>关系</small><b>{{ answers.informant.relation }}</b></span>
        </div>
        <div v-if="answers.informant.answers" class="informant-answers">
          <div v-for="(answer, questionId) in answers.informant.answers" :key="questionId" class="informant-item">
            <small>{{ informantLabels[questionId] || questionId }}</small>
            <b>{{ answer.answer ? '是' : '否' }}</b>
            <span v-if="answer.onset">{{ onsetLabels[answer.onset] || answer.onset }}</span>
          </div>
        </div>
      </div>

      <div v-if="answers.additionalInformation" class="scd-additional">
        <h4>补充信息</h4>
        <div class="additional-grid">
          <span v-for="(value, key) in answers.additionalInformation" :key="key">
            <small>{{ additionalLabels[key] || key }}</small>
            <b>{{ value }}</b>
          </span>
        </div>
      </div>
    </div>

    <div v-else class="fallback"><div v-for="(value,key) in answers" :key="key"><b>{{key}}</b><span>{{String(value)}}</span></div></div>
  </section>
</template>

<style scoped>
.evidence{margin-top:18px}.evidence-head{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:12px}.evidence-head span{color:#1686d9;font-size:9px;font-weight:700;letter-spacing:.16em}.evidence-head h3{margin:4px 0 0}.evidence-head>small{color:#718299}.conversation{display:flex;flex-direction:column;gap:10px;padding:16px;background:#f4f7f5;border-radius:12px}.message{max-width:82%;padding:11px 13px;background:#fff;border:1px solid #dce7e1;border-radius:12px}.message.user{align-self:flex-end;background:#e4f1eb}.message b,.open-answer small{color:#718299;font-size:10px}.message p{margin:5px 0 0;line-height:1.65}.open-answer{display:grid;gap:12px;padding:18px;background:#f4f7f5;border-radius:12px}.open-answer>div{display:grid;gap:8px}.open-answer b{color:#31495f}.open-answer p{padding:14px;margin:0;background:#fff;border-radius:8px;line-height:1.7}.trail-summary{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px}.stt-forms-tag{display:flex;align-items:center;gap:10px;margin-bottom:4px}.stt-age{color:#718299;font-size:12px}.stt-stage{margin-top:14px}.stt-stage h4{display:flex;align-items:center;gap:10px;margin:0 0 10px}.stt-stage+.stt-stage{padding-top:14px;border-top:1px dashed #dce7e1}.trail-replay+.trail-replay{margin-top:0}.trail-summary span{padding:13px;background:#f4f7f5;border-radius:9px}.trail-summary small,.trail-summary b{display:block}.trail-summary small{margin-bottom:6px;color:#718299}.trail-replay{position:relative;height:320px;margin-top:12px;background:linear-gradient(145deg,#f5f8f6,#eaf2ee);border:1px solid #dce7e1;border-radius:12px}.trail-replay svg{position:absolute;inset:0;width:100%;height:100%}.trail-replay line{stroke:#43816f;stroke-width:1.2;vector-effect:non-scaling-stroke}.trail-replay line.error{stroke:#c65b5b;stroke-dasharray:4 3}.trail-replay circle{fill:#43816f}.trail-replay circle.error{fill:#c65b5b}.trail-replay text{fill:#fff;font-size:3px}.trail-replay>span{position:absolute;display:grid;place-items:center;width:34px;height:34px;transform:translate(-50%,-50%);color:#29473f;background:#fff;border:1px solid #aac0b7;border-radius:50%;font-weight:700}.trail-events{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.trail-events span{display:flex;align-items:center;gap:7px;padding:7px 10px;background:#e9f4ef;border-radius:99px}.trail-events span.error{color:#a54646;background:#fff0f0}.trail-events i{display:grid;place-items:center;width:24px;height:24px;color:#fff;font-style:normal;background:#367866;border-radius:50%}.trail-events .error i{background:#c45d5d}.scd-structured-review{display:flex;flex-direction:column;gap:16px}.scd-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.scd-summary span{padding:13px;background:#f4f7f5;border-radius:9px}.scd-summary small{display:block;margin-bottom:6px;color:#718299;font-size:11px}.scd-summary b{color:#31495f}.scd-domains,.scd-informant,.scd-additional{padding:16px;background:#f4f7f5;border-radius:12px}.scd-domains h4,.scd-informant h4,.scd-additional h4{margin:0 0 12px;color:#31495f;font-size:14px}.domain-card{padding:12px;margin-bottom:8px;background:#fff;border-radius:10px}.domain-card:last-child{margin-bottom:0}.domain-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}.domain-header b{color:#31495f}.follow-up{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px}.follow-up span{display:flex;flex-direction:column;gap:4px;padding:8px;background:#f8faf9;border-radius:6px;font-size:13px}.follow-up small{color:#718299;font-size:10px}.informant-info{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:12px}.informant-info span{padding:10px;background:#fff;border-radius:8px}.informant-info small{display:block;margin-bottom:4px;color:#718299;font-size:10px}.informant-answers{display:grid;gap:8px}.informant-item{display:grid;grid-template-columns:140px 60px 1fr;align-items:center;gap:10px;padding:10px;background:#fff;border-radius:8px}.informant-item small{color:#718299;font-size:11px}.informant-item b{color:#31495f}.additional-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}.additional-grid span{display:flex;flex-direction:column;gap:6px;padding:12px;background:#fff;border-radius:8px}.additional-grid small{color:#718299;font-size:10px}.additional-grid b{color:#31495f}.fallback{display:grid;gap:8px}.fallback div{display:grid;grid-template-columns:120px 1fr;padding:10px;background:#f4f7f5}.evidence-table{border:1px solid #e1e9e5;border-radius:10px}@media(max-width:600px){.trail-summary{grid-template-columns:1fr}.trail-replay{height:250px}.message{max-width:94%}.scd-summary{grid-template-columns:1fr}.follow-up{grid-template-columns:1fr}.informant-info{grid-template-columns:1fr}.informant-item{grid-template-columns:1fr;gap:6px}.additional-grid{grid-template-columns:1fr}}
</style>
