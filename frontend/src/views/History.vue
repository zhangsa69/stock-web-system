<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { analysisApi, type HistoryItem } from "../api/analysis";
import { Clock, TrendingUp, Download } from "lucide-vue-next";

const router = useRouter();
const items = ref<HistoryItem[]>([]);
const total = ref(0);
const loading = ref(true);
const page = ref(1);

const statusMap: Record<string, { text: string; color: string }> = {
  completed: { text: "已完成", color: "text-green-400" },
  failed: { text: "失败", color: "text-red-400" },
  running: { text: "分析中", color: "text-yellow-400" },
  pending: { text: "排队中", color: "text-blue-400" },
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
  <div class="max-w-5xl mx-auto px-6 py-12">
    <div class="flex items-center gap-3 mb-8">
      <Clock :size="24" class="text-[#D4A843]" />
      <h2 class="text-2xl font-bold text-[#E8EDF5]">分析历史</h2>
    </div>

    <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead class="border-b border-white/5">
            <tr>
              <th class="text-left px-6 py-4 text-xs text-[#5C6E8A] font-medium uppercase tracking-wider">股票代码</th>
              <th class="text-left px-6 py-4 text-xs text-[#5C6E8A] font-medium uppercase tracking-wider">股票名称</th>
              <th class="text-left px-6 py-4 text-xs text-[#5C6E8A] font-medium uppercase tracking-wider">状态</th>
              <th class="text-left px-6 py-4 text-xs text-[#5C6E8A] font-medium uppercase tracking-wider">分析时间</th>
              <th class="text-right px-6 py-4 text-xs text-[#5C6E8A] font-medium uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in items"
              :key="item.task_id"
              class="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <td class="px-6 py-4 text-sm font-mono text-[#E8EDF5]">{{ item.stock_code }}</td>
              <td class="px-6 py-4 text-sm text-[#8B9CB5]">{{ item.stock_name || "-" }}</td>
              <td class="px-6 py-4">
                <span :class="[statusMap[item.status]?.color || 'text-gray-400']" class="text-xs font-medium">
                  {{ statusMap[item.status]?.text || item.status }}
                </span>
              </td>
              <td class="px-6 py-4 text-xs text-[#5C6E8A]">{{ formatTime(item.created_at) }}</td>
              <td class="px-6 py-4 text-right">
                <button
                  v-if="item.status === 'completed'"
                  @click="handleDownload(item.task_id, item.stock_code)"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#D4A843] hover:text-[#F0C060] hover:bg-white/5 rounded-lg transition-colors"
                >
                  <Download :size="14" />下载 .md
                </button>
                <span v-else class="text-xs text-[#5C6E8A]">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!loading && items.length === 0" class="text-center py-16">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
          <TrendingUp :size="24" class="text-[#5C6E8A]" />
        </div>
        <p class="text-[#8B9CB5]">暂无分析记录</p>
        <router-link to="/analysis" class="inline-block mt-4 text-sm text-[#D4A843] hover:text-[#F0C060]">
          开始第一次分析 →
        </router-link>
      </div>
    </div>
  </div>
</template>
