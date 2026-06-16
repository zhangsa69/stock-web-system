<script setup lang="ts">
import { ref, onMounted } from "vue";
import AppHeader from "./components/layout/AppHeader.vue";
import AppFooter from "./components/layout/AppFooter.vue";
import { useAuthStore } from "./stores/auth";
import { setGlobalErrorHandler } from "./api/client";

const auth = useAuthStore();

const globalError = ref("");
const showError = ref(false);
let errorTimer: ReturnType<typeof setTimeout> | null = null;

setGlobalErrorHandler((msg: string) => {
  globalError.value = msg;
  showError.value = true;
  if (errorTimer) clearTimeout(errorTimer);
  errorTimer = setTimeout(() => { showError.value = false; }, 5000);
});

onMounted(async () => {
  if (auth.isLoggedIn) {
    await auth.fetchUser();
  }
});
</script>

<template>
  <div class="ai-gradient-bg"></div>

  <div class="app-shell">
    <AppHeader />
    <main class="flex-1 pt-16">
      <router-view v-slot="{ Component }">
        <transition name="page-slide" mode="out-in" appear>
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <AppFooter />

    <!-- Error Toast -->
    <transition name="toast-slide">
      <div
        v-if="showError"
        class="error-toast"
      >
        <span>&#9888;</span>
        <span class="flex-1">{{ globalError }}</span>
        <button @click.stop="showError = false">&times;</button>
      </div>
    </transition>
  </div>
</template>

<style>
/* ── Page transitions ── */
.page-slide-enter-active {
  transition: opacity 0.35s cubic-bezier(0.16,1,0.3,1),
              transform 0.35s cubic-bezier(0.16,1,0.3,1);
}
.page-slide-leave-active {
  transition: opacity 0.2s ease-in,
              transform 0.2s ease-in;
  position: absolute; width: 100%;
}
.page-slide-enter-from { opacity: 0; transform: translateY(12px); }
.page-slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* ── Toast ── */
.error-toast {
  position: fixed;
  bottom: 24px; right: 24px;
  z-index: 9999;
  display: flex; align-items: center; gap: 12px;
  max-width: 384px;
  padding: 14px 18px;
  border-radius: 12px;
  background: rgba(207,32,47,0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(207,32,47,0.3);
  color: #ffffff;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 8px 32px rgba(207,32,47,0.2);
  cursor: pointer;
  animation: toast-enter 0.35s cubic-bezier(0.16,1,0.3,1) both;
}
.error-toast button {
  flex-shrink: 0;
  width: 22px; height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(255,255,255,0.18);
  color: #fff;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.error-toast button:hover { background: rgba(255,255,255,0.32); }
.toast-slide-leave-active {
  animation: toast-exit 0.3s ease-in both;
}
@keyframes toast-enter {
  from { opacity: 0; transform: translateX(40px) scale(0.92); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}
@keyframes toast-exit {
  from { opacity: 1; transform: translateX(0); }
  to { opacity: 0; transform: translateX(60px); }
}

/* ── AI Gradient Background ── */
.ai-gradient-bg {
  position: fixed; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,82,255,0.08) 0%, transparent 60%),
    radial-gradient(ellipse 50% 50% at 80% 80%, rgba(124,58,237,0.06) 0%, transparent 60%),
    radial-gradient(ellipse 60% 40% at 20% 20%, rgba(59,130,246,0.05) 0%, transparent 50%),
    linear-gradient(160deg, #0a0e1a 0%, #0d1b2a 30%, #132238 60%, #0f172a 100%);
  pointer-events: none;
}
.app-shell {
  position: relative; z-index: 1;
  min-height: 100vh;
  display: flex; flex-direction: column;
}
</style>
