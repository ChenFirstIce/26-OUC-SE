<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const username = ref('doctor1')
const password = ref('Doctor123!')
const loading = ref(false)
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
async function submit() {
  loading.value = true
  try { await auth.login(username.value, password.value); router.push(String(route.query.redirect || '/dashboard')) }
  catch (error) { ElMessage.error((error as Error).message) }
  finally { loading.value = false }
}
</script>

<template>
  <div class="login-page">
    <div class="login-art">
      <div class="login-grid"></div><div class="art-copy"><span class="eyebrow">NEURO·NEXUS / COGNITIVE CARE CLOUD</span><h1>让每一次筛查<br>都成为连续的照护</h1><p>连接患者移动填写、临床复核、纵向档案与机构治理，为认知照护提供可信的数据工作流。</p><div class="login-features"><span><i></i>移动端实时接入</span><span><i></i>纵向风险分析</span><span><i></i>细粒度权限审计</span></div></div>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <span class="brand-mark large">N</span><h2>欢迎回来</h2><p class="muted">登录临床与机构管理工作台</p>
        <el-form label-position="top" @submit.prevent="submit">
          <el-form-item label="账号"><el-input v-model="username" size="large" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="password" type="password" size="large" show-password @keyup.enter="submit" /></el-form-item>
          <el-button type="primary" size="large" class="full" :loading="loading" @click="submit">登录系统</el-button>
        </el-form>
        <div class="demo-accounts"><b>演示账号</b><span>医生：doctor1 / Doctor123!</span><span>管理员：admin / Admin123!</span></div>
      </div>
    </div>
  </div>
</template>
