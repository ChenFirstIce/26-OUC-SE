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
      <div class="art-copy"><span class="eyebrow">COGNITIVE CARE · 认知关怀</span><h1>让每一次筛查<br>都成为连续的照护</h1><p>问卷派发、移动填写、结果复核和数据统计在一个清晰的流程中完成。</p></div>
    </div>
    <div class="login-panel">
      <div class="login-box">
        <span class="brand-mark large">认</span><h2>欢迎回来</h2><p class="muted">登录医生与管理工作台</p>
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

