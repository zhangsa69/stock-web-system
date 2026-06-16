<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useAnalysisStore } from "../stores/analysis";
import AnalysisProgress from "../components/analysis/AnalysisProgress.vue";
import { Search, Loader2, CheckCircle, TrendingUp, FileText } from "lucide-vue-next";

const route = useRoute();
const store = useAnalysisStore();
const auth = useAuthStore();
const stockCode = ref("");
const didAutoStart = ref(false);

onMounted(() => {
  const taskId = route.params.taskId as string | undefined;
  if (taskId) { store.fetchStatus(taskId); return; }
  if (route.query.code) {
    stockCode.value = route.query.code as string;
    autoStart(route.query.code as string);
  }
});

watch(() => route.query.code, (newCode) => {
  if (newCode && !didAutoStart.value) {
    stockCode.value = newCode as string;
    autoStart(newCode as string);
  }
});

function autoStart(code: string) {
  didAutoStart.value = true;
  store.startAnalysis(code, auth.user?.email || "");
}

function handleSubmit() {
  const code = stockCode.value.trim();
  if (!code) return;
  store.reset();
  store.startAnalysis(code, auth.user?.email || "");
}
</script>

<template>
  <div class="analysis-page">
    <!-- Search area -->
    <div class="search-area animate-fade-in-up">
      <h2 class="section-title">股票财报分析</h2>
      <div class="search-pill">
        <Search :size="20" class="search-icon" />
        <input
          v-model="stockCode"
          type="text"
          placeholder="输入股票代码，如 600519"
          @keyup.enter="handleSubmit"
        />
        <button @click="handleSubmit" :disabled="!stockCode.trim() || store.isLoading" class="btn-primary">
          <Loader2 v-if="store.isLoading" :size="16" class="animate-spin" />
          {{ store.isLoading ? "分析中..." : "开始分析" }}
        </button>
      </div>
      <p class="search-hint">
        报告将发送至 <span class="email-highlight">{{ auth.user?.email }}</span>
      </p>
    </div>

    <!-- Progress -->
    <AnalysisProgress
      v-if="store.currentStatus && (store.currentStatus.status === 'pending' || store.currentStatus.status === 'running')"
      :status="store.currentStatus"
    />

    <!-- Error -->
    <div v-if="store.error" class="error-card animate-scale-in">
      <div class="error-icon">!</div>
      <p>{{ store.error }}</p>
      <button @click="handleSubmit" class="btn-secondary">重新分析</button>
    </div>

    <!-- Completed -->
    <div v-if="store.currentStatus?.status === 'completed'" class="done-card animate-scale-in">
      <div class="done-ring">
        <CheckCircle :size="48" />
      </div>
      <h3>分析完成</h3>
      <p class="done-stock">
        {{ store.currentStatus.stock_name || store.currentStatus.stock_code }}
        <span class="done-badge">报告已生成</span>
      </p>
      <p class="done-email">
        报告已发送至 <span class="email-highlight">{{ auth.user?.email || '您的邮箱' }}</span>
        <br />请在历史记录中下载原始 .md 文件
      </p>
      <div class="done-actions">
        <router-link to="/history" class="btn-primary">
          <FileText :size="16" />查看历史
        </router-link>
        <button @click="stockCode = ''; store.reset()" class="btn-secondary">
          分析新股票
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-if="!store.currentStatus && !store.isLoading && !store.error"
      class="empty-state animate-fade-in-up"
    >
      <div class="empty-icon">
        <TrendingUp :size="32" />
      </div>
      <h3>输入股票代码开始分析</h3>
      <p>支持 A 股（600519）和港股（00700）</p>
    </div>
  </div>
</template>

<style scoped>
.analysis-page {
  max-width: 720px; margin: 0 auto; padding: 48px 24px 96px;
}
.section-title {
  font-family: 'Inter', sans-serif;
  font-size: 28px; font-weight: 600;
  color: #ffffff; margin: 0 0 24px;
  letter-spacing: -0.4px;
}

