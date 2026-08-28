<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
function logout() { auth.logout(); router.push('/login') }
</script>

<template>
  <div class="staff-shell">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">认</span><div><strong>认知筛查中心</strong><small>AD Questionnaire</small></div></div>
      <nav>
        <router-link to="/dashboard">数据总览</router-link>
        <router-link to="/patients">患者管理</router-link>
        <router-link to="/assignments">问卷派发</router-link>
        <router-link to="/questionnaires">问卷模板</router-link>
      </nav>
      <div class="sidebar-note">筛查结果不等同于医学诊断</div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <div><b>{{ auth.user?.department_name || '全院管理' }}</b><span class="muted"> · {{ auth.user?.role === 'admin' ? '管理员' : '医生工作台' }}</span></div>
        <div class="user-chip"><span>{{ auth.user?.display_name }}</span><el-button link @click="logout">退出</el-button></div>
      </header>
      <section class="page-content"><router-view /></section>
    </main>
  </div>
</template>

