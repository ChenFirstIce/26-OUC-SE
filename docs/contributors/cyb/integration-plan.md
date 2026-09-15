# 六项认知评估任务系统整合与 RAG 辅助评分实现计划

## 1. 背景与目标

### 1.1 当前状态

- **admin-web**（Vue 3 + Element Plus）：医生端，支持患者管理、问卷派发、结果查看
- **server**（FastAPI + SQLAlchemy）：统一后端，已完成基础问卷管理、派发、草稿、计分、统计功能
- **patient-web/c2b**（React + Vite）：C/B 四项独立演示（SCD 对话、MoCA-B 开放题、Boston 命名、STT 连线）

### 1.2 目标

将六项认知评估任务（GDS-15、ESS、Boston 命名、STT 连线、SCD 对话、MoCA-B 开放题）统一接入正式工作流：
1. 医生派发六项任务组合
2. 患者通过统一的患者端完成作答
3. 后端保存原始答案、交互事件、前端指标
4. 规则可确定的任务（GDS、ESS、Boston）由程序计分；需要理解的任务（SCD、MoCA-B）由 RAG + 模型生成候选分
5. 医生复核并确认最终结果

### 1.3 架构决策

- **前端统一**：所有六项集成到 admin-web 的患者端（`PatientPortal.vue`），不再使用独立 React 演示
- **任务类型扩展**：问卷 schema 增加 `task_type` 字段，支持 `structured_questionnaire | boston_naming | trail_making | scd_interview | moca_open_answer`
- **评分分离**：
  - 前端：计算可校验的初步指标（时长、错误计数、选择结果）
  - 后端程序：执行规则计分（GDS、ESS）
  - RAG + LLM：生成候选分（Boston、SCD、MoCA-B）
  - 医生：确认或修改最终分数
- **版本化知识包**：绑定问卷派发时的量表版本、评分规则、允许提示等

---

## 2. 系统架构设计

### 2.1 数据流向

```
医生创建患者 → 选择问卷版本 → 派发任务包
                               ↓
患者进入患者端 → 查看待完成任务 → 选择任务
                               ↓
┌─────────────────────────────────────────┐
│ 根据 task_type 渲染不同组件              │
│                                         │
│ A 类：普通量表答题器（GDS、ESS）       │
│ B 类：特殊交互组件（Boston、STT）      │
│ C 类：对话/开放题组件（SCD、MoCA-B）  │
└─────────────────────────────────────────┘
       ↓ 保存草稿、提交答案
后端保存 Response（原始答案+事件）
       ↓
规则计分 / RAG 生成候选分
       ↓
医生查看结果 → 复核和确认
       ↓
保存最终评估结果
```

### 2.2 核心表设计变更

**新增表：`task_events`**
```python
class TaskEvent(Base):
    __tablename__ = "task_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id"))
    event_type: str  # 'answer' | 'hint_used' | 'timeout' | 'error' | 'llm_message'
    timestamp: datetime
    data: dict  # 事件详情（回答内容、提示类型等）
```

**新增表：`ai_candidates`**
```python
class AICandidate(Base):
    __tablename__ = "ai_candidates"
    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id"), unique=True)
    task_type: str
    candidate_score: float | None
    explanation: str
    evidence_references: list[str]  # RAG 引用的规则/评分条款
    model_name: str  # deepseek-flash
    prompt_version: str
    status: str  # 'pending' | 'ready' | 'invalid'
    created_at: datetime
    confirmed_score: float | None  # 医生确认后填充
    confirmation_notes: str
    confirmed_at: datetime | None
    confirmed_by_id: int  # 医生 ID
```

**扩展 `Response` 表**
```python
# 新增字段
class Response(Base):
    # ...existing...
    task_type: str = "structured_questionnaire"  # 任务类型
    task_config_ref: str | None  # 任务特定配置（如 Boston 题号、STT 模式）
    provisional_score: float | None  # 前端可计算的初步分数
    metrics_json: dict = {}  # 前端指标（时长、错误、提示等）
    interaction_events: list[dict] = []  # 交互事件序列
```

### 2.3 问卷 Schema 扩展

**新增 questionnaire_schema 字段**
```json
{
  "code": "OUC_BOSTON_NAMING",
  "name": "Boston 命名测试",
  "task_type": "boston_naming",
  "task_config": {
    "items": [
      {
        "id": "boston_01",
        "image_url": "assets/boston/01_tree.png",
        "expected_answers": ["树", "树木"],
        "semantic_hints": ["植物"],
        "choice_hints": [
          { "text": "是一种植物吗?", "score_deduction": 0.5 },
          { "text": "绿色的东西?", "score_deduction": 1.0 }
        ],
        "time_limit_seconds": 20
      }
    ],
    "scoring_rules": {
      "unprompted_correct": 1.0,
      "semantic_hint_correct": 0.5,
      "choice_hint_correct": 0.25
    }
  }
}
```

