<script setup lang="ts">
import { init, use, type ECharts } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])
const props = defineProps<{ title: string; option: any }>()
const el = ref<HTMLElement>()
let chart: ECharts | undefined
let resizeObserver: ResizeObserver | undefined
function render() { if (el.value?.clientWidth) { chart ||= init(el.value); chart.resize(); chart.setOption(props.option, true) } }
function exportPng() { const url = chart?.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' }); if (url) { const a = document.createElement('a'); a.href = url; a.download = `${props.title}.png`; a.click() } }
onMounted(() => { resizeObserver = new ResizeObserver(() => render()); if (el.value) resizeObserver.observe(el.value); nextTick(render); window.addEventListener('resize', render) })
watch(() => props.option, () => nextTick(render), { deep: true })
onBeforeUnmount(() => { resizeObserver?.disconnect(); window.removeEventListener('resize', render); chart?.dispose() })
</script>
<template><article class="panel"><div class="panel-head"><h3>{{ title }}</h3><el-button link @click="exportPng">导出 PNG</el-button></div><div ref="el" class="chart"></div></article></template>
