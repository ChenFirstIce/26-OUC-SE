<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
const list=ref<any[]>([]); const loading=ref(true)
onMounted(async()=>{try{list.value=(await api.get('/questionnaires')).data}finally{loading.value=false}})
</script>
<template><div><div class="page-heading"><div><span class="eyebrow">QUESTIONNAIRES</span><h1>问卷模板</h1><p>已发布版本可用于医生派发；历史派发始终使用当时版本。</p></div></div><div class="template-grid" v-loading="loading"><article v-for="q in list" :key="q.id" class="template-card"><div class="template-top"><span class="template-code">{{q.code}}</span><el-tag :type="q.status==='published'?'success':'info'">{{q.status==='published'?'已发布':'草稿'}}</el-tag></div><h3>{{q.name}}</h3><p>{{q.description}}</p><div class="template-foot"><span>版本 v{{q.latest_version}}</span><span>{{q.schema_json?.sections?.reduce((n:number,s:any)=>n+s.questions.length,0)||0}} 题</span></div></article></div><div class="notice-card"><b>正式量表提醒</b><p>当前内容均为非临床演示问卷。获得授权的正式题目和评分手册后，可通过版本化模板接入，不能用演示题替代临床量表。</p></div></div></template>