---

## 3. 前端集成方案（admin-web Vue）

### 3.1 患者端组件重构

**目标**：将 C/B 四项从 React 独立项目迁移到 Vue admin-web 中

**新增页面与组件**

| 路由 | 组件 | 职责 |
|------|------|------|
| `/p/fill/:token` | `PatientSessionView.vue` | 验证入口（已有，继续使用） |
| `/p/tasks` | `PatientTaskListView.vue` | 任务列表（已有 `PatientPortal.vue` 的功能） |
| `/p/task/:itemId/intro` | `TaskIntroView.vue` | 任务说明页 |
| `/p/task/:itemId/questionnaire` | `StructuredQuestionnaireView.vue` | A 类量表答题（复用现有 `DynamicQuestion.vue`） |
| `/p/task/:itemId/boston` | `BostonNamingView.vue` | Boston 命名任务 |
| `/p/task/:itemId/trail-making` | `TrailMakingView.vue` | STT 连线任务 |
| `/p/task/:itemId/interview` | `ScdInterviewView.vue` | SCD 对话任务 |
| `/p/task/:itemId/open-answer` | `MocaOpenAnswerView.vue` | MoCA-B 开放题任务 |
| `/p/task/:itemId/complete` | `TaskCompleteView.vue` | 完成页面 |

### 3.2 关键组件设计

#### 3.2.1 `BostonNamingView.vue`

```vue
<template>
  <div class="boston-task">
    <!-- 题号进度 -->
    <ProgressBar :current="currentItemIndex" :total="items.length" />
    
    <!-- 图片展示 -->
    <div class="image-container">
      <img :src="currentItem.image_url" :alt="`Item ${currentItemIndex + 1}`" />
      <Timer :elapsed="elapsedSeconds" :limit="currentItem.time_limit_seconds" />
    </div>
    
    <!-- 回答输入 -->
    <input v-model="userAnswer" @keyup.enter="recordAnswer" placeholder="输入您的答案" />
    <button @click="recordAnswer">确认答案</button>
    <button v-if="!hintUsed" @click="showHint">需要提示</button>
    
    <!-- 评分阶段显示 -->
    <div v-if="showPhase" class="phase-display">
      <p>{{ phaseText }}</p>
      <div class="phase-options" v-if="currentPhase === 'choice'">
        <button v-for="option in currentItem.choice_hints" :key="option.text" @click="selectChoice(option)">
          {{ option.text }}
        </button>
      </div>
    </div>
    
    <!-- 交互按钮 -->
    <div class="actions">
      <button @click="previousItem" :disabled="currentItemIndex === 0">上一题</button>
      <button @click="nextItem" :disabled="currentItemIndex === items.length - 1">下一题</button>
      <button v-if="allAnswered" @click="submitTask">完成任务</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBostonStore } from '@/stores/boston'

interface BostonAnswer {
  itemId: string
  unprompedAnswer: string
  unprompedCorrect: boolean
  hintPhaseAnswer: string | null
  choiceAnswer: string | null
  durationMs: number
  hintUsed: boolean
  currentPhase: 'unprompted' | 'semantic' | 'choice'
}

const store = useBostonStore()
const currentItemIndex = ref(0)
const userAnswer = ref('')
const hintUsed = ref(false)
const currentPhase = ref<'unprompted' | 'semantic' | 'choice'>('unprompted')
const startTime = ref<number>(0)
const answers = ref<Record<string, BostonAnswer>>({})

const items = computed(() => store.taskConfig?.items || [])
const currentItem = computed(() => items.value[currentItemIndex.value])
const elapsedSeconds = computed(() => Math.floor((Date.now() - startTime.value) / 1000))
const allAnswered = computed(() => Object.keys(answers.value).length === items.value.length)

function recordAnswer() {
  const current = answers.value[currentItem.value.id] || {
    itemId: currentItem.value.id,
    unprompedAnswer: '',
    unprompedCorrect: false,
    hintPhaseAnswer: null,
    choiceAnswer: null,
    durationMs: 0,
    hintUsed: false,
    currentPhase: 'unprompted'
  }
  
  if (currentPhase.value === 'unprompted') {
    current.unprompedAnswer = userAnswer.value
    current.unprompedCorrect = checkMatch(userAnswer.value, currentItem.value.expected_answers)
  } else if (currentPhase.value === 'semantic') {
    current.hintPhaseAnswer = userAnswer.value
  } else {
    current.choiceAnswer = userAnswer.value
  }
  
  current.durationMs = Date.now() - startTime.value
  answers.value[currentItem.value.id] = current
  userAnswer.value = ''
  
  // 自动进入下一题或下一阶段
  if (currentPhase.value === 'unprompted' && current.unprompedCorrect) {
    nextItem()
  } else if (currentPhase.value === 'unprompted' && !current.unprompedCorrect) {
    currentPhase.value = 'semantic'
  }
}

function checkMatch(answer: string, expected: string[]): boolean {
  // 实现模糊匹配逻辑
  return expected.some(exp => answer.includes(exp) || exp.includes(answer))
}

function showHint() {
  hintUsed.value = true
  if (currentPhase.value === 'unprompted') {
    currentPhase.value = 'semantic'
  }
}

async function submitTask() {
  // 构建提交数据
  const submission = {
    answers: answers.value,
    provisional_score: calculateProvisionScore(),
    metrics: { total_duration: Date.now() - startTime.value }
  }
  await store.submitTask(submission)
}

function calculateProvisionScore(): number {
  // 前端能够计算的初步分数
  let score = 0
  Object.values(answers.value).forEach((ans: BostonAnswer) => {
    if (ans.unprompedCorrect) score += 1
    else if (ans.hintPhaseAnswer) score += 0.5
    else if (ans.choiceAnswer) score += 0.25
  })
  return score
}

onMounted(() => {
  startTime.value = Date.now()
})
</script>
```