/* Search */
.search-area { margin-bottom: 40px; }
.search-pill {
  display: flex; align-items: center;
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 9999px; padding: 4px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search-pill:focus-within {
  border-color: #0052ff;
  box-shadow: 0 0 0 3px rgba(0,82,255,0.15);
}
.search-icon { color: rgba(255,255,255,0.3); margin: 0 8px 0 16px; flex-shrink: 0; }
.search-pill input {
  flex: 1; background: transparent; border: none; outline: none;
  color: #fff; font-size: 16px; font-family: 'Inter', sans-serif;
  padding: 12px 0;
}
.search-pill input::placeholder { color: rgba(255,255,255,0.3); }
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: 9999px; border: none;
  background: #0052ff; color: #fff;
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: 15px;
  cursor: pointer; white-space: nowrap;
  transition: all 0.2s ease;
}
.btn-primary:hover { background: #0045d9; box-shadow: 0 4px 16px rgba(0,82,255,0.35); }
.btn-primary:active { transform: scale(0.97); }
.btn-primary:disabled { background: rgba(0,82,255,0.3); cursor: not-allowed; box-shadow: none; }
.search-hint {
  font-size: 13px; color: rgba(255,255,255,0.3); margin-top: 10px;
}
.email-highlight { color: #0052ff; font-weight: 500; }

.btn-secondary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: 9999px;
  border: 1px solid rgba(255,255,255,0.15);
  background: transparent; color: rgba(255,255,255,0.7);
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: 15px;
  cursor: pointer; transition: all 0.2s ease;
}
.btn-secondary:hover { border-color: rgba(255,255,255,0.35); background: rgba(255,255,255,0.04); }

/* Error */
.error-card {
  text-align: center; padding: 48px;
  background: rgba(207,32,47,0.06);
  border: 1px solid rgba(207,32,47,0.15);
  border-radius: 24px;
}
.error-icon {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(207,32,47,0.15); color: #cf202f;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700;
  margin: 0 auto 16px;
}
.error-card p { color: rgba(255,255,255,0.6); margin: 0 0 20px; }

/* Done */
.done-card {
  text-align: center; padding: 56px 32px;
  background: rgba(5,177,105,0.04);
  border: 1px solid rgba(5,177,105,0.12);
  border-radius: 24px;
}
.done-ring {
  width: 80px; height: 80px; border-radius: 50%;
  background: rgba(5,177,105,0.1);
  display: flex; align-items: center; justify-content: center;
  color: #05b169; margin: 0 auto 24px;
  animation: pulse-ring 2s ease-in-out infinite;
}
@keyframes pulse-ring {
  0%,100% { box-shadow: 0 0 0 0 rgba(5,177,105,0.3); }
  50% { box-shadow: 0 0 0 16px rgba(5,177,105,0); }
}
.done-card h3 {
  font-family: 'Inter', sans-serif;
  font-size: 24px; font-weight: 600;
  color: #ffffff; margin: 0 0 12px;
}
.done-stock {
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-size: 18px; font-weight: 500;
  color: rgba(255,255,255,0.6);
  display: flex; align-items: center; justify-content: center; gap: 10px;
  margin: 0 0 12px;
}
.done-badge {
  display: inline-block;
  padding: 2px 10px; border-radius: 9999px;
  background: rgba(5,177,105,0.15);
  color: #05b169;
  font-family: 'Inter', sans-serif;
  font-size: 11px; font-weight: 600;
}
.done-email {
  color: rgba(255,255,255,0.4); font-size: 14px;
  margin: 0 0 28px; line-height: 1.6;
}
.done-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

/* Empty */
.empty-state { text-align: center; padding: 80px 24px; }
.empty-icon {
  width: 72px; height: 72px; border-radius: 50%;
  background: rgba(255,255,255,0.04);
  display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,0.15);
  margin: 0 auto 24px;
}
.empty-state h3 {
  font-family: 'Inter', sans-serif;
  font-size: 18px; font-weight: 500;
  color: rgba(255,255,255,0.35);
  margin: 0 0 8px;
}
.empty-state p { color: rgba(255,255,255,0.2); font-size: 14px; }

/* Animations */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) both; }
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.92); }
  to { opacity: 1; transform: scale(1); }
}
.animate-scale-in { animation: scaleIn 0.4s cubic-bezier(0.34,1.56,0.64,1) both; }
</style>
