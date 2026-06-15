<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { Search, TrendingUp, FileText, Brain, Shield, Zap } from "lucide-vue-next";

const router = useRouter();
const stockCode = ref("");
const userEmail = ref("");

function startAnalysis() {
  const code = stockCode.value.trim();
  const email = userEmail.value.trim();
  if (!code || !email) return;
  router.push({ path: "/analysis", query: { code, email } });
}

const features = [
  {
    icon: FileText,
    title: "智能财报下载",
    desc: "自动从巨潮资讯网获取近5年年报及最新季报，覆盖A股及港股市场全部上市公司",
  },
  {
    icon: Brain,
    title: "AI 深度分析",
    desc: "基于自学习 AI Agent 进行多维度财务分析，识别财务风险，评估企业真实价值",
  },
  {
    icon: TrendingUp,
    title: "专业投资建议",
    desc: "结合财务指标、行业对比、管理层分析，输出结构化的投资参考报告",
  },
];
</script>

<template>
  <div>
    <!-- Hero Banner -->
    <section
      class="relative min-h-[85vh] flex items-center justify-center overflow-hidden"
    >
      <!-- 背景渐变 + 粒子装饰 -->
      <div class="absolute inset-0 bg-gradient-to-b from-[#0A1929] via-[#132238] to-[#0D1B2A]" />
      <div class="absolute inset-0 opacity-30">
        <div
          class="absolute top-20 left-[10%] w-72 h-72 bg-[#1A3A6B] rounded-full blur-[120px]"
        />
        <div
          class="absolute bottom-20 right-[10%] w-96 h-96 bg-[#D4A843]/20 rounded-full blur-[120px]"
        />
      </div>

      <div class="relative z-10 max-w-4xl mx-auto px-6 text-center">
        <h1 class="text-4xl md:text-6xl font-bold mb-6 leading-tight">
          <span class="bg-gradient-to-r from-[#F0C060] to-[#D4A843] bg-clip-text text-transparent">
            AI 股票财报分析平台
          </span>
        </h1>
        <p class="text-lg md:text-xl text-[#8B9CB5] mb-10 max-w-2xl mx-auto leading-relaxed">
          一键输入股票代码，AI Agent 自动下载财报并生成深度分析报告，让投资决策更智慧
        </p>

        <!-- 搜索框 -->
        <div class="max-w-xl mx-auto relative animate-slide-up">
          <div
            class="flex items-center bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl overflow-hidden focus-within:border-[#D4A843] transition-colors"
          >
            <Search :size="20" class="ml-5 text-[#8B9CB5]" />
            <input
              v-model="stockCode"
              type="text"
              placeholder="输入股票代码，如 600519（贵州茅台）"
              class="flex-1 bg-transparent border-none outline-none px-4 py-4 text-white placeholder:text-[#5C6E8A] text-base"
              @keyup.enter="startAnalysis"
            />
            <button
              @click="startAnalysis"
              :disabled="!stockCode.trim() || !userEmail.trim()"
              class="mr-2 px-6 py-2.5 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              开始分析
            </button>
          </div>
          <!-- 邮箱输入框 -->
          <div class="max-w-xl mx-auto mt-4">
            <input
              v-model="userEmail"
              type="email"
              placeholder="输入您的邮箱（必填，分析完成后发送报告）"
              class="w-full bg-white/10 backdrop-blur-md border border-white/20 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] text-sm focus:border-[#D4A843] outline-none transition-colors"
              @keyup.enter="startAnalysis"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- 功能亮点 -->
    <section class="py-24 px-6 bg-[#0A1628]">
      <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-16 text-[#E8EDF5]">
          为什么选择我们
        </h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="(f, i) in features"
            :key="i"
            class="group bg-[#132238]/50 backdrop-blur-sm border border-white/5 rounded-2xl p-8 hover:border-[#D4A843]/30 hover:-translate-y-1 transition-all duration-300"
          >
            <div
              class="w-12 h-12 rounded-xl bg-gradient-to-br from-[#D4A843]/20 to-[#F0C060]/20 flex items-center justify-center mb-5"
            >
              <component :is="f.icon" :size="24" class="text-[#F0C060]" />
            </div>
            <h3 class="text-lg font-semibold text-[#E8EDF5] mb-3">{{ f.title }}</h3>
            <p class="text-sm text-[#8B9CB5] leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20 px-6">
      <div class="max-w-2xl mx-auto text-center">
        <h2 class="text-3xl font-bold text-[#E8EDF5] mb-4">立即体验</h2>
        <p class="text-[#8B9CB5] mb-8">输入任意 A 股或港股代码，即刻获得 AI 财务分析报告</p>
        <div class="flex items-center justify-center gap-4 flex-wrap">
          <button
            v-for="code in ['600519', '000858', '00700']"
            :key="code"
            @click="stockCode = code"
            class="px-5 py-2.5 bg-white/5 border border-white/10 rounded-xl text-[#8B9CB5] hover:border-[#D4A843]/50 hover:text-[#F0C060] transition-all text-sm"
          >
            {{ code }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
