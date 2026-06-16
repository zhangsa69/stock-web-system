<script setup lang="ts">
import { onMounted } from "vue";
import AppHeader from "./components/layout/AppHeader.vue";
import AppFooter from "./components/layout/AppFooter.vue";
import { useAuthStore } from "./stores/auth";

const auth = useAuthStore();

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
</style>
