<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const isAdmin = computed(() => auth.user?.role === 'admin')
function logout() { auth.logout(); router.push('/login') }
</script>

<template>
  <div class="staff-shell">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">N</span><div><strong>NEURO·NEXUS</strong><small>COGNITIVE CARE CLOUD</small></div></div>
      <div class="nav-caption">CLINICAL WORKSPACE</div>
      <nav>
        <router-link to="/dashboard"><i>⌁</i><span>数据中心</span></router-link>
        <router-link to="/patients"><i>◎</i><span>患者中心</span></router-link>
        <router-link v-if="isAdmin || auth.user?.permissions?.can_assign_questionnaires" to="/assignments"><i>↗</i><span>任务与派发</span></router-link>
        <router-link to="/questionnaires"><i>▦</i><span>问卷资源库</span></router-link>
      </nav>
      <template v-if="isAdmin">
        <div class="nav-caption admin-caption">ADMINISTRATION</div>
        <nav><router-link to="/admin"><i>◇</i><span>组织与权限</span></router-link></nav>
      </template>
      <div class="sidebar-status"><span class="status-signal"></span><div><b>Secure Node Online</b><small>安全连接已建立</small></div></div>
      <div class="sidebar-note">问卷筛查仅提供风险提示，不替代医生诊断。</div>
    </aside>
    <main class="main-area">
      <header class="topbar">
        <div class="top-context"><span class="breadcrumb-orb"></span><div><b>{{ auth.user?.department_name || '全院数据域' }}</b><small>{{ isAdmin ? '机构管理控制台' : '临床协作工作台' }}</small></div></div>
        <div class="top-actions"><span class="live-chip"><i></i>系统在线</span><div class="user-avatar">{{ auth.user?.display_name?.slice(0, 1) }}</div><div class="user-chip"><span>{{ auth.user?.display_name }}</span><small>{{ isAdmin ? 'SYSTEM ADMIN' : 'PHYSICIAN' }}</small></div><el-button link @click="logout">退出</el-button></div>
      </header>
      <section class="page-content"><router-view /></section>
    </main>
  </div>
</template>