#### 3.2.2 `TrailMakingView.vue`

```vue
<template>
  <div class="trail-making-task">
    <ProgressBar :current="currentAttempt" :total="maxAttempts" label="尝试" />
    
    <svg :width="svgWidth" :height="svgHeight" class="trail-canvas">
      <!-- 背景 -->
      <rect width="100%" height="100%" fill="#f5f5f5" />
      
      <!-- 已连接的线 -->
      <line v-for="(line, idx) in drawnLines" :key="`line-${idx}`"
        :x1="line.x1" :y1="line.y1" :x2="line.x2" :y2="line.y2"
        :stroke="line.correct ? '#4CAF50' : '#f44336'" stroke-width="2" />
      
      <!-- 错误提示线 -->
      <line v-if="lastErrorLine"
        :x1="lastErrorLine.x1" :y1="lastErrorLine.y1"
        :x2="lastErrorLine.x2" :y2="lastErrorLine.y2"
        stroke="#ff6b6b" stroke-width="3" stroke-dasharray="5,5" opacity="0.7" />
      
      <!-- 节点 -->
      <g v-for="node in nodes" :key="node.id">
        <circle
          :cx="node.x" :cy="node.y" r="25"
          :fill="getNodeColor(node)" :stroke="getNodeStroke(node)" stroke-width="2"
          @click="selectNode(node)"
          class="node"
        />
        <text :x="node.x" :y="node.y" text-anchor="middle" dy="0.3em" font-size="18" font-weight="bold">
          {{ node.label }}
        </text>
        <!-- 已点击的节点显示顺序 -->
        <text v-if="nodeClickOrder.includes(node.id)" 
          :x="node.x + 20" :y="node.y - 20" fill="green" font-weight="bold">
          {{ nodeClickOrder.indexOf(node.id) + 1 }}
        </text>
      </g>
    </svg>
    
    <!-- 状态与提示 -->
    <div class="status">
      <div v-if="waitingForHint" class="hint-countdown">
        系统在搜索下一个点... {{ hintCountdown }}s
      </div>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
        <button @click="undo">撤销最后一步</button>
        <button @click="restart">重新开始</button>
      </div>
    </div>
    
    <!-- 统计信息 -->
    <div class="metrics">
      <div>用时: {{ elapsedSeconds }}s</div>
      <div>错误: {{ errorCount }}</div>
      <div>提示: {{ hintCount }}</div>
    </div>
    
    <!-- 操作按钮 -->
    <div class="actions">
      <button @click="restart">重新开始</button>
      <button @click="skipAttempt" v-if="currentAttempt < maxAttempts">跳过此尝试</button>
      <button @click="completeTask" v-if="completed">完成任务</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTrailMakingStore } from '@/stores/trail-making'

interface Node {
  id: string
  label: string
  shape: 'circle' | 'square'
  x: number
  y: number
}

interface DrawnLine {
  x1: number
  y1: number
  x2: number
  y2: number
  correct: boolean
}

const store = useTrailMakingStore()
const svgWidth = 600
const svgHeight = 500
const currentAttempt = ref(0)
const maxAttempts = 3
const nodeClickOrder = ref<string[]>([])
const drawnLines = ref<DrawnLine[]>([])
const errorCount = ref(0)
const hintCount = ref(0)
const errorMessage = ref('')
const waitingForHint = ref(false)
const hintCountdown = ref(0)
const startTime = ref<number>(0)

const nodes = computed(() => store.taskConfig?.nodes || [])
const correctSequence = computed(() => store.taskConfig?.correctSequence || [])
const completed = computed(() => nodeClickOrder.value.length === correctSequence.value.length)
const elapsedSeconds = computed(() => Math.floor((Date.now() - startTime.value) / 1000))

function getNodeColor(node: Node): string {
  if (!nodeClickOrder.value.includes(node.id)) return '#fff'
  return nodeClickOrder.value.indexOf(node.id) === nodeClickOrder.value.length - 1 ? '#fff59d' : '#4CAF50'
}

function getNodeStroke(node: Node): string {
  const isNext = nodeClickOrder.value.length < correctSequence.value.length && 
                 correctSequence.value[nodeClickOrder.value.length] === node.id
  return isNext ? '#2196F3' : '#ccc'
}

function selectNode(node: Node) {
  const expectedNextId = correctSequence.value[nodeClickOrder.value.length]
  
  if (node.id === expectedNextId) {
    nodeClickOrder.value.push(node.id)
    
    // 绘制连接线
    if (nodeClickOrder.value.length > 1) {
      const prevNode = nodes.value.find(n => n.id === nodeClickOrder.value[nodeClickOrder.value.length - 2])
      drawnLines.value.push({
        x1: prevNode.x,
        y1: prevNode.y,
        x2: node.x,
        y2: node.y,
        correct: true
      })
    }
    
    errorMessage.value = ''
  } else {
    // 错误处理
    errorCount.value++
    const wrongNode = node
    const correctNode = nodes.value.find(n => n.id === expectedNextId)
    
    errorMessage.value = `选错了！正确答案是 ${correctNode.label}`
    lastErrorLine.value = {
      x1: wrongNode.x,
      y1: wrongNode.y,
      x2: correctNode.x,
      y2: correctNode.y,
      correct: false
    }
    
    // 3 秒后清除错误显示
    setTimeout(() => {
      errorMessage.value = ''
      lastErrorLine.value = null
    }, 3000)
  }
}

function restart() {
  nodeClickOrder.value = []
  drawnLines.value = []
  errorCount.value = 0
  hintCount.value = 0
  errorMessage.value = ''
  startTime.value = Date.now()
  currentAttempt.value++
}

async function completeTask() {
  const submission = {
    attempts: [{
      sequence: nodeClickOrder.value,
      errorCount: errorCount.value,
      hintCount: hintCount.value,
      durationMs: (Date.now() - startTime.value) * 1000,
      completed: true
    }],
    metrics: {
      total_duration: Date.now() - startTime.value,
      error_count: errorCount.value,
      hint_count: hintCount.value
    }
  }
  await store.submitTask(submission)
}

onMounted(() => {
  startTime.value = Date.now()
})
</script>
```

