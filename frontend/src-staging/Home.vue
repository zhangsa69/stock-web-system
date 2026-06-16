<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { redeemCode } from "../api/recharge";
import {
  Search, TrendingUp, FileText, Brain, Zap,
  Coins, Check, Key, AlertCircle, ArrowRight, Sparkles
} from "lucide-vue-next";

const router = useRouter();
const auth = useAuthStore();

const stockCode = ref("");
const redeemInput = ref("");
const redeemMsg = ref("");
const redeemOk = ref(false);
const redeeming = ref(false);

onMounted(async () => {
  if (auth.isLoggedIn) await auth.fetchBalance();
});

function startAnalysis() {
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
  redeeming.value = true; redeemMsg.value = "";
  try {
    const res = await redeemCode(code);
    redeemMsg.value = res.message; redeemOk.value = res.success;
    redeemInput.value = ""; await auth.fetchBalance();
  } catch (e: any) {
    redeemMsg.value = e.response?.data?.detail || "核销失败";
    redeemOk.value = false;
  } finally { redeeming.value = false; }
}

const features = [
  { icon: FileText, title: "全自动财报获取", desc: "A股+港股全上市公司，巨潮资讯网自动下载近5年年报及最新季报" },
  { icon: Brain, title: "AI 深度多维分析", desc: "自研 AI Agent 财务拆解、排雷检测、行业对标、管理层评估" },
  { icon: TrendingUp, title: "结构化投资报告", desc: "完整 Markdown 分析报告直发邮箱，含估值区间、风险预警、操作建议" },
];

const advantages = [
  { label: "数据覆盖", free: "手动查财报，费时费力", us: "A股+港股全自动，5年数据" },
  { label: "分析深度", free: "基本面指标罗列", us: "AI多维度：排雷/估值/DCF/行业对标" },
  { label: "报告质量", free: "零散信息，不成体系", us: "结构化报告直发邮箱，随时查阅" },
  { label: "更新速度", free: "季度报后需手动重新查", us: "一键重新分析，始终最新" },
  { label: "决策效率", free: "看财报→整理→分析→决策，数小时", us: "输入代码→5分钟→完整报告" },
];
</script>

