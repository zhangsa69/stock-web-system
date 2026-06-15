<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { Download, Copy } from "lucide-vue-next";

const props = defineProps<{
  report: string;
  htmlReport?: string | null;
  stockCode: string;
  stockName: string;
}>();

const iframeRef = ref<HTMLIFrameElement | null>(null);

// 简单 Markdown 转 HTML（兜底）
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

// 提取 md2html 生成的 <body> 内容
function extractBody(html: string): string {
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  if (bodyMatch) return bodyMatch[1];
  // 如果没 body 标签，去掉 html/head 标签后返回
  return html
    .replace(/<!DOCTYPE[^>]*>/i, '')
    .replace(/<html[^>]*>/i, '')
    .replace(/<\/html>/i, '')
    .replace(/<head>[\s\S]*?<\/head>/i, '');
}

// 构建 iframe 内容：如果是完整 HTML 文档，用 srcdoc 独立渲染
const iframeContent = computed(() => {
  if (props.htmlReport) {
    // md2html 生成的是完整 HTML 文档，用 iframe srcdoc
    return props.htmlReport;
  }
  // 兜底：包裹简单渲染的 Markdown
  return `<html><body style="background:#0D1B2A;color:#8B9CB5;font-family:system-ui,sans-serif;padding:24px;line-height:1.8">${simpleMarkdownToHtml(props.report)}</body></html>`;
});

const useIframe = computed(() => !!props.htmlReport);

// iframe 自适应高度
function adjustIframeHeight() {
  if (iframeRef.value) {
    try {
      const doc = iframeRef.value.contentDocument;
      if (doc && doc.body) {
        const h = doc.body.scrollHeight;
        iframeRef.value.style.height = Math.max(h + 40, 400) + 'px';
      }
    } catch (_) {}
  }
}

onMounted(() => {
  if (useIframe.value) {
    iframeRef.value?.addEventListener('load', adjustIframeHeight);
  }
});

watch(useIframe, (val) => {
  if (val) {
    setTimeout(() => {
      iframeRef.value?.addEventListener('load', adjustIframeHeight);
    }, 100);
  }
});

// 提取 body 内容用于预览（非 iframe 模式）
const htmlContent = computed(() => {
  if (props.htmlReport) {
    return extractBody(props.htmlReport);
  }
  return simpleMarkdownToHtml(props.report);
});

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

    <!-- 报告内容：iframe 独立渲染完整 HTML -->
    <div class="px-2 py-2">
      <iframe
        v-if="useIframe"
        ref="iframeRef"
        :srcdoc="iframeContent"
        class="w-full border-0 rounded-lg"
        style="min-height:400px;"
        sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        @load="adjustIframeHeight"
      />
      <!-- 兜底：无 htmlReport 时用 v-html -->
      <div
        v-else
        class="px-6 py-4 prose prose-invert max-w-none text-sm leading-relaxed text-[#8B9CB5]"
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
