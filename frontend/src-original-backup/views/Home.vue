<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { redeemCode } from "../api/recharge";
import {
  Search, TrendingUp, FileText, Brain, Shield, Zap,
  Coins, ExternalLink, Check, Gift, Key, AlertCircle,
} from "lucide-vue-next";

const router = useRouter();
const auth = useAuthStore();

const stockCode = ref("");
const redeemInput = ref("");
const redeemMsg = ref("");
const redeemOk = ref(false);
const redeeming = ref(false);

onMounted(async () => {
  if (auth.isLoggedIn) {
    await auth.fetchBalance();
  }
});

async function startAnalysis() {
  const code = stockCode.value.trim();
  if (!code) return;
  if (auth.balance <= 0) {
    redeemMsg.value = "点券余额不足，请先充值";
    redeemOk.value = false;
    return;
  }
  router.push({ path: "/analysis", query: { code } });
}

async function doRedeem() {
  const code = redeemInput.value.trim();
  if (!code) return;
  redeeming.value = true;
  redeemMsg.value = "";
  try {
    const res = await redeemCode(code);
    redeemMsg.value = res.message;
    redeemOk.value = res.success;
    redeemInput.value = "";
    await auth.fetchBalance();
  } catch (e: any) {
    redeemMsg.value = e.response?.data?.detail || "核销失败，请检查卡密";
    redeemOk.value = false;
  } finally {
    redeeming.value = false;
  }
}

const features = [
  {
    icon: FileText,
    title: "全自动财报获取",
    desc: "覆盖 A 股 + 港股全部上市公司，从巨潮资讯网自动下载近 5 年年报及最新季报，无需手动上传",
  },
  {
    icon: Brain,
    title: "AI 深度多维分析",
    desc: "基于自研 AI Agent 进行财务指标拆解、排雷检测、行业对标、管理层评估，非简单指标解读",
  },
  {
    icon: TrendingUp,
    title: "结构化投资报告",
    desc: "输出完整 Markdown 分析报告直发邮箱，包含估值区间、风险预警、操作建议，可直接用于决策",
  },
];

const advantages = [
  { label: "数据覆盖", free: "手动查财报，费时费力", us: "A股+港股全自动，5年数据" },
  { label: "分析深度", free: "基本面指标罗列", us: "AI多维度：排雷/估值/DCF/行业对标" },
  { label: "报告质量", free: "零散信息，不成体系", us: "结构化报告直发邮箱，随时查阅" },
  { label: "更新速度", free: "季度报后需手动重新查", us: "一键重新分析，始终最新" },
  { label: "决策效率", free: "看财报 → 整理 → 分析 → 决策，数小时", us: "输入代码 → 5分钟 → 完整报告" },
];
</script>

