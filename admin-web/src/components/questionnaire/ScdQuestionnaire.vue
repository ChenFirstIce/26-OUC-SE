<template>
  <div class="scd-questionnaire">
    <div class="questionnaire-header">
      <h2>{{ scdQuestionnaire.sourceSection }}</h2>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${overallProgress}%` }"></div>
      </div>
      <p class="progress-text">进度：{{ currentStep }}/{{ totalSteps }}</p>
    </div>

    <!-- 初始筛查阶段 -->
    <div v-if="phase === 'screening'" class="phase-container">
      <h3>{{ scdQuestionnaire.screeningPrompt }}</h3>
      <div class="domain-grid">
        <button
          v-for="domain in scdQuestionnaire.cognitiveDomains"
          :key="domain.id"
          @click="selectDomain(domain.id)"
          :class="['domain-button', { selected: selectedDomains.includes(domain.id) }]"
        >
          {{ domain.label }}
        </button>
      </div>
      <div class="actions">
        <button @click="proceedToQuestioning" class="primary-button" :disabled="selectedDomains.length === 0">
          继续问卷
        </button>
      </div>
    </div>

    <!-- 认知域问卷阶段 -->
    <div v-else-if="phase === 'questioning'" class="phase-container">
      <div v-if="currentDomainIndex < selectedDomains.length" class="domain-section">
        <h3>{{ currentDomain.label }}</h3>

        <!-- 主要问题 -->
        <div v-for="(question, qIndex) in currentDomain.mainQuestions" :key="`main-${qIndex}`" class="question-block">
          <p class="question-text">{{ question }}</p>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" :name="`main-${currentDomain.id}-${qIndex}`" :value="false" v-model="mainAnswers[currentDomain.id]" />
              <span>否</span>
            </label>
            <label class="radio-label">
              <input type="radio" :name="`main-${currentDomain.id}-${qIndex}`" :value="true" v-model="mainAnswers[currentDomain.id]" />
              <span>是</span>
            </label>
          </div>
        </div>

        <!-- 追加问题（仅当主要问题回答"是"时显示） -->
        <div v-if="mainAnswers[currentDomain.id] === true" class="follow-up-section">
          <div v-for="(followUp, key) in currentDomain.followUpQuestions" :key="`follow-${key}`" class="question-block">
            <p class="question-text">{{ followUp.question }}</p>

            <!-- 单选题 -->
            <div v-if="!followUp.type || followUp.type === 'radio'" class="radio-group">
              <label v-for="(option, optIndex) in followUp.options" :key="optIndex" class="radio-label">
                <input
                  type="radio"
                  :name="`follow-${currentDomain.id}-${key}`"
                  :value="followUp.values?.[optIndex]"
                  v-model="followUpAnswers[currentDomain.id][key]"
                />
                <span>{{ option }}</span>
              </label>
            </div>

            <!-- 文本输入 -->
            <div v-else-if="followUp.type === 'text'" class="text-input">
              <input
                type="text"
                v-model="followUpAnswers[currentDomain.id][key]"
                :placeholder="followUp.responseFormat"
                class="text-field"
              />
            </div>
          </div>
        </div>

        <div class="actions">
          <button @click="previousDomain" class="secondary-button" v-if="currentDomainIndex > 0">
            上一题
          </button>
          <button @click="nextDomain" class="primary-button">
            {{ currentDomainIndex < selectedDomains.length - 1 ? '下一题' : '完成受访者问卷' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 知情者问卷阶段 -->
    <div v-else-if="phase === 'informant'" class="phase-container">
      <h3>知情者问卷</h3>

      <!-- 知情者可用性检查 -->
      <div v-if="!informantAvailable" class="question-block">
        <p class="question-text">是否有知情者可以提供信息？</p>
        <div class="radio-group">
          <label class="radio-label">
            <input type="radio" name="informant-check" :value="true" v-model="informantAvailable" />
            <span>有</span>
          </label>
          <label
            v-for="unavailOption in scdQuestionnaire.informantMeta.availabilityOptions"
            :key="unavailOption"
            class="radio-label"
          >
            <input type="radio" name="informant-check" :value="unavailOption" v-model="informantUnavailableReason" @change="markInformantUnavailable" />
            <span>{{ unavailOption }}</span>
          </label>
        </div>
      </div>

      <!-- 知情者关系 -->
      <div v-if="informantAvailable === true" class="informant-section">
        <div class="question-block">
          <p class="question-text">知情者与受访者的关系</p>
          <div class="radio-group">
            <label
              v-for="relation in scdQuestionnaire.informantMeta.relationshipOptions"
              :key="relation"
              class="radio-label"
            >
              <input type="radio" name="informant-relation" :value="relation" v-model="informantRelation" />
              <span>{{ relation }}</span>
            </label>
          </div>
        </div>

        <!-- 知情者问题 -->
        <div v-for="question in scdQuestionnaire.informantQuestionnaire" :key="question.id" class="question-block">
          <p class="question-text">{{ question.question }}</p>
          <div class="radio-group">
            <label class="radio-label">
              <input type="radio" :name="question.id" :value="false" v-model="informantAnswers[question.id]" />
              <span>否</span>
            </label>
            <label class="radio-label">
              <input type="radio" :name="question.id" :value="true" v-model="informantAnswers[question.id]" />
              <span>是</span>
            </label>
          </div>

          <!-- 如果回答"是"，询问开始时间 -->
          <div v-if="informantAnswers[question.id] === true" class="follow-up-indent">
            <p class="question-text">{{ question.followUpIfYes }}</p>
            <div class="radio-group">
              <label
                v-for="(option, index) in scdQuestionnaire.informantOnsetOptions.options"
                :key="index"
                class="radio-label"
              >
                <input
                  type="radio"
                  :name="`${question.id}-onset`"
                  :value="scdQuestionnaire.informantOnsetOptions.values[index]"
                  v-model="informantOnsets[question.id]"
                />
                <span>{{ option }}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="actions">
        <button @click="phase = 'questioning'; currentDomainIndex = selectedDomains.length - 1" class="secondary-button">
          返回
        </button>
        <button @click="proceedToAdditional" class="primary-button">
          继续补充信息
        </button>
      </div>
    </div>

    <!-- 补充信息阶段 -->
    <div v-else-if="phase === 'additional'" class="phase-container">
      <h3>补充信息</h3>

      <div v-for="question in scdQuestionnaire.additionalInformation" :key="question.id" class="question-block">
        <p class="question-text">{{ question.question }}</p>
        <div class="radio-group">
          <label v-for="option in question.options" :key="option" class="radio-label">
            <input type="radio" :name="question.id" :value="option" v-model="additionalAnswers[question.id]" />
            <span>{{ option }}</span>
          </label>
        </div>
      </div>

      <div class="actions">
        <button @click="phase = 'informant'" class="secondary-button">
          返回
        </button>
        <button @click="submitQuestionnaire" class="primary-button" :disabled="busy">
          {{ busy ? '提交中...' : '提交问卷' }}
        </button>
      </div>
    </div>

    <!-- 完成阶段 -->
    <div v-else-if="phase === 'completed'" class="phase-container completion-message">
      <div class="completion-icon">✓</div>
      <h3>问卷已完成</h3>
      <p>感谢您完成 SCD 结构性问卷。</p>
      <button @click="emit('complete')" class="primary-button">返回</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { scdQuestionnaire, type ScdCognitiveDomain } from '../../data/scd-questionnaire'
import { ElMessage } from 'element-plus'

const props = defineProps<{ task: any }>()
const emit = defineEmits<{ complete: []; back: [] }>()

type Phase = 'screening' | 'questioning' | 'informant' | 'additional' | 'completed'

const phase = ref<Phase>('screening')
const selectedDomains = ref<string[]>([])
const currentDomainIndex = ref(0)
const busy = ref(false)

// 受访者答案
const mainAnswers = ref<Record<string, boolean | null>>({})
const followUpAnswers = ref<Record<string, Record<string, any>>>({})

// 知情者信息
const informantAvailable = ref<boolean | null>(null)
const informantUnavailableReason = ref<string>('')
const informantRelation = ref<string>('')
const informantAnswers = ref<Record<string, boolean | null>>({})
const informantOnsets = ref<Record<string, number | null>>({})

// 补充信息
const additionalAnswers = ref<Record<string, string>>({})

// 初始化答案结构
scdQuestionnaire.cognitiveDomains.forEach(domain => {
  mainAnswers.value[domain.id] = null
  followUpAnswers.value[domain.id] = {}
  Object.keys(domain.followUpQuestions).forEach(key => {
    followUpAnswers.value[domain.id][key] = null
  })
})

scdQuestionnaire.informantQuestionnaire.forEach(q => {
  informantAnswers.value[q.id] = null
  informantOnsets.value[q.id] = null
})

scdQuestionnaire.additionalInformation.forEach(q => {
  additionalAnswers.value[q.id] = ''
})

const currentDomain = computed<ScdCognitiveDomain>(() => {
  const domainId = selectedDomains.value[currentDomainIndex.value]
  return scdQuestionnaire.cognitiveDomains.find(d => d.id === domainId)!
})

const totalSteps = computed(() => {
  let steps = 1 // screening
  steps += selectedDomains.value.length // questioning
  steps += 1 // informant
  steps += 1 // additional
  return steps
})

const currentStep = computed(() => {
  if (phase.value === 'screening') return 1
  if (phase.value === 'questioning') return 1 + currentDomainIndex.value + 1
  if (phase.value === 'informant') return 1 + selectedDomains.value.length + 1
  if (phase.value === 'additional') return 1 + selectedDomains.value.length + 2
  if (phase.value === 'completed') return totalSteps.value
  return 1
})

const overallProgress = computed(() => (currentStep.value / totalSteps.value) * 100)

function selectDomain(domainId: string) {
  const index = selectedDomains.value.indexOf(domainId)
  if (index > -1) {
    selectedDomains.value.splice(index, 1)
  } else {
    selectedDomains.value.push(domainId)
  }
}

function proceedToQuestioning() {
  if (selectedDomains.value.length === 0) {
    ElMessage.warning('请至少选择一个认知域')
    return
  }
  phase.value = 'questioning'
  currentDomainIndex.value = 0
}

function nextDomain() {
  if (currentDomainIndex.value < selectedDomains.value.length - 1) {
    currentDomainIndex.value++
  } else {
    phase.value = 'informant'
  }
}

function previousDomain() {
  if (currentDomainIndex.value > 0) {
    currentDomainIndex.value--
  }
}

function markInformantUnavailable() {
  informantAvailable.value = false
}

function proceedToAdditional() {
  phase.value = 'additional'
}

async function submitQuestionnaire() {
  busy.value = true

  try {
    const results = {
      selectedDomains: selectedDomains.value,
      mainAnswers: mainAnswers.value,
      followUpAnswers: followUpAnswers.value,
      informant: {
        available: informantAvailable.value,
        unavailableReason: informantUnavailableReason.value,
        relation: informantRelation.value,
        answers: informantAnswers.value,
        onsets: informantOnsets.value,
      },
      additionalInformation: additionalAnswers.value,
      completedAt: new Date().toISOString(),
    }

    // TODO: 集成到后端 API
    console.log('SCD Questionnaire Results:', results)

    ElMessage.success('问卷提交成功')
    phase.value = 'completed'
  } catch (error) {
    ElMessage.error('提交失败，请重试')
    console.error(error)
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.scd-questionnaire {
  padding: 2rem;
  max-width: 56rem;
  margin: 0 auto;
}

.questionnaire-header {
  margin-bottom: 2rem;
}

.questionnaire-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #1E2636;
}

.progress-bar {
  height: 0.5rem;
  background: #E5E7EB;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3B6DFF 0%, #6EE7B7 100%);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: #6B7280;
}

.phase-container {
  background: #FFFFFF;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.phase-container h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #1E2636;
}

.domain-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.domain-button {
  padding: 1rem 1.5rem;
  border: 2px solid #E5E7EB;
  border-radius: 0.75rem;
  background: #FFFFFF;
  color: #374151;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.domain-button:hover {
  border-color: #3B6DFF;
  background: #EFF6FF;
}

.domain-button.selected {
  border-color: #3B6DFF;
  background: #3B6DFF;
  color: #FFFFFF;
}

.domain-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.question-block {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.question-text {
  font-size: 1rem;
  font-weight: 500;
  color: #1F2937;
  line-height: 1.5;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid #E5E7EB;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.radio-label:hover {
  background: #F9FAFB;
  border-color: #3B6DFF;
}

.radio-label input[type="radio"] {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.radio-label span {
  font-size: 0.9375rem;
  color: #374151;
}

.follow-up-section {
  margin-left: 1.5rem;
  padding-left: 1.5rem;
  border-left: 3px solid #3B6DFF;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.follow-up-indent {
  margin-left: 1.5rem;
  margin-top: 0.75rem;
  padding-left: 1rem;
  border-left: 2px solid #E5E7EB;
}

.text-input {
  display: flex;
}

.text-field {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #D1D5DB;
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  transition: all 0.2s ease;
}

.text-field:focus {
  outline: none;
  border-color: #3B6DFF;
  box-shadow: 0 0 0 3px rgba(59, 109, 255, 0.1);
}

.informant-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  justify-content: flex-end;
}

.primary-button {
  padding: 0.75rem 2rem;
  background: #3B6DFF;
  color: #FFFFFF;
  border: none;
  border-radius: 999px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-button:hover:not(:disabled) {
  background: #2952E0;
  transform: translateY(-1px);
}

.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary-button {
  padding: 0.75rem 2rem;
  background: #FFFFFF;
  color: #374151;
  border: 1px solid #D1D5DB;
  border-radius: 999px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.secondary-button:hover {
  background: #F9FAFB;
  border-color: #9CA3AF;
}

.completion-message {
  text-align: center;
  padding: 3rem 2rem;
}

.completion-icon {
  width: 4rem;
  height: 4rem;
  margin: 0 auto 1.5rem;
  background: #6EE7B7;
  color: #FFFFFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: bold;
}

.completion-message h3 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: #1E2636;
}

.completion-message p {
  font-size: 1rem;
  color: #6B7280;
  margin-bottom: 2rem;
}
</style>