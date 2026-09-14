<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ code: string; answers: any; autoResult?: any }>()
const metrics = computed(() => props.answers?._metrics || {})
const seconds = (milliseconds:any) => milliseconds == null ? '—' : `${(Number(milliseconds) / 1000).toFixed(1)} 秒`
const roleText:any = { assistant:'访谈助手', user:'患者' }
const objectNames:any = { demo_boston_01:'雨伞图', demo_boston_02:'自行车图', demo_boston_03:'苹果图' }
const bostonScores = computed(() => Object.fromEntries((props.autoResult?.item_scores || []).map((row:any) => [row.question_id, row.score])))
const trailEvents = computed(() => props.answers?.events || [])
const trailPositions:any = { '1':{x:12,y:18}, A:{x:72,y:12}, '2':{x:42,y:38}, B:{x:86,y:56}, '3':{x:22,y:78}, C:{x:68,y:86} }
const replayEvents = computed(() => (props.autoResult?.events?.length ? props.autoResult.events : trailEvents.value).map((event:any) => {
  const nodeId = event.node_id ?? event.nodeId
  return { nodeId, timestampMs:event.timestamp_ms ?? event.timestampMs, correct:event.correct,
    expectedNode:event.expected_node ?? event.expectedNode, x:event.x ?? trailPositions[nodeId]?.x, y:event.y ?? trailPositions[nodeId]?.y }
}).filter((event:any) => event.x != null && event.y != null))
const replayLines = computed(() => replayEvents.value.slice(1).map((event:any,index:number) => ({ from:replayEvents.value[index], to:event, correct:event.correct })))
</script>

<template>
  <section class="evidence">
    <div class="evidence-head"><div><span>SUBMISSION EVIDENCE</span><h3>原始数据</h3></div><small>总用时 {{seconds(metrics.durationMs)}}</small></div>

    <div v-if="code === 'DEMO_SCD_INTERVIEW'" class="conversation">
      <div v-for="(message,index) in answers.messages || []" :key="index" :class="['message',message.role]"><b>{{roleText[message.role] || message.role}}</b><p>{{message.content}}</p></div>
      <el-empty v-if="!answers.messages?.length" description="没有访谈消息" :image-size="54"/>
    </div>

    <div v-else-if="code === 'DEMO_MOCA_OPEN'" class="open-answer">
      <small>演示题目</small><b>“火车”和“自行车”有什么共同之处？</b>
      <small>患者回答</small><p>{{answers.answer || '未填写'}}</p>
    </div>

    <el-table v-else-if="code === 'DEMO_BOSTON'" :data="answers.items || []" empty-text="没有逐题回答" class="evidence-table">
      <el-table-column label="题目" min-width="120"><template #default="s">{{objectNames[s.row.questionId] || s.row.questionId}}</template></el-table-column>
      <el-table-column prop="answer" label="患者回答" min-width="140"/>
      <el-table-column label="使用提示" width="95"><template #default="s">{{s.row.hintUsed ? '是' : '否'}}</template></el-table-column>
      <el-table-column label="单题用时" width="110"><template #default="s">{{seconds(s.row.durationMs)}}</template></el-table-column>
      <el-table-column label="程序核验" width="105"><template #default="s"><el-tag :type="bostonScores[s.row.questionId] ? 'success' : 'warning'">{{bostonScores[s.row.questionId] ? '匹配' : '待确认'}}</el-tag></template></el-table-column>
    </el-table>

    <div v-else-if="code === 'DEMO_TRAIL'" class="trail-review">
      <div class="trail-summary"><span><small>完成顺序</small><b>{{(answers.sequence || []).join(' → ') || '—'}}</b></span><span><small>错误 / 纠正</small><b>{{autoResult?.error_count ?? answers.errorCount ?? 0}} / {{autoResult?.correction_count ?? 0}}</b></span><span><small>首次点击 / 总用时</small><b>{{seconds(autoResult?.first_click_ms)}} / {{seconds(autoResult?.duration_ms ?? metrics.durationMs)}}</b></span></div>
      <div class="trail-replay"><svg viewBox="0 0 100 100" preserveAspectRatio="none"><line v-for="(line,index) in replayLines" :key="`line-${index}`" :x1="line.from.x" :y1="line.from.y" :x2="line.to.x" :y2="line.to.y" :class="{error:!line.correct}"/><g v-for="(event,index) in replayEvents" :key="`point-${index}`"><circle :cx="event.x" :cy="event.y" r="4" :class="{error:!event.correct}"/><text :x="event.x" :y="event.y+1.4" text-anchor="middle">{{index+1}}</text></g></svg><span v-for="node in Object.keys(trailPositions)" :key="node" :style="{left:`${trailPositions[node].x}%`,top:`${trailPositions[node].y}%`}">{{node}}</span></div>
      <div class="trail-events"><span v-for="(event,index) in trailEvents" :key="index" :class="{error:!event.correct}"><i>{{event.nodeId}}</i><small>{{seconds(event.timestampMs)}} · {{event.correct ? '正确' : '错误点击'}}</small></span></div>
    </div>

    <div v-else class="fallback"><div v-for="(value,key) in answers" :key="key"><b>{{key}}</b><span>{{String(value)}}</span></div></div>
  </section>