---

## 4. 后端实现方案（FastAPI）

### 4.1 新增路由与服务

**新路由 `/api/v1/patient-session/tasks/{item_id}/events`**
```python
@router.post("/patient-session/tasks/{item_id}/events")
def record_event(
    item_id: int,
    event: EventInput,  # {event_type, timestamp, data}
    identity: PatientIdentity = Depends(patient_identity),
    db: Session = Depends(get_db)
):
    """记录交互事件（答题过程中的每个操作）"""
    item = item_for_identity(item_id, identity, db)
    response = item.response
    
    event_record = TaskEvent(
        response_id=response.id,
        event_type=event.event_type,
        timestamp=event.timestamp,
        data=event.data
    )
    db.add(event_record)
    db.commit()
    return {"recorded": True}
```

### 4.2 计分服务重构

**新增文件 `server/app/services/ai_scoring.py`**

```python
from datetime import datetime
from typing import Optional
import httpx
import json
from sqlalchemy.orm import Session
from ..models import Response, AICandidate, TaskEvent

class RagService:
    """RAG 知识包检索服务"""
    
    def __init__(self):
        self.knowledge_base = {}  # 加载量表规则、评分条款、同义词等
    
    def get_scoring_rules(self, task_type: str, version: str) -> dict:
        """获取任务的评分规则和证据"""
        # 从版本化知识包中检索
        return self.knowledge_base.get(f"{task_type}:{version}", {})
    
    def search_examples(self, task_type: str, query: str, limit: int = 3) -> list[dict]:
        """关键词检索评分示例和同义词"""
        pass

class AIScoreGenerator:
    """AI 辅助评分生成器"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://api.deepseek.com/v1"
        self.rag = RagService()
    
    async def generate_candidate_score(
        self,
        response: Response,
        task_type: str,
        task_config: dict,
        db: Session
    ) -> dict:
        """为 Boston、SCD、MoCA-B 等任务生成候选分"""
        
        if task_type == "boston_naming":
            return await self._score_boston(response, task_config, db)
        elif task_type == "scd_interview":
            return await self._score_scd(response, task_config, db)
        elif task_type == "moca_open_answer":
            return await self._score_moca_open(response, task_config, db)
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _score_boston(
        self,
        response: Response,
        task_config: dict,
        db: Session
    ) -> dict:
        """Boston 命名评分
        
        策略：
        1. 未提示答案：直接匹配 expected_answers + 同义词库
        2. 语义提示答案：在知识包中查找评分规则
        3. 选项提示答案：查询预定义答案表
        4. 模糊答案：调用 LLM 判断是否合理
        """
        
        scoring_rules = self.rag.get_scoring_rules("boston_naming", "v1")
        answers = response.answers_json
        scores = []
        evidence_refs = []
        
        for item_id, answer_data in answers.items():
            item_config = next((i for i in task_config["items"] if i["id"] == item_id), None)
            if not item_config:
                continue
            
            # 判断完全匹配
            if self._exact_match(answer_data["answer"], item_config["expected_answers"]):
                scores.append({
                    "item_id": item_id,
                    "score": 1.0,
                    "method": "exact_match"
                })
                evidence_refs.append(f"boston:{item_id}:unprompted_correct")
                continue
            
            # 判断语义提示答案
            if answer_data.get("hint_phase_answer"):
                hint_score = await self._llm_evaluate_hint_answer(
                    answer_data["hint_phase_answer"],
                    item_config,
                    scoring_rules
                )
                scores.append({
                    "item_id": item_id,
                    "score": hint_score,
                    "method": "semantic_hint"
                })
                evidence_refs.append(f"boston:{item_id}:semantic_hint_score:{hint_score}")
                continue
            
            # 选项提示答案（规则可确定）
            if answer_data.get("choice_hint_index") is not None:
                choice_score = item_config["choice_hints"][answer_data["choice_hint_index"]]["score_deduction"]
                scores.append({
                    "item_id": item_id,
                    "score": choice_score,
                    "method": "choice_hint"
                })
                evidence_refs.append(f"boston:{item_id}:choice_hint:{answer_data['choice_hint_index']}")
                continue
            
            # 无回答
            scores.append({
                "item_id": item_id,
                "score": 0.0,
                "method": "no_answer"
            })
        
        total_score = sum(s["score"] for s in scores)
        
        return {
            "task_type": "boston_naming",
            "candidate_score": total_score,
            "explanation": f"Boston 命名：{total_score}/{len(scores)} 项正确或部分正确",
            "evidence_references": evidence_refs,
            "details": scores,
            "status": "ready"
        }
    
    async def _score_scd(
        self,
        response: Response,
        task_config: dict,
        db: Session
    ) -> dict:
        """SCD 访谈评分
        
        策略：
        1. 维持访谈状态机，确保必问题都被询问
        2. 提取用户回答中的关键信息（时间、严重度、影响）
        3. 不生成无依据的总分；标为"待复核"或按维度给候选分
        """
        
        # 从交互事件中重建访谈对话
        events = db.query(TaskEvent).filter(TaskEvent.response_id == response.id).all()
        dialogue = [json.loads(e.data) for e in events if e.event_type == "llm_message"]
        
        # 调用 LLM 提取信息
        prompt = f"""
        请根据以下患者访谈对话，提取 SCD 评估的关键信息：
        - 记忆问题的时间点（何时开始）
        - 主观严重度（1-10 分）
        - 对日常生活的影响
        - 相关背景信息
        
        对话：
        {json.dumps(dialogue, ensure_ascii=False, indent=2)}
        
        请返回 JSON 格式：
        {{
          "onset_timing": "...",
          "severity": 5,
          "functional_impact": "...",
          "background_info": "...",
          "candidate_score": null,
          "recommendation": "该患者信息 [充分|不充分] 用于评分，建议人工复核"
        }}
        """
        
        async with httpx.AsyncClient() as client:
            response_text = await self._call_llm(prompt)
        
        result = json.loads(response_text)
        
        return {
            "task_type": "scd_interview",
            "candidate_score": result.get("candidate_score"),
            "explanation": result.get("recommendation"),
            "evidence_references": [f"scd:dialogue:{len(dialogue)}_exchanges"],
            "details": result,
            "status": "pending" if result.get("candidate_score") is None else "ready"
        }
    
    async def _llm_evaluate_hint_answer(
        self,
        answer: str,
        item_config: dict,
        scoring_rules: dict
    ) -> float:
        """调用 LLM 判断语义提示下的答案是否合理"""
        
        prompt = f"""
        题目：{item_config['expected_answers']}
        提示：{item_config['semantic_hints']}
        患者回答：{answer}
        
        评分规则：{json.dumps(scoring_rules)}
        
        请判断患者的回答是否接受，并给出 0.5 分（接受）或 0.0 分（不接受）。
        返回 JSON: {{"score": 0.5, "reason": "..."}}
        """
        
        response_text = await self._call_llm(prompt)
        result = json.loads(response_text)
        return result.get("score", 0.0)
    
    async def _call_llm(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

async def process_ai_scoring_task(response: Response, db: Session):
    """后台任务：处理 AI 评分"""
    generator = AIScoreGenerator(api_key=settings.deepseek_api_key)
    
    result = await generator.generate_candidate_score(
        response,
        response.task_type,
        response.task_config_ref,
        db
    )
    
    candidate = AICandidate(
        response_id=response.id,
        task_type=response.task_type,
        candidate_score=result.get("candidate_score"),
        explanation=result.get("explanation"),
        evidence_references=result.get("evidence_references", []),
        model_name="deepseek-flash",
        prompt_version="v1",
        status=result.get("status", "pending")
    )
    db.add(candidate)
    db.commit()
```

