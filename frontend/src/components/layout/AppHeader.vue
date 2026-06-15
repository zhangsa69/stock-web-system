<script setup lang="ts">
import { useRouter } from "vue-router";
import { LineChart } from "lucide-vue-next";

const router = useRouter();
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
    </nav>
  </header>
</template>