<template>
  <div>
    <!-- ═══════════════ HERO BAND DARK ═══════════════ -->
    <section class="hero-band">
      <!-- Floating particles -->
      <div class="particles" aria-hidden="true">
        <div v-for="i in 20" :key="i" class="particle"
          :style="{
            left: (Math.random()*90+5)+'%',
            top: (Math.random()*80+10)+'%',
            animationDelay: (Math.random()*8)+'s',
            animationDuration: (6+Math.random()*6)+'s',
            width: (2+Math.random()*3)+'px',
            height: (2+Math.random()*3)+'px',
          }"
        />
      </div>

      <!-- Animated gradient blobs -->
      <div class="blob blob-1" />
      <div class="blob blob-2" />

      <div class="hero-content animate-fade-in-up">
        <!-- Eyebrow badge -->
        <div class="eyebrow">
          <Sparkles :size="14" />
          <span>AI-POWERED FINANCIAL ANALYSIS</span>
        </div>

        <h1>
          <span class="gradient-text">AI 股票财报分析</span>
        </h1>
        <p class="hero-sub">
          输入股票代码，AI Agent 自动下载财报，生成深度分析报告
        </p>

        <!-- Search Pill -->
        <div class="search-pill-wrapper">
          <div class="search-pill">
            <Search :size="20" class="search-icon" />
            <input
              v-model="stockCode"
              type="text"
              placeholder="输入股票代码，如 600519（贵州茅台）"
              @keyup.enter="startAnalysis"
            />
            <button
              @click="startAnalysis"
              :disabled="!stockCode.trim()"
              class="btn-primary"
            >
              开始分析 <ArrowRight :size="16" />
            </button>
          </div>
          <p class="search-hint">每次分析消耗 1 点券</p>
        </div>

        <!-- Quick codes -->
        <div class="quick-codes">
          <button
            v-for="code in ['600519','000858','00700','300750']"
            :key="code"
            @click="stockCode = code"
            class="quick-chip"
          >{{ code }}</button>
        </div>
      </div>
    </section>

    <!-- ═══════════════ FEATURES ═══════════════ -->
    <section class="features-section">
      <div class="section-inner">
        <h2 class="section-title animate-fade-in-up">平台核心能力</h2>
        <div class="features-grid stagger-children">
          <div
            v-for="(f, i) in features" :key="i"
            class="feature-card card-tilt"
          >
            <div class="feature-icon">
              <component :is="f.icon" :size="24" />
            </div>
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ═══════════════ COMPARISON TABLE ═══════════════ -->
    <section class="compare-section">
      <div class="section-inner">
        <h2 class="section-title animate-fade-in-up">为什么收费？</h2>
        <p class="section-desc">免费工具只能给你财务指标列表。我们调用真实 AI Agent 多轮推理——每次分析消耗大量算力。</p>
        <div class="compare-table animate-scale-in">
          <table>
            <thead>
              <tr>
                <th>对比维度</th>
                <th class="th-free">免费工具</th>
                <th class="th-us">本平台</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in advantages" :key="a.label">
                <td class="td-label">{{ a.label }}</td>
                <td class="td-free">{{ a.free }}</td>
                <td class="td-us">{{ a.us }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ═══════════════ RECHARGE ═══════════════ -->
    <section class="recharge-section">
      <div class="section-inner">
        <h2 class="section-title animate-fade-in-up">
          <Coins :size="28" class="inline-block mr-2" style="color:#0052ff" />充值中心
        </h2>
        <p class="section-desc">选择套餐 → 付款获得卡密 → 在此核销</p>

        <!-- Pricing cards -->
        <div class="pricing-grid stagger-children">
          <a href="https://68n.cn/YhVjH" target="_blank" class="pricing-card card-tilt">
            <div class="pricing-amount">1 <span class="unit">点券</span></div>
            <div class="pricing-label">体验套餐</div>
            <div class="pricing-cta">立即购买</div>
          </a>
          <a href="https://68n.cn/reygI" target="_blank" class="pricing-card featured card-tilt">
            <div class="featured-tag">推荐</div>
            <div class="pricing-amount">20 <span class="unit">点券</span></div>
            <div class="pricing-label">超值套餐</div>
            <div class="pricing-cta">立即购买</div>
          </a>
        </div>

        <!-- Redeem -->
        <div class="redeem-card animate-scale-in">
          <h3><Key :size="18" />核销充值卡密</h3>
          <div class="redeem-row">
            <input
              v-model="redeemInput"
              type="text"
              placeholder="粘贴充值卡密..."
              @keyup.enter="doRedeem"
            />
            <button @click="doRedeem" :disabled="!redeemInput.trim() || redeeming" class="btn-primary">
              {{ redeeming ? "核销中..." : "核销" }}
            </button>
          </div>
          <div v-if="redeemMsg" :class="['redeem-msg', redeemOk ? 'msg-ok' : 'msg-err']">
            <Check v-if="redeemOk" :size="14" />
            <AlertCircle v-else :size="14" />
            {{ redeemMsg }}
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* ── HERO ── */
.hero-band {
  position: relative;
  min-height: 92vh;
  display: flex; align-items: center; justify-content: center;
  background: var(--cb-surface-dark, #0a0b0d);
  overflow: hidden;
  padding: 120px 24px 80px;
}
.hero-content {
  position: relative; z-index: 10;
  max-width: 720px; width: 100%;
  text-align: center;
}
.eyebrow {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 16px; border-radius: 9999px;
  background: rgba(0,82,255,0.1);
  border: 1px solid rgba(0,82,255,0.2);
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-size: 11px; font-weight: 500;
  letter-spacing: 1.5px;
  color: rgba(0,82,255,0.9);
  margin-bottom: 32px;
}
.hero-band h1 {
  font-family: 'Inter', sans-serif;
  font-size: clamp(36px, 7vw, 64px);
  font-weight: 600;
  line-height: 1.05;
  letter-spacing: -1.6px;
  margin: 0 0 20px;
}
.gradient-text {
  background: linear-gradient(135deg, #0052ff 0%, #3b82f6 40%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-sub {
  font-family: 'Inter', sans-serif;
  font-size: 18px; font-weight: 400;
  color: rgba(255,255,255,0.55);
  margin: 0 0 40px;
  line-height: 1.6;
}
/* Search Pill */
.search-pill-wrapper {
  max-width: 560px; margin: 0 auto 28px;
}
.search-pill {
  display: flex; align-items: center;
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 9999px;
  padding: 4px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.search-pill:focus-within {
  border-color: #0052ff;
  box-shadow: 0 0 0 3px rgba(0,82,255,0.15);
}
.search-pill .search-icon {
  color: rgba(255,255,255,0.3);
  margin: 0 8px 0 16px; flex-shrink: 0;
}
.search-pill input {
  flex: 1;
  background: transparent; border: none; outline: none;
  color: #ffffff; font-size: 16px;
  font-family: 'Inter', sans-serif;
  padding: 12px 0;
}
.search-pill input::placeholder { color: rgba(255,255,255,0.3); }
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 10px 22px; border-radius: 9999px;
  border: none;
  background: #0052ff; color: #fff;
  font-family: 'Inter', sans-serif;
  font-weight: 600; font-size: 15px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.1s ease;
}
.btn-primary:hover { background: #0045d9; box-shadow: 0 4px 16px rgba(0,82,255,0.35); }
.btn-primary:active { transform: scale(0.97); }
.btn-primary:disabled { background: rgba(0,82,255,0.3); cursor: not-allowed; box-shadow: none; }
.search-hint {
  font-size: 12px; color: rgba(255,255,255,0.25);
  text-align: center; margin-top: 10px;
}
.quick-codes {
  display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;
}
.quick-chip {
  padding: 8px 20px; border-radius: 9999px;
  border: 1px solid rgba(255,255,255,0.1);
  background: transparent;
  color: rgba(255,255,255,0.45);
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-size: 14px; font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}
.quick-chip:hover {
  border-color: rgba(0,82,255,0.5);
  color: #0052ff;
  background: rgba(0,82,255,0.06);
}

/* Particles */
.particles { position: absolute; inset: 0; }
.particle {
  position: absolute;
  border-radius: 50%;
  background: #0052ff;
  opacity: 0;
  animation: particle-float 8s ease-in-out infinite;
}
@keyframes particle-float {
  0% { opacity: 0; transform: translate(0,0) scale(0.5); }
  20% { opacity: 0.5; }
  80% { opacity: 0.2; }
  100% { opacity: 0; transform: translate(var(--drift,30px), var(--drift-y,-40px)) scale(0.2); }
}

/* Gradient blobs */
.blob {
  position: absolute; border-radius: 50%; filter: blur(100px); opacity: 0.12;
}
.blob-1 {
  width: 400px; height: 400px;
  background: #0052ff;
  top: 10%; left: 5%;
  animation: blob-move 12s ease-in-out infinite alternate;
}
.blob-2 {
  width: 500px; height: 500px;
  background: #7c3aed;
  bottom: 5%; right: 5%;
  animation: blob-move 15s ease-in-out infinite alternate-reverse;
}
@keyframes blob-move {
  0% { transform: translate(0,0) scale(1); }
  50% { transform: translate(30px,-20px) scale(1.08); }
  100% { transform: translate(-20px,15px) scale(0.95); }
}

/* ── SECTION BASE ── */
.section-inner {
  max-width: 1200px; margin: 0 auto; padding: 0 24px;
}
.section-title {
  font-family: 'Inter', sans-serif;
  font-size: 36px; font-weight: 600;
  color: #ffffff;
  text-align: center;
  margin: 0 0 12px;
  letter-spacing: -0.5px;
}
.section-desc {
  font-size: 16px; color: rgba(255,255,255,0.4);
  text-align: center; max-width: 600px;
  margin: 0 auto 48px; line-height: 1.6;
}

/* ── FEATURES ── */
.features-section {
  padding: 96px 0;
  background: linear-gradient(180deg, #0a0b0d 0%, #111318 100%);
}
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 48px;
}
.feature-card {
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px;
  padding: 36px 32px;
  transition: all 0.3s ease;
}
.feature-card:hover {
  border-color: rgba(0,82,255,0.25);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.3), 0 0 40px rgba(0,82,255,0.06);
}
.feature-icon {
  width: 48px; height: 48px;
  border-radius: 12px;
  background: rgba(0,82,255,0.1);
  display: flex; align-items: center; justify-content: center;
  color: #0052ff;
  margin-bottom: 20px;
}
.feature-card h3 {
  font-family: 'Inter', sans-serif;
  font-size: 18px; font-weight: 600;
  color: #ffffff;
  margin: 0 0 10px;
}
.feature-card p {
  font-size: 14px; color: rgba(255,255,255,0.45);
  line-height: 1.6; margin: 0;
}

/* ── COMPARE TABLE ── */
.compare-section {
  padding: 96px 0;
  background: #0a0b0d;
}
.compare-table {
  max-width: 900px; margin: 0 auto;
  border-radius: 24px; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.06);
}
.compare-table table {
  width: 100%; border-collapse: collapse;
}
.compare-table thead tr {
  background: var(--cb-surface-dark-elevated, #16181c);
}
.compare-table th {
  text-align: left;
  padding: 16px 24px;
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-size: 11px; font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(255,255,255,0.35);
}
.th-free { color: rgba(207,32,47,0.6) !important; }
.th-us { color: rgba(0,82,255,0.7) !important; }
.compare-table td {
  padding: 14px 24px;
  font-size: 14px;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.td-label { color: rgba(255,255,255,0.7); font-weight: 500; }
.td-free { color: rgba(255,255,255,0.35); }
.td-us { color: rgba(255,255,255,0.55); }
.compare-table tbody tr:hover {
  background: rgba(255,255,255,0.015);
}

/* ── RECHARGE ── */
.recharge-section {
  padding: 96px 0;
  background: linear-gradient(180deg, #111318 0%, #0a0b0d 100%);
}
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  max-width: 600px; margin: 0 auto 48px;
}
.pricing-card {
  display: block;
  text-decoration: none;
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px;
  padding: 32px 24px;
  text-align: center;
  transition: all 0.3s ease;
  position: relative;
}
.pricing-card:hover {
  border-color: rgba(0,82,255,0.25);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.pricing-amount {
  font-family: 'Inter', sans-serif;
  font-size: 42px; font-weight: 700;
  color: #ffffff;
  letter-spacing: -1px;
  line-height: 1;
  margin-bottom: 8px;
}
.pricing-amount .unit {
  font-size: 18px; font-weight: 500;
  color: rgba(255,255,255,0.4);
  margin-left: 4px;
}
.pricing-label {
  font-size: 14px; color: rgba(255,255,255,0.35);
  margin-bottom: 20px;
}
.pricing-cta {
  display: inline-block;
  padding: 10px 24px;
  border-radius: 9999px;
  background: rgba(0,82,255,0.1);
  color: #0052ff;
  font-family: 'Inter', sans-serif;
  font-weight: 600; font-size: 14px;
  border: 1px solid rgba(0,82,255,0.2);
  transition: all 0.2s ease;
}
.pricing-card:hover .pricing-cta { background: #0052ff; color: #fff; border-color: #0052ff; }

.pricing-card.featured {
  border-color: rgba(0,82,255,0.3);
  background: linear-gradient(135deg, rgba(0,82,255,0.08), rgba(124,58,237,0.06));
}
.featured-tag {
  position: absolute; top: 16px; right: 16px;
  padding: 4px 12px;
  border-radius: 9999px;
  background: #0052ff;
  color: #fff;
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.5px;
}

/* ── REDEEM ── */
.redeem-card {
  max-width: 600px; margin: 0 auto;
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px;
  padding: 32px;
}
.redeem-card h3 {
  display: flex; align-items: center; gap: 8px;
  font-family: 'Inter', sans-serif;
  font-size: 18px; font-weight: 600;
  color: #ffffff;
  margin: 0 0 20px;
}
.redeem-row {
  display: flex; gap: 12px;
}
.redeem-row input {
  flex: 1;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 12px 16px;
  color: #fff; font-size: 15px;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: border-color 0.2s ease;
}
.redeem-row input:focus { border-color: #0052ff; }
.redeem-row input::placeholder { color: rgba(255,255,255,0.25); }
.redeem-msg {
  margin-top: 12px;
  padding: 12px 16px; border-radius: 12px;
  font-size: 14px;
  display: flex; align-items: center; gap: 8px;
}
.msg-ok { background: rgba(5,177,105,0.1); color: #05b169; border: 1px solid rgba(5,177,105,0.2); }
.msg-err { background: rgba(207,32,47,0.1); color: #cf202f; border: 1px solid rgba(207,32,47,0.2); }

@media (max-width: 768px) {
  .features-grid { grid-template-columns: 1fr; }
  .pricing-grid { grid-template-columns: 1fr; }
}

/* Bring in global animation classes */
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
.stagger-children > * { opacity: 0; animation: fadeInUp 0.6s cubic-bezier(0.16,1,0.3,1) forwards; }
.stagger-children > *:nth-child(1) { animation-delay: 0ms; }
.stagger-children > *:nth-child(2) { animation-delay: 80ms; }
.stagger-children > *:nth-child(3) { animation-delay: 160ms; }
</style>
