<script setup lang="ts">
import { computed } from 'vue'
const props=defineProps<{question:any; modelValue:any}>();const emit=defineEmits(['update:modelValue'])
const value=computed({get:()=>props.modelValue,set:v=>emit('update:modelValue',v)})
</script>
<template><div class="question-block"><label class="question-label"><span v-if="question.required" class="required">*</span>{{question.label}}</label><p v-if="question.help" class="question-help">{{question.help}}</p>
<el-input v-if="question.type==='short_text'" v-model="value" size="large"/>
<el-input v-else-if="question.type==='long_text'" v-model="value" type="textarea" :rows="4"/>
<el-input-number v-else-if="['integer','number','duration'].includes(question.type)" v-model="value" :min="question.min" :max="question.max" controls-position="right"/>
<el-date-picker v-else-if="question.type==='date'" v-model="value" value-format="YYYY-MM-DD" class="full"/>
<el-time-picker v-else-if="question.type==='time'" v-model="value" value-format="HH:mm" class="full"/>
<el-radio-group v-else-if="['yes_no','single_choice','scale'].includes(question.type)" v-model="value" class="option-stack"><el-radio v-for="o in question.options" :key="String(o.value)" :value="o.value" border>{{o.label}}</el-radio></el-radio-group>
<el-checkbox-group v-else-if="question.type==='multi_choice'" v-model="value" class="option-stack"><el-checkbox v-for="o in question.options" :key="String(o.value)" :value="o.value" border>{{o.label}}</el-checkbox></el-checkbox-group>
</div></template>

