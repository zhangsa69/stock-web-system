<script setup lang="ts">
import { computed } from "vue";
import { Download, Copy, Share2 } from "lucide-vue-next";

const props = defineProps<{
  report: string;
  stockCode: string;
  stockName: string;
}>();

// 简单的 Markdown 转 HTML（生产环境应使用 marked 等库）
function simpleMarkdownToHtml(md: string): string {
  return md
    .replace(/### (.+)/g, '<h3 class="text-lg font-semibold text-[#E8EDF5] mt-6 mb-3">$1</h3>')
    .replace(/## (.+)/g, '<h2 class="text-xl font-bold text-[#E8EDF5] mt-8 mb-4 border-b border-white/10 pb-2">$1</h2>')
    .replace(/# (.+)/g, '<h1 class="text-2xl font-bold text-[#F0C060] mt-8 mb-4">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong class="text-[#F0C060]">$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)/gm, '<li class="text-[#8B9CB5] ml-4 mb-1 list-disc">$1</li>')
    .replace(/\n/g, '<br/>');
}

const htmlContent = computed(() => simpleMarkdownToHtml(props.report));

function handleCopy() {
  navigator.clipboard.writeText(props.report);
}

function handleDownload() {
  const blob = new Blob([props.report], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${props.stockCode}_分析报告_${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<template>
  <div class="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden animate-slide-up">
    <!-- 报告头部 -->
    <div class="border-b border-white/5 px-8 py-5 flex items-center justify-between">
      <div>
        <h3 class="text-lg font-bold text-[#E8EDF5]">分析报告</h3>
        <p class="text-sm text-[#5C6E8A] mt-0.5">{{ stockName }} ({{ stockCode }})</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="handleCopy"
          class="p-2 rounded-lg bg-white/5 border border-white/10 text-[#8B9CB5] hover:text-[#E8EDF5] hover:border-[#D4A843]/30 transition-colors"
          title="复制报告"
        >
          <Copy :size="16" />
        </button>
        <button
          @click="handleDownload"
          class="p-2 rounded-lg bg-white/5 border border-white/10 text-[#8B9CB5] hover:text-[#E8EDF5] hover:border-[#D4A843]/30 transition-colors"
          title="下载报告"
        >
          <Download :size="16" />
        </button>
      </div>
    </div>

    <!-- 报告内容 -->
    <div class="px-8 py-6">
      <div
        class="prose prose-invert max-w-none text-sm leading-relaxed text-[#8B9CB5]"
        v-html="htmlContent"
      />
    </div>

    <!-- 免责声明 -->
    <div class="border-t border-white/5 px-8 py-4 bg-[#0A1929]/50">
      <p class="text-xs text-[#5C6E8A]">
        ⚠️ 免责声明：本报告由 AI 自动生成，仅供参考学习，不构成任何投资建议。投资有风险，入市需谨慎。
      </p>
    </div>
  </div>
</template>
