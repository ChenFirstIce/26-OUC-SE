// SCD 主观认知下降结构性问卷完整数据模型
// 数据来源：仓库根目录 scd_structured_interview.json

import sourceData from '../../../scd_structured_interview.json'

export type ScdQuestionType = 'radio' | 'text'

export type ScdFollowUpQuestion = {
  question: string
  type?: ScdQuestionType
  options?: string[]
  values?: number[]
  responseFormat?: string
}

export type ScdCognitiveDomain = {
  id: string
  label: string
  initialQuestion: string
  mainQuestions: string[]
  followUpQuestions: Record<string, ScdFollowUpQuestion>
}

export type ScdInformantQuestion = {
  id: string
  question: string
  followUpIfYes: string
}

export type ScdAdditionalQuestion = {
  id: string
  question: string
  options: string[]
}

export type ScdQuestionnaireData = {
  sourceSection: string
  screeningPrompt: string
  branchRule: string
  cognitiveDomains: ScdCognitiveDomain[]
  informantQuestionnaire: ScdInformantQuestion[]
  informantOnsetOptions: {
    question: string
    options: string[]
    values: number[]
  }
  informantMeta: {
    availabilityOptions: string[]
    relationshipOptions: string[]
  }
  additionalInformation: ScdAdditionalQuestion[]
}

export const scdQuestionnaire = sourceData as ScdQuestionnaireData

// 认知域标识映射
export const cognitiveDomainLabels: Record<string, string> = {
  memory: '记忆力',
  language: '语言 / 找词困难',
  planning: '组织能力 / 计划能力',
  attention: '注意力 / 专心',
  other_cognition: '其他认知功能方面',
}

// 知情者关系选项
export const informantRelationships = scdQuestionnaire.informantMeta.relationshipOptions

// 知情者可用性选项
export const informantAvailability = scdQuestionnaire.informantMeta.availabilityOptions
