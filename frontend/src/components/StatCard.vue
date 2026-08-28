<script setup lang="ts">
defineProps<{ label: string; value: string | number; hint: string; tone?: string }>()
</script>
<template><article class="stat-card" :class="tone"><div class="stat-label">{{ label }}</div><div class="stat-value">{{ value }}</div><div class="stat-hint">{{ hint }}</div></article></template>
