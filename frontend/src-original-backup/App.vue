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
  <div class="min-h-screen flex flex-col">
    <AppHeader />
    <main class="flex-1 pt-16">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <AppFooter />

    <!-- 全局错误 Toast -->
    <transition name="toast">
      <div
        v-if="showError"
        class="fixed bottom-6 right-6 z-[9999] bg-red-500/90 backdrop-blur text-white px-5 py-3 rounded-xl shadow-lg text-sm max-w-sm"
      >
        ⚠ {{ globalError }}
      </div>
    </transition>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from { opacity: 0; transform: translateY(20px); }
.toast-leave-to { opacity: 0; transform: translateY(20px); }
</style>
