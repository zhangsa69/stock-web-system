<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { Coins, User, LogOut } from "lucide-vue-next";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

onMounted(async () => {
  if (auth.isLoggedIn) {
    await auth.fetchBalance();
  }
});

function isActive(to: string) {
  if (to === '/') return route.path === '/';
  return route.path.startsWith(to);
}

function logout() {
  auth.logout();
  router.push('/');
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Logo -->
      <router-link to="/" class="logo-link">
        <svg class="logo-icon" width="28" height="28" viewBox="0 0 28 28" fill="none">
          <defs>
            <linearGradient id="cb-logo-grad" x1="0" y1="0" x2="28" y2="28">
              <stop offset="0%" stop-color="#0052ff" />
              <stop offset="100%" stop-color="#3b82f6" />
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="24" height="24" rx="6" stroke="url(#cb-logo-grad)" stroke-width="2.5"/>
          <rect x="7" y="7" width="5" height="13" rx="1.5" fill="url(#cb-logo-grad)"/>
          <rect x="14" y="10" width="5" height="10" rx="1.5" fill="url(#cb-logo-grad)" opacity="0.6"/>
          <line x1="7" y1="7" x2="19" y2="7" stroke="url(#cb-logo-grad)" stroke-width="2" opacity="0.3"/>
        </svg>
        <span class="logo-text">AI财报分析</span>
      </router-link>

      <!-- Navigation -->
      <nav class="nav-links">
        <router-link
          v-for="link in [{label:'首页',to:'/'},{label:'开始分析',to:'/analysis'},{label:'分析历史',to:'/history'}]"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ active: isActive(link.to) }"
        >
          {{ link.label }}
          <span class="nav-underline" />
        </router-link>
      </nav>

      <div class="header-spacer" />

      <!-- Logged In -->
      <template v-if="auth.isLoggedIn">
        <div class="user-area">
          <span class="user-email">
            <User :size="14" />
            {{ auth.user?.email }}
          </span>
          <span class="balance-badge">
            <Coins :size="14" />
            <span>{{ auth.balance }}</span>
          </span>
          <button @click="logout" class="logout-btn" aria-label="退出登录">
            <LogOut :size="14" />
          </button>
        </div>
      </template>

      <!-- Logged Out -->
      <router-link v-else to="/login" class="login-btn">
        登录 / 注册
      </router-link>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 50;
  height: 64px;
  background: rgba(10,11,13,0.88);
  backdrop-filter: blur(16px) saturate(140%);
  -webkit-backdrop-filter: blur(16px) saturate(140%);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.header-inner {
  display: flex; align-items: center;
  height: 100%; max-width: 1280px;
  margin: 0 auto; padding: 0 24px;
  gap: 28px;
}
.logo-link {
  display: flex; align-items: center; gap: 10px;
  text-decoration: none; flex-shrink: 0;
}
.logo-text {
  font-family: 'Inter', sans-serif;
  font-weight: 600; font-size: 18px;
  color: #0052ff; letter-spacing: -0.01em;
  white-space: nowrap;
}
.nav-links { display: flex; align-items: center; gap: 2px; height: 100%; }
.nav-link {
  position: relative;
  display: inline-flex; align-items: center;
  height: 100%; padding: 0 16px;
  font-family: 'Inter', sans-serif;
  font-weight: 500; font-size: 14px;
  color: rgba(255,255,255,0.55);
  text-decoration: none;
  transition: color 0.2s ease;
  white-space: nowrap;
}
.nav-link:hover { color: rgba(255,255,255,0.9); }
.nav-link.active { color: #ffffff; }
.nav-underline {
  position: absolute; bottom: 0; left: 50%;
  width: 0; height: 2px;
  background: #0052ff; border-radius: 1px;
  transition: width 0.25s cubic-bezier(0.25,0.8,0.25,1.2),
              left 0.25s cubic-bezier(0.25,0.8,0.25,1.2);
}
.nav-link:hover .nav-underline {
  width: calc(100% - 32px); left: 16px;
  background: rgba(255,255,255,0.3);
}
.nav-link.active .nav-underline {
  width: calc(100% - 32px); left: 16px;
  background: #0052ff;
}
.header-spacer { flex: 1; }
.user-area {
  display: flex; align-items: center; gap: 12px;
  flex-shrink: 0;
}
.user-email {
  display: flex; align-items: center; gap: 6px;
  font-family: 'Inter', sans-serif;
  font-weight: 400; font-size: 13px;
  color: rgba(255,255,255,0.45);
  max-width: 180px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap;
}
.balance-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 10px; border-radius: 9999px;
  font-family: 'Inter', sans-serif;
  font-weight: 600; font-size: 13px;
  color: #0052ff;
  background: rgba(0,82,255,0.1);
  border: 1px solid rgba(0,82,255,0.25);
  white-space: nowrap;
}
.logout-btn {
  display: inline-flex; align-items: center;
  justify-content: center;
  width: 32px; height: 32px; padding: 0;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 50%; background: transparent;
  color: rgba(255,255,255,0.35);
  cursor: pointer;
  transition: all 0.2s ease;
}
.logout-btn:hover {
  color: #cf202f;
  background: rgba(207,32,47,0.1);
  border-color: rgba(207,32,47,0.3);
}
.login-btn {
  display: inline-flex; align-items: center;
  justify-content: center;
  height: 36px; padding: 0 20px;
  border: none; border-radius: 9999px;
  font-family: 'Inter', sans-serif;
  font-weight: 600; font-size: 14px;
  color: #ffffff; background: #0052ff;
  text-decoration: none; white-space: nowrap;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}
.login-btn:hover {
  background: #0045d9;
  box-shadow: 0 2px 12px rgba(0,82,255,0.4);
}

@media (max-width: 768px) {
  .header-inner { padding: 0 16px; gap: 12px; }
  .nav-link { padding: 0 10px; font-size: 13px; }
  .nav-link:hover .nav-underline,
  .nav-link.active .nav-underline {
    width: calc(100% - 20px); left: 10px;
  }
  .user-email { display: none; }
}
@media (max-width: 480px) {
  .logo-text { font-size: 15px; }
  .nav-link { padding: 0 8px; font-size: 12px; }
}
</style>
