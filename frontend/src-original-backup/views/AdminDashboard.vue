<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getDashboard, type DashboardStats } from "../api/admin";
import {
  Users, Ticket, TrendingUp, Activity,
  Shield, CreditCard, BarChart3, Loader2,
} from "lucide-vue-next";

const router = useRouter();
const stats = ref<DashboardStats | null>(null);
const loading = ref(true);

onMounted(async () => {
  const token = localStorage.getItem("admin_token");
  if (!token) { router.push("/admin/login"); return; }
  try {
    stats.value = await getDashboard();
  } catch(e) {
    if ((e as any)?.response?.status === 401 || (e as any)?.response?.status === 403) {
      localStorage.removeItem("admin_token");
      router.push("/admin/login");
    }
  } finally {
    loading.value = false;
  }
});

function go(path: string) { router.push(path); }
function doLogout() { localStorage.removeItem("admin_token"); router.push("/admin/login"); }
</script>

<template>
  <div class="min-h-screen bg-[#0A1628]">
    <!-- Header -->
    <header class="bg-[#0D1B2A] border-b border-white/10 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Shield :size="20" class="text-[#F0C060]" />
        <h1 class="text-lg font-bold text-[#E8EDF5]">管理后台</h1>
      </div>
      <nav class="flex items-center gap-4 text-sm">
        <button @click="go('/admin/dashboard')" class="text-[#F0C060] font-medium">总览</button>
        <button @click="go('/admin/codes')" class="text-[#8B9CB5] hover:text-[#E8EDF5]">卡密管理</button>
        <button @click="go('/admin/users')" class="text-[#8B9CB5] hover:text-[#E8EDF5]">用户管理</button>
        <button @click="doLogout" class="text-red-400 hover:text-red-300 ml-4">退出</button>
      </nav>
    </header>

    <main class="max-w-6xl mx-auto px-6 py-10">
      <Loader2 v-if="loading" :size="32" class="mx-auto mt-20 text-[#8B9CB5] animate-spin" />

      <template v-if="stats">
        <h2 class="text-2xl font-bold text-[#E8EDF5] mb-8">数据总览</h2>

        <!-- 卡片网格 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div class="bg-[#132238] border border-white/10 rounded-2xl p-5">
            <div class="flex items-center gap-2 mb-3"><Users :size="16" class="text-[#D4A843]" /><span class="text-xs text-[#8B9CB5]">注册用户</span></div>
            <div class="text-3xl font-bold text-[#E8EDF5]">{{ stats.total_users }}</div>
          </div>
          <div class="bg-[#132238] border border-white/10 rounded-2xl p-5">
            <div class="flex items-center gap-2 mb-3"><CreditCard :size="16" class="text-[#D4A843]" /><span class="text-xs text-[#8B9CB5]">卡密总数</span></div>
            <div class="text-3xl font-bold text-[#E8EDF5]">{{ stats.total_codes }}</div>
            <div class="text-xs text-[#8B9CB5] mt-1">已用 {{ stats.used_codes }} · 未用 {{ stats.unused_codes }}</div>
          </div>
          <div class="bg-[#132238] border border-white/10 rounded-2xl p-5">
            <div class="flex items-center gap-2 mb-3"><TrendingUp :size="16" class="text-[#D4A843]" /><span class="text-xs text-[#8B9CB5]">分析次数</span></div>
            <div class="text-3xl font-bold text-[#E8EDF5]">{{ stats.total_analyses }}</div>
            <div class="text-xs text-[#8B9CB5] mt-1">完成 {{ stats.completed_analyses }} · 失败 {{ stats.failed_analyses }}</div>
          </div>
          <div class="bg-[#132238] border border-white/10 rounded-2xl p-5">
            <div class="flex items-center gap-2 mb-3"><Ticket :size="16" class="text-[#D4A843]" /><span class="text-xs text-[#8B9CB5]">点券消耗</span></div>
            <div class="text-3xl font-bold text-[#E8EDF5]">{{ stats.total_tickets_used }}</div>
            <div class="text-xs text-[#8B9CB5] mt-1">已售 {{ stats.total_tickets_sold }} 点券</div>
          </div>
        </div>

        <!-- 快捷入口 -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button @click="go('/admin/codes')"
            class="group bg-[#132238]/50 border border-white/10 rounded-2xl p-6 hover:border-[#D4A843]/30 transition-all text-left">
            <CreditCard :size="24" class="text-[#F0C060] mb-3 group-hover:scale-110 transition-transform" />
            <h3 class="font-semibold text-[#E8EDF5] mb-1">卡密管理</h3>
            <p class="text-sm text-[#8B9CB5]">导入 / 查看 / 搜索卡密及核销状态</p>
          </button>
          <button @click="go('/admin/users')"
            class="group bg-[#132238]/50 border border-white/10 rounded-2xl p-6 hover:border-[#D4A843]/30 transition-all text-left">
            <Users :size="24" class="text-[#F0C060] mb-3 group-hover:scale-110 transition-transform" />
            <h3 class="font-semibold text-[#E8EDF5] mb-1">用户管理</h3>
            <p class="text-sm text-[#8B9CB5]">查看用户列表 / 点券余额 / 分析历史</p>
          </button>
          <button @click="go('/admin/codes')"
            class="group bg-[#132238]/50 border border-white/10 rounded-2xl p-6 hover:border-[#D4A843]/30 transition-all text-left">
            <Activity :size="24" class="text-[#F0C060] mb-3 group-hover:scale-110 transition-transform" />
            <h3 class="font-semibold text-[#E8EDF5] mb-1">数据趋势</h3>
            <p class="text-sm text-[#8B9CB5]">日活 / 消费趋势 / 营收统计（即将上线）</p>
          </button>
        </div>
      </template>
    </main>
  </div>
</template>