### 4.3 提交与计分流程

**修改 `/api/v1/patient-session/tasks/{item_id}/submit`**

```python
@router.post("/patient-session/tasks/{item_id}/submit")
async def submit_task(
    item_id: int,
    payload: SubmitInput,
    idempotency_key: str = Header(None),
    identity: PatientIdentity = Depends(patient_identity),
    db: Session = Depends(get_db)
):
    """提交任务答案并触发评分"""
    
    item = item_for_identity(item_id, identity, db)
    response = item.response
    
    # 幂等检查
    existing = db.scalar(select(Assessment).where(Assessment.assignment_item_id == item_id))
    if idempotency_key and (existing_resp := db.scalar(...)):
        return existing_resp.to_dict()
    
    # 保存响应
    response.status = "submitted"
    response.answers_json = payload.answers
    response.submitted_at = utcnow()
    response.duration_seconds = ceil((response.submitted_at - response.started_at).total_seconds())
    db.commit()
    
    # 根据任务类型进行计分
    task_type = response.task_type or "structured_questionnaire"
    
    if task_type in ["structured_questionnaire"]:
        # 规则计分（GDS、ESS 等）
        scores = score_questionnaire(response, item.questionnaire_version, db)
        assessment = Assessment(
            assignment_item_id=item_id,
            patient_id=identity.patient_id,
            doctor_id=item.assignment.doctor_id,
            questionnaire_code=item.questionnaire_version.template.code,
            total_score=scores.get("total_score"),
            dimension_scores=scores.get("dimension_scores", {}),
            risk_level=scores.get("risk_level", "unknown"),
            review_status="auto"
        )
        db.add(assessment)
        db.commit()
        
        return assessment.to_dict()
    
    else:
        # AI 评分（Boston、SCD、MoCA-B）
        # 1. 启动后台任务
        background_tasks.add_task(process_ai_scoring_task, response, db)
        
        # 2. 返回"待评分"状态
        return {
            "id": response.id,
            "status": "pending_ai_scoring",
            "message": "正在进行 AI 评分分析，请稍候..."
        }
```

