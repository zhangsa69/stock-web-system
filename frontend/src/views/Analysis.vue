<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useAnalysisStore } from "../stores/analysis";
import AnalysisProgress from "../components/analysis/AnalysisProgress.vue";
import { Search, Loader2, CheckCircle } from "lucide-vue-next";

const route = useRoute();
const store = useAnalysisStore();
const stockCode = ref("");
const userEmail = ref("");

onMounted(() => {
  const taskId = route.params.taskId as string | undefined;
  if (taskId) {
    store.fetchStatus(taskId);
    return;
  }
  if (route.query.code) {
    stockCode.value = route.query.code as string;
    userEmail.value = (route.query.email as string) || "";
    if (userEmail.value) {
      store.startAnalysis(route.query.code as string, userEmail.value);
    }
  }
});

watch(
  () => [route.query.code, route.query.email],
  ([newCode, newEmail]) => {
    if (newCode) {
      stockCode.value = newCode as string;
      userEmail.value = (newEmail as string) || "";
      store.reset();
      if (userEmail.value) {
        store.startAnalysis(newCode as string, userEmail.value);
      }
    }
  }
);

function handleSubmit() {
  const code = stockCode.value.trim();
  const email = userEmail.value.trim();
  if (!code || !email) return;
  store.reset();
  store.startAnalysis(code, email);
}
</script>

<template>
  <div class="max-w-5xl mx-auto px-6 py-12">
    <!-- 搜索区域 -->
    <div class="mb-10 animate-slide-up">
      <h2 class="text-2xl font-bold text-[#E8EDF5] mb-6">股票财报分析</h2>
      <div
        class="flex items-center gap-3 bg-white/5 backdrop-blur-md border border-white/10 rounded-xl p-2 focus-within:border-[#D4A843] transition-colors"
      >
        <Search :size="20" class="ml-3 text-[#8B9CB5] shrink-0" />
        <input
          v-model="stockCode"
          type="text"
          placeholder="输入股票代码，如 600519"
          class="flex-1 bg-transparent border-none outline-none text-white placeholder:text-[#5C6E8A] py-2.5 text-base"
          @keyup.enter="handleSubmit"
        />
        <button
          @click="handleSubmit"
          :disabled="!stockCode.trim() || !userEmail.trim() || store.isLoading"
          class="px-6 py-2.5 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-lg hover:opacity-90 disabled:opacity-40 transition-opacity flex items-center gap-2"
        >
          <Loader2 v-if="store.isLoading" :size="16" class="animate-spin" />
          {{ store.isLoading ? "分析中..." : "开始分析" }}
        </button>
      </div>
      <div class="mt-3">
        <input
          v-model="userEmail"
          type="email"
          placeholder="输入您的邮箱（必填，分析完成后发送报告）"
          class="w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] text-sm focus:border-[#D4A843] outline-none transition-colors"
          @keyup.enter="handleSubmit"
        />
      </div>
    </div>

    <!-- 进度 -->
    <AnalysisProgress
      v-if="store.currentStatus && (store.currentStatus.status === 'pending' || store.currentStatus.status === 'running')"
      :status="store.currentStatus"
    />

    <!-- 错误 -->
    <div
      v-if="store.error"
      class="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center"
    >
      <p class="text-red-400">{{ store.error }}</p>
      <button
        @click="handleSubmit"
        class="mt-4 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-[#8B9CB5] hover:border-[#D4A843]/50 transition-colors"
      >
        重新分析
      </button>
    </div>

    <!-- 分析完成 -->
    <div
      v-if="store.currentStatus?.status === 'completed'"
      class="bg-green-500/10 border border-green-500/30 rounded-2xl p-10 text-center animate-slide-up"
    >
      <CheckCircle :size="48" class="mx-auto mb-4 text-green-400" />
      <h3 class="text-xl font-bold text-[#E8EDF5] mb-2">分析完成</h3>
      <p class="text-[#8B9CB5] mb-1">
        {{ store.currentStatus.stock_name || store.currentStatus.stock_code }} 报告已生成
      </p>
      <p class="text-sm text-[#5C6E8A]">
        报告已发送至 <span class="text-[#F0C060]">{{ userEmail || '您的邮箱' }}</span>，请在历史记录中下载原始 .md 文件
      </p>
    </div>

    <!-- 空状态 -->
    <div
      v-if="!store.currentStatus && !store.isLoading && !store.error"
      class="text-center py-20"
    >
      <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-white/5 flex items-center justify-center">
        <Search :size="32" class="text-[#5C6E8A]" />
      </div>
      <h3 class="text-lg text-[#8B9CB5] mb-2">输入股票代码开始分析</h3>
      <p class="text-sm text-[#5C6E8A]">支持 A 股（600519）和港股（00700）</p>
    </div>
  </div>
</template>
