<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import { LineChart, LogOut, User } from "lucide-vue-next";

const router = useRouter();
const auth = useAuthStore();
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 h-16 bg-[#0D1B2A]/90 backdrop-blur-md border-b border-white/10 flex items-center px-6"
  >
    <!-- Logo -->
    <router-link to="/" class="flex items-center gap-2.5 no-underline">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#D4A843] to-[#F0C060] flex items-center justify-center">
        <LineChart :size="18" class="text-[#0D1B2A]" />
      </div>
      <span class="text-lg font-bold text-[#E8EDF5]">AI财报分析</span>
    </router-link>

    <!-- 导航 -->
    <nav class="ml-auto flex items-center gap-1">
      <router-link
        to="/"
        class="px-4 py-2 text-sm text-[#8B9CB5] hover:text-[#E8EDF5] rounded-lg hover:bg-white/5 transition-colors"
      >
        首页
      </router-link>
      <template v-if="auth.isLoggedIn">
        <router-link
          to="/analysis"
          class="px-4 py-2 text-sm text-[#8B9CB5] hover:text-[#E8EDF5] rounded-lg hover:bg-white/5 transition-colors"
        >
          开始分析
        </router-link>
        <router-link
          to="/history"
          class="px-4 py-2 text-sm text-[#8B9CB5] hover:text-[#E8EDF5] rounded-lg hover:bg-white/5 transition-colors"
        >
          分析历史
        </router-link>
        <!-- 用户菜单 -->
        <div class="flex items-center gap-2 ml-4 pl-4 border-l border-white/10">
          <User :size="16" class="text-[#8B9CB5]" />
          <span class="text-sm text-[#8B9CB5] max-w-[160px] truncate">{{ auth.user?.email }}</span>
          <button
            @click="auth.logout(); router.push('/')"
            class="ml-2 px-3 py-1.5 text-xs text-[#8B9CB5] hover:text-red-400 rounded-lg hover:bg-white/5 transition-colors flex items-center gap-1"
          >
            <LogOut :size="14" />退出
          </button>
        </div>
      </template>
      <template v-else>
        <router-link
          to="/login"
          class="ml-4 px-5 py-2 text-sm font-semibold bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] rounded-xl hover:opacity-90 transition-opacity"
        >
          登录 / 注册
        </router-link>
      </template>
    </nav>
  </header>
</template>