---

## 5. 医生端复核界面

### 5.1 新增医生复核页面

**路由**：`/admin/assessments/:assessmentId/review`

**功能**：
- 查看患者原始答案和交互事件
- 查看 AI 生成的候选分及证据引用
- 修改分数或标记为"需要人工判断"
- 记录复核意见

```vue
<template>
  <div class="assessment-review">
    <!-- 患者信息 -->
    <PatientInfo :patient="assessment.patient" />
    
    <!-- 原始答案与交互事件 -->
    <section class="original-data">
      <h3>原始答案记录</h3>
      <InteractionTimeline :events="taskEvents" />
    </section>
    
    <!-- AI 候选分 -->
    <section class="ai_candidate" v-if="aiCandidate">
      <h3>AI 分析结果</h3>
      <div class="candidate-score">
        <div class="score-display">
          <div class="number">{{ aiCandidate.candidate_score || '待评分' }}</div>
          <div class="status" :class="aiCandidate.status">{{ aiCandidate.status }}</div>
        </div>
      </div>
      
      <div class="explanation">{{ aiCandidate.explanation }}</div>
      
      <!-- 证据引用 -->
      <div class="evidence">
        <h4>评分依据</h4>
        <ul>
          <li v-for="ref in aiCandidate.evidence_references" :key="ref">
            <code>{{ ref }}</code>
            <a href="#" @click.prevent="openEvidenceDetail(ref)">查看详情</a>
          </li>
        </ul>
      </div>
    </section>
    
    <!-- 医生确认 -->
    <section class="confirmation">
      <h3>医生确认</h3>
      <div class="form">
        <label>确认分数</label>
        <input v-model="confirmScore" type="number" />
        
        <label>复核意见</label>
        <textarea v-model="confirmNotes" placeholder="记录您的复核意见或修改原因"></textarea>
        
        <div class="actions">
          <button @click="confirmScore">确认</button>
          <button @click="markForManualReview">标记为需人工复核</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
// 实现代码
</script>
```

