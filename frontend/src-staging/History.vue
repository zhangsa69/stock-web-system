<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { analysisApi, type HistoryItem } from "../api/analysis";
import { Clock, Download, TrendingUp, Search } from "lucide-vue-next";

const router = useRouter();
const items = ref<HistoryItem[]>([]);
const total = ref(0);
const loading = ref(true);
const page = ref(1);

const statusMap: Record<string, { text: string; color: string; dot: string }> = {
  completed: { text: "已完成", color: "#05b169", dot: "bg-[#05b169]" },
  failed: { text: "失败", color: "#cf202f", dot: "bg-[#cf202f]" },
  running: { text: "分析中", color: "#f4b000", dot: "bg-[#f4b000]" },
  pending: { text: "排队中", color: "#0052ff", dot: "bg-[#0052ff]" },
};

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleString("zh-CN");
}

async function handleDownload(taskId: string, stockCode: string) {
  try {
    const response = await fetch(`/api/analysis/${taskId}/download`);
    if (!response.ok) throw new Error("下载失败");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${stockCode}_分析报告.md`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error("下载失败", e);
  }
}

async function loadHistory() {
  loading.value = true;
  const data = await analysisApi.getHistory(page.value);
  items.value = data.items;
  total.value = data.total;
  loading.value = false;
}

onMounted(loadHistory);
</script>

<template>
  <div class="history-page">
    <div class="history-header animate-fade-in-up">
      <div class="flex items-center gap-3">
        <Clock :size="22" style="color: #0052ff" />
        <h2>分析历史</h2>
      </div>
      <router-link to="/analysis" class="new-analysis-btn">
        <Search :size="14" />新分析
      </router-link>
    </div>

    <div class="history-table animate-fade-in-up" style="animation-delay: 0.1s">
      <!-- Loading skeleton -->
      <div v-if="loading" class="loading-area">
        <div v-for="i in 5" :key="i" class="skeleton-row">
          <div class="skeleton-cell w-20" />
          <div class="skeleton-cell w-24" />
          <div class="skeleton-cell w-16" />
          <div class="skeleton-cell w-40" />
          <div class="skeleton-cell w-16" />
        </div>
      </div>

      <!-- Table -->
      <table v-else-if="items.length > 0" class="cb-table">
        <thead>
          <tr>
            <th>股票代码</th>
            <th>名称</th>
            <th>状态</th>
            <th>分析时间</th>
            <th class="text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(item, i) in items"
            :key="item.task_id"
            :style="{ animationDelay: (0.1 + i * 0.05) + 's' }"
            class="table-row-animate"
          >
            <td class="td-code">{{ item.stock_code }}</td>
            <td class="td-name">{{ item.stock_name || "-" }}</td>
            <td>
              <span class="status-badge" :style="{ color: statusMap[item.status]?.color, borderColor: statusMap[item.status]?.color + '40', background: statusMap[item.status]?.color + '10' }">
                <span class="status-dot" :style="{ background: statusMap[item.status]?.color }" :class="{ 'animate-status-pulse': item.status === 'running' }" />
                {{ statusMap[item.status]?.text || item.status }}
              </span>
            </td>
            <td class="td-time">{{ formatTime(item.created_at) }}</td>
            <td class="td-action">
              <button
                v-if="item.status === 'completed'"
                @click="handleDownload(item.task_id, item.stock_code)"
                class="download-btn"
              >
                <Download :size="14" />下载
              </button>
              <span v-else class="no-action">-</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Empty -->
      <div v-else class="empty-state">
        <div class="empty-icon-wrap">
          <TrendingUp :size="28" />
        </div>
        <h3>暂无分析记录</h3>
        <p>开始你的第一次股票分析吧</p>
        <router-link to="/analysis" class="btn-primary">开始分析</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-page {
  max-width: 1000px; margin: 0 auto; padding: 48px 24px 96px;
}
.history-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 32px;
}
.history-header h2 {
  font-family: 'Inter', sans-serif;
  font-size: 28px; font-weight: 600;
  color: #ffffff; margin: 0;
  letter-spacing: -0.4px;
}
.new-analysis-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 20px; border-radius: 9999px;
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.55);
  font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
}
.new-analysis-btn:hover {
  border-color: rgba(0,82,255,0.4);
  color: #0052ff;
  background: rgba(0,82,255,0.06);
}

/* Table */
.history-table {
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px;
  overflow: hidden;
}
.cb-table {
  width: 100%; border-collapse: collapse;
}
.cb-table thead tr {
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.cb-table th {
  text-align: left;
  padding: 14px 24px;
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-size: 11px; font-weight: 500;
  text-transform: uppercase; letter-spacing: 1px;
  color: rgba(255,255,255,0.3);
}
.cb-table td {
  padding: 14px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  font-size: 14px;
  color: rgba(255,255,255,0.5);
}
.cb-table tbody tr:hover {
  background: rgba(255,255,255,0.015);
}
.td-code {
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-weight: 500; color: #ffffff !important;
}
.td-name { font-weight: 500; }
.td-time { font-size: 13px; color: rgba(255,255,255,0.3) !important; }
.td-action { text-align: right; }
.table-row-animate {
  opacity: 0;
  animation: rowSlideIn 0.4s cubic-bezier(0.16,1,0.3,1) forwards;
}
@keyframes rowSlideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

/* Status badge */
.status-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 9999px;
  border: 1px solid; font-size: 12px; font-weight: 600;
}
.status-dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.animate-status-pulse {
  animation: statusPulse 1.5s ease-in-out infinite;
}
@keyframes statusPulse {
  0%,100% { box-shadow: 0 0 0 0 currentColor; opacity: 1; }
  50% { box-shadow: 0 0 0 6px transparent; opacity: 0.6; }
}

/* Download */
.download-btn {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 6px 14px; border-radius: 9999px;
  border: 1px solid rgba(0,82,255,0.25);
  background: rgba(0,82,255,0.06);
  color: #0052ff;
  font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s ease;
}
.download-btn:hover {
  background: #0052ff; color: #fff; border-color: #0052ff;
}
.no-action { color: rgba(255,255,255,0.15); }

/* Loading skeleton */
.loading-area { padding: 16px; }
.skeleton-row {
  display: flex; gap: 24px; padding: 14px 24px;
}
.skeleton-cell {
  height: 16px; border-radius: 8px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.06) 50%, rgba(255,255,255,0.03) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}
.w-20 { width: 80px; }
.w-24 { width: 96px; }
.w-16 { width: 64px; }
.w-40 { width: 160px; }
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Empty */
.empty-state { text-align: center; padding: 72px 24px; }
.empty-icon-wrap {
  width: 64px; height: 64px; border-radius: 50%;
  background: rgba(255,255,255,0.04);
  display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,0.12);
  margin: 0 auto 20px;
}
.empty-state h3 {
  font-family: 'Inter', sans-serif;
  font-size: 18px; font-weight: 500;
  color: rgba(255,255,255,0.3);
  margin: 0 0 8px;
}
.empty-state p { color: rgba(255,255,255,0.18); font-size: 14px; margin: 0 0 24px; }
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: 9999px; border: none;
  background: #0052ff; color: #fff;
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: 15px;
  cursor: pointer; text-decoration: none;
  transition: all 0.2s ease;
}
.btn-primary:hover { background: #0045d9; box-shadow: 0 4px 16px rgba(0,82,255,0.35); }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up { animation: fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) both; }
</style>