</template>

<style scoped>
.evidence{margin-top:18px}.evidence-head{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:12px}.evidence-head span{color:#1686d9;font-size:9px;font-weight:700;letter-spacing:.16em}.evidence-head h3{margin:4px 0 0}.evidence-head>small{color:#718299}.conversation{display:flex;flex-direction:column;gap:10px;padding:16px;background:#f4f7f5;border-radius:12px}.message{max-width:82%;padding:11px 13px;background:#fff;border:1px solid #dce7e1;border-radius:12px}.message.user{align-self:flex-end;background:#e4f1eb}.message b,.open-answer small{color:#718299;font-size:10px}.message p{margin:5px 0 0;line-height:1.65}.open-answer{display:grid;gap:8px;padding:18px;background:#f4f7f5;border-radius:12px}.open-answer b{color:#31495f}.open-answer p{padding:14px;margin:0;background:#fff;border-radius:8px;line-height:1.7}.trail-summary{display:grid;grid-template-columns:2fr 1fr 1fr;gap:10px}.trail-summary span{padding:13px;background:#f4f7f5;border-radius:9px}.trail-summary small,.trail-summary b{display:block}.trail-summary small{margin-bottom:6px;color:#718299}.trail-replay{position:relative;height:320px;margin-top:12px;background:linear-gradient(145deg,#f5f8f6,#eaf2ee);border:1px solid #dce7e1;border-radius:12px}.trail-replay svg{position:absolute;inset:0;width:100%;height:100%}.trail-replay line{stroke:#43816f;stroke-width:1.2;vector-effect:non-scaling-stroke}.trail-replay line.error{stroke:#c65b5b;stroke-dasharray:4 3}.trail-replay circle{fill:#43816f}.trail-replay circle.error{fill:#c65b5b}.trail-replay text{fill:#fff;font-size:3px}.trail-replay>span{position:absolute;display:grid;place-items:center;width:34px;height:34px;transform:translate(-50%,-50%);color:#29473f;background:#fff;border:1px solid #aac0b7;border-radius:50%;font-weight:700}.trail-events{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.trail-events span{display:flex;align-items:center;gap:7px;padding:7px 10px;background:#e9f4ef;border-radius:99px}.trail-events span.error{color:#a54646;background:#fff0f0}.trail-events i{display:grid;place-items:center;width:24px;height:24px;color:#fff;font-style:normal;background:#367866;border-radius:50%}.trail-events .error i{background:#c45d5d}.fallback{display:grid;gap:8px}.fallback div{display:grid;grid-template-columns:120px 1fr;padding:10px;background:#f4f7f5}.evidence-table{border:1px solid #e1e9e5;border-radius:10px}@media(max-width:600px){.trail-summary{grid-template-columns:1fr}.trail-replay{height:250px}.message{max-width:94%}}
</style>