---

## 6. 任务类型与数据结构映射

### 6.1 GDS-15（A 类结构化）

| 属性 | 值 |
|------|-----|
| `task_type` | `structured_questionnaire` |
| `scoring_strategy` | `metadata_sum` |
| 前端能力 | 计算分数、保存草稿 |
| 后端能力 | 最终计分、风险分层 |
| 医生复核 | 可选（自动评分置信度高） |

**答卷结构**
```json
{
  "gds_1": "yes",
  "gds_2": "no",
  "gds_3": "yes",
  ...
}
```

### 6.2 Boston 命名（B 类）

| 属性 | 值 |
|------|-----|
| `task_type` | `boston_naming` |
| `scoring_strategy` | `ai_candidate` |
| 前端能力 | 记录回答、时长、提示使用 |
| 后端能力 | 候选分（通过 RAG + LLM） |
| 医生复核 | 必须（需确认同义词） |

**答卷结构**
```json
{
  "boston_01": {
    "unprompted_answer": "树",
    "unprompted_correct": true,
    "hint_phase_answer": null,
    "choice_hint_index": null,
    "duration_ms": 5230,
    "hint_used": false
  },
  "boston_02": {
    "unprompted_answer": "笔写的",
    "unprompted_correct": false,
    "hint_phase_answer": "用来书写",
    "choice_hint_index": null,
    "duration_ms": 8100,
    "hint_used": true
  },
  ...
}
```

### 6.3 STT 连线（B 类）

| 属性 | 值 |
|------|-----|
| `task_type` | `trail_making` |
| `mode` | `A \| B` |
| 前端能力 | 记录连接序列、错误、时长 |
| 后端能力 | 根据规则计算时间/错误分 |
| 医生复核 | 可选 |

**答卷结构**
```json
{
  "attempts": [
    {
      "sequence": ["1", "A", "2", "B", "3", "C"],
      "error_count": 1,
      "hint_count": 0,
      "duration_ms": 42180,
      "completed": true
    }
  ]
}
```

### 6.4 SCD 访谈（C 类）

| 属性 | 值 |
|------|-----|
| `task_type` | `scd_interview` |
| 前端能力 | 对话界面、消息保存 |
| 后端能力 | 候选分（结构化访谈分析） |
| 医生复核 | 必须 |

**答卷结构**
```json
{
  "messages": [
    {"role": "ai", "content": "..."},
    {"role": "patient", "content": "..."},
    ...
  ],
  "extracted_fields": {
    "onset_timing": "半年前开始",
    "severity": 6,
    "functional_impact": "经常忘记放东西的位置"
  }
}
```

---

## 7. 实现阶段与时间表

### 阶段 1：后端数据模型与 API（1 周）

- [ ] 新增 `TaskEvent`、`AICandidate` 表
- [ ] 扩展 `Response` 表字段
- [ ] 实现 `/patient-session/tasks/{item_id}/events` 路由
- [ ] 重构计分服务，分离规则计分与 AI 候选分

### 阶段 2：前端迁移与集成（2 周）

- [ ] 迁移 C/B 四项组件到 Vue admin-web
- [ ] 实现任务路由与菜单
- [ ] 实现交互事件记录
- [ ] 集成医生复核界面

### 阶段 3：AI 评分与 RAG（1.5 周）

- [ ] 建立版本化知识包（量表规则、同义词库、评分范例）
- [ ] 实现 `RagService` 和 `AIScoreGenerator`
- [ ] 实现后台任务处理
- [ ] 本地云 API 联调与验证

### 阶段 4：完整流程验证与优化（1 周）

- [ ] 端到端联调（派发 → 作答 → 评分 → 复核）
- [ ] 边界情况和错误处理
- [ ] 性能优化与日志完善
- [ ] 浏览器与手机端适配

---

## 8. 核心代码位置与扩展点

### 文件结构