<template>
  <div>
    <!-- Hero Banner -->
    <section class="relative min-h-[92vh] flex items-center justify-center overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-b from-[#0A1929] via-[#132238] to-[#0D1B2A]" />
      <div class="absolute inset-0 opacity-30">
        <div class="absolute top-20 left-[10%] w-72 h-72 bg-[#1A3A6B] rounded-full blur-[120px]" />
        <div class="absolute bottom-20 right-[10%] w-96 h-96 bg-[#D4A843]/20 rounded-full blur-[120px]" />
      </div>

      <div class="relative z-10 max-w-4xl mx-auto px-6 text-center">
        <h1 class="text-4xl md:text-6xl font-bold mb-6 leading-tight">
          <span class="bg-gradient-to-r from-[#F0C060] to-[#D4A843] bg-clip-text text-transparent">
            AI 股票财报分析平台
          </span>
        </h1>
        <p class="text-lg md:text-xl text-[#8B9CB5] mb-3 max-w-2xl mx-auto leading-relaxed">
          一键输入股票代码，AI Agent 自动下载财报并生成深度分析报告
        </p>
        <!-- 余额提示 -->
        <div v-if="auth.balance > 0" class="mb-6 inline-flex items-center gap-1.5 px-4 py-1.5 bg-[#D4A843]/10 border border-[#D4A843]/30 rounded-full">
          <Coins :size="14" class="text-[#F0C060]" />
          <span class="text-sm text-[#F0C060]">余额：<strong>{{ auth.balance }}</strong> 点券</span>
        </div>
        <div v-else class="mb-6">
          <span class="inline-flex items-center gap-1.5 px-4 py-1.5 bg-red-500/10 border border-red-500/30 rounded-full text-sm text-red-400">
            <AlertCircle :size="14" />
            点券余额不足，请先充值
          </span>
        </div>

        <!-- 搜索框 -->
        <div class="max-w-xl mx-auto relative">
          <div class="flex items-center bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl overflow-hidden focus-within:border-[#D4A843] transition-colors">
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
              :disabled="!stockCode.trim()"
              class="mr-2 px-6 py-2.5 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
            >
              开始分析（-1 点券）
            </button>
          </div>
          <p class="text-xs text-[#5C6E8A] mt-2">每次分析消耗 1 点券，余额不足请充值</p>
        </div>
      </div>
    </section>

    <!-- 为什么收费 — 对比表 -->
    <section class="py-20 px-6 bg-[#0A1628]">
      <div class="max-w-5xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-4 text-[#E8EDF5]">为什么收费？</h2>
        <p class="text-center text-[#8B9CB5] mb-12 max-w-2xl mx-auto leading-relaxed">
          免费工具只能给你一堆财务指标让你自己看。我们调用真实 AI Agent 进行多轮推理分析，
          每次分析都消耗大量算力——这钱花得值。
        </p>

        <!-- 对比表格 -->
        <div class="overflow-x-auto rounded-2xl border border-white/10">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-[#132238]">
                <th class="text-left px-6 py-4 text-[#8B9CB5] font-medium">对比维度</th>
                <th class="text-left px-6 py-4 text-red-400/80 font-medium">❌ 免费工具</th>
                <th class="text-left px-6 py-4 text-[#F0C060] font-medium">✅ 本平台</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5">
              <tr v-for="a in advantages" :key="a.label" class="hover:bg-white/[0.02]">
                <td class="px-6 py-3.5 text-[#E8EDF5] font-medium">{{ a.label }}</td>
                <td class="px-6 py-3.5 text-[#8B9CB5]">{{ a.free }}</td>
                <td class="px-6 py-3.5 text-[#C4D0E0]">{{ a.us }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 充值模块 -->
    <section class="py-20 px-6">
      <div class="max-w-2xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-4 text-[#E8EDF5]">
          <Coins :size="28" class="inline text-[#F0C060] mr-2" />充值中心
        </h2>
        <p class="text-center text-[#8B9CB5] mb-10">选择套餐 → 付款获得卡密 → 在此核销</p>

        <!-- 两个充值按钮 -->
        <div class="grid grid-cols-2 gap-4 mb-10">
          <a
            href="https://68n.cn/YhVjH"
            target="_blank"
            class="group block bg-[#132238] border border-white/10 rounded-2xl p-6 hover:border-[#D4A843]/50 hover:-translate-y-1 transition-all duration-300 no-underline"
          >
            <div class="text-center">
              <div class="text-3xl font-bold text-[#E8EDF5] mb-1">1 点券</div>
              <div class="text-[#8B9CB5] text-sm mb-4">体验套餐</div>
              <div class="inline-flex items-center gap-1 text-[#F0C060] group-hover:text-[#D4A843] transition-colors">
                立即购买 <ExternalLink :size="14" />
              </div>
            </div>
          </a>

          <a
            href="https://68n.cn/reygI"
            target="_blank"
            class="group block bg-gradient-to-br from-[#D4A843]/10 to-[#F0C060]/5 border border-[#D4A843]/30 rounded-2xl p-6 hover:border-[#D4A843]/70 hover:-translate-y-1 transition-all duration-300 no-underline relative overflow-hidden"
          >
            <div class="absolute top-3 right-3 bg-[#F0C060] text-[#0A1929] text-xs font-bold px-2 py-0.5 rounded-full">
              推荐
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-[#E8EDF5] mb-1">20 点券</div>
              <div class="text-[#8B9CB5] text-sm mb-4">超值套餐</div>
              <div class="inline-flex items-center gap-1 text-[#F0C060] group-hover:text-[#D4A843] transition-colors">
                立即购买 <ExternalLink :size="14" />
              </div>
            </div>
          </a>
        </div>

        <p class="text-center text-xs text-[#5C6E8A] mb-8">
          点击上方按钮跳转至发卡网站付款，付款成功后复制获得的充值卡密，粘贴到下方核销
        </p>

        <!-- 核销输入 -->
        <div class="bg-[#132238]/50 border border-white/10 rounded-2xl p-6">
          <h3 class="text-lg font-semibold text-[#E8EDF5] mb-4 flex items-center gap-2">
            <Key :size="18" class="text-[#D4A843]" />核销充值卡密
          </h3>
          <div class="flex gap-3">
            <input
              v-model="redeemInput"
              type="text"
              placeholder="粘贴充值卡密..."
              class="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] text-sm focus:border-[#D4A843] outline-none transition-colors"
              @keyup.enter="doRedeem"
            />
            <button
              @click="doRedeem"
              :disabled="!redeemInput.trim() || redeeming"
              class="px-6 py-3 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity text-sm whitespace-nowrap"
            >
              {{ redeeming ? "核销中..." : "核 销" }}
            </button>
          </div>
          <div
            v-if="redeemMsg"
            :class="[
              'mt-3 text-sm px-3 py-2 rounded-lg',
              redeemOk ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400',
            ]"
          >
            <Check v-if="redeemOk" :size="14" class="inline mr-1" />
            <AlertCircle v-else :size="14" class="inline mr-1" />
            {{ redeemMsg }}
          </div>
        </div>
      </div>
    </section>

    <!-- 功能亮点 -->
    <section class="py-20 px-6 bg-[#0A1628]">
      <div class="max-w-6xl mx-auto">
        <h2 class="text-3xl font-bold text-center mb-16 text-[#E8EDF5]">平台核心能力</h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="(f, i) in features"
            :key="i"
            class="group bg-[#132238]/50 backdrop-blur-sm border border-white/5 rounded-2xl p-8 hover:border-[#D4A843]/30 hover:-translate-y-1 transition-all duration-300"
          >
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-[#D4A843]/20 to-[#F0C060]/20 flex items-center justify-center mb-5">
              <component :is="f.icon" :size="24" class="text-[#F0C060]" />
            </div>
            <h3 class="text-lg font-semibold text-[#E8EDF5] mb-3">{{ f.title }}</h3>
            <p class="text-sm text-[#8B9CB5] leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 快捷代码 -->
    <section class="py-16 px-6">
      <div class="max-w-2xl mx-auto text-center">
        <p class="text-[#8B9CB5] mb-5 text-sm">试试这些热门股票：</p>
        <div class="flex items-center justify-center gap-3 flex-wrap">
          <button
            v-for="code in ['600519', '000858', '00700', '300750']"
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