```
server/
├── app/
│   ├── models.py  ← 新增 TaskEvent、AICandidate
│   ├── services/
│   │   ├── scoring.py  ← 修改：分离规则计分
│   │   ├── ai_scoring.py  ← 新增：RAG 与 AI 评分
│   │   └── rag.py  ← 新增：知识包检索
│   └── routers/
│       └── patient_session.py  ← 新增 /events 路由、修改 /submit
│
admin-web/
└── src/
    ├── views/
    │   └── patient/
    │       ├── BostonNamingView.vue  ← 新增
    │       ├── TrailMakingView.vue  ← 新增
    │       ├── ScdInterviewView.vue  ← 新增
    │       ├── MocaOpenAnswerView.vue  ← 新增
    │       └── AssessmentReviewView.vue  ← 新增
    ├── stores/
    │   ├── boston.ts  ← 新增
    │   ├── trail-making.ts  ← 新增
    │   └── ...
    └── utils/
        └── task-renderer.ts  ← 根据 task_type 渲染组件
```

---

## 9. 验收标准

### 9.1 功能完整性

- [ ] 六项任务均可通过医生派发 → 患者作答 → 后端评分 → 医生复核的完整流程
- [ ] 原始答案、交互事件、指标均被完整保存
- [ ] 规则可确定的结果（GDS、ESS）由程序正确计分
- [ ] 需要理解的结果（Boston、SCD、MoCA-B）由 AI 生成候选分，医生确认

### 9.2 数据准确性

- [ ] Boston 30 张图片逐一对应原表，同义词库完整
- [ ] STT 节点坐标、形状、顺序正确
- [ ] GDS 正反向题、ESS 边界情况计分正确
- [ ] SCD 访谈状态机完整，不漏必问题

### 9.3 AI 集成质量

- [ ] 本地 DeepSeek 联调成功，以虚拟回答完成真实模型测试
- [ ] 候选分范围合理，证据引用有效
- [ ] 模型失败、超时不丢答案，支持重试

### 9.4 兼容性与回归

- [ ] 现有后端、前端、浏览器可正常运行
- [ ] 旧数据库可升级（Alembic 迁移）
- [ ] 旧问卷继续使用普通答题器
- [ ] 移动端与桌面端都可操作

---

## 10. 对接负责人指南

### 10.1 关键决策点

1. **知识包版本管理**：选择文件（JSON）+ 数据库（SQL）混合还是纯数据库？
   - 建议：文件管理（便于版本控制）+ 应用启动加载，必要时再迁移数据库

2. **AI 模型选择**：深度搜索（DeepSeek）vs 其他模型？
   - 当前方案使用 DeepSeek Flash，可通过 `settings.py` 切换模型

3. **医生复核工作流**：所有 AI 结果都必须复核，还是置信度高的自动确认？
   - 当前方案：Boston、SCD、MoCA-B 必须复核；GDS、ESS 自动确认

### 10.2 文件清单

#### 需要新建的文件
- `server/app/services/ai_scoring.py` — AI 评分核心
- `server/app/services/rag.py` — 知识包检索
- `admin-web/src/views/patient/BostonNamingView.vue` 等 4 个任务页面
- `admin-web/src/stores/boston.ts` 等 4 个状态管理
- `docs/knowledge-base/boston-v1.json` — Boston 知识包
- `docs/knowledge-base/scd-v1.json` — SCD 知识包

#### 需要修改的文件
- `server/app/models.py` — 新增表、扩展 Response
- `server/app/routers/patient_session.py` — 新增 /events、修改 /submit
- `server/app/services/scoring.py` — 分离规则计分逻辑
- `admin-web/src/views/patient/PatientPortal.vue` — 路由跳转到各任务页面
- `admin-web/src/router.ts` — 新增患者端路由
- `server/alembic/versions/` — 数据库迁移脚本

---

## 11. 常见问题与解决方案

### Q1：前端如何区分是哪种任务类型？
**A**：从问卷 schema 的 `task_type` 字段判断，使用动态组件渲染。

### Q2：Boston 标准答案保存在哪里？
**A**：保存在版本化知识包（JSON 文件或数据库），**不发送到患者端**。后端评分时使用。

### Q3：AI 评分失败怎么办？
**A**：响应标记为 `status: 'invalid'`，前端重试或医生手工评分。

### Q4：如何支持离线填写后同步？
**A**：前端本地缓存答案，恢复网络后以幂等提交同步。

---

## 12. 后续扩展点

- 支持语音输入（STT）的 SCD 访谈
- 知识包的管理后台（预览、版本对比、发布）
- 多语言支持（当前中文）
- 数据导出与统计报告
- 与电子病历（EMR）系统集成

