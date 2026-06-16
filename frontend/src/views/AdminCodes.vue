<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { getCodes, importCodes, type CodeItem } from "../api/admin";
import {
  Shield, CreditCard, Upload, Search, Loader2,
  Check, X, ChevronLeft, ChevronRight, Download,
} from "lucide-vue-next";

const router = useRouter();
const codes = ref<CodeItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 50;
const search = ref("");
const usedFilter = ref("all");
const loading = ref(false);

const totalPages = computed(() => Math.ceil(total.value / pageSize));

// 导入
const importFile = ref<File | null>(null);
const importValue = ref(1);
const importing = ref(false);
const importMsg = ref("");
const importOk = ref(false);

onMounted(() => {
  if (!localStorage.getItem("admin_token")) { router.push("/admin/login"); return; }
  fetchCodes();
});

async function fetchCodes() {
  loading.value = true;
  try {
    const res = await getCodes({ page: page.value, page_size: pageSize, search: search.value, used_filter: usedFilter.value });
    codes.value = res.items;
    total.value = res.total;
  } catch(e: any) {
    if (e?.response?.status === 401) { localStorage.removeItem("admin_token"); router.push("/admin/login"); }
  } finally {
    loading.value = false;
  }
}

function onSearch() { page.value = 1; fetchCodes(); }
function onFilter(f: string) { usedFilter.value = f; page.value = 1; fetchCodes(); }
function prevPage() { if (page.value > 1) { page.value--; fetchCodes(); } }
function nextPage() { if (page.value < totalPages.value) { page.value++; fetchCodes(); } }

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  importFile.value = target.files?.[0] || null;
}

async function doImport() {
  if (!importFile.value) return;
  importing.value = true;
  importMsg.value = "";
  try {
    const res = await importCodes(importFile.value, importValue.value);
    importMsg.value = res.message;
    importOk.value = true;
    importFile.value = null;
    fetchCodes();
  } catch(e: any) {
    importMsg.value = e.response?.data?.detail || "导入失败";
    importOk.value = false;
  } finally {
    importing.value = false;
  }
}

function go(p: string) { router.push(p); }
function doLogout() { localStorage.removeItem("admin_token"); router.push("/admin/login"); }
function maskCode(c: string) { return c.slice(0, 4) + "****" + c.slice(-4); }
</script>

<template>
  <div class="min-h-screen bg-[#0A1628]">
    <header class="bg-[#0D1B2A] border-b border-white/10 px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <Shield :size="20" class="text-[#F0C060]" />
        <h1 class="text-lg font-bold text-[#E8EDF5]">管理后台</h1>
      </div>
      <nav class="flex items-center gap-4 text-sm">
        <button @click="go('/admin/dashboard')" class="text-[#8B9CB5] hover:text-[#E8EDF5]">总览</button>
        <button @click="go('/admin/codes')" class="text-[#F0C060] font-medium">卡密管理</button>
        <button @click="go('/admin/users')" class="text-[#8B9CB5] hover:text-[#E8EDF5]">用户管理</button>
        <button @click="doLogout" class="text-red-400 hover:text-red-300 ml-4">退出</button>
      </nav>
    </header>

    <main class="max-w-6xl mx-auto px-6 py-10">
      <h2 class="text-2xl font-bold text-[#E8EDF5] mb-8">卡密管理</h2>

      <!-- 导入区域 -->
      <div class="bg-[#132238] border border-white/10 rounded-2xl p-6 mb-8">
        <h3 class="font-semibold text-[#E8EDF5] mb-4 flex items-center gap-2">
          <Upload :size="18" class="text-[#D4A843]" />导入卡密 CSV
        </h3>
        <div class="flex items-center gap-4 flex-wrap">
          <label class="flex-1 min-w-[200px]">
            <span class="text-xs text-[#8B9CB5] mb-1 block">选择 CSV 文件（每行一个卡密）</span>
            <input type="file" accept=".csv,.txt" @change="onFileChange"
              class="w-full text-sm text-[#8B9CB5] file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-[#D4A843]/20 file:text-[#F0C060] file:text-sm file:font-medium hover:file:bg-[#D4A843]/30" />
          </label>
          <div>
            <span class="text-xs text-[#8B9CB5] mb-1 block">点券面值</span>
            <select v-model="importValue"
              class="bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white text-sm">
              <option :value="1">1 点券</option>
              <option :value="20">20 点券</option>
            </select>
          </div>
          <button @click="doImport" :disabled="!importFile || importing"
            class="self-end px-6 py-2.5 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 text-sm">
            <Loader2 v-if="importing" :size="14" class="inline animate-spin mr-1" />
            {{ importing ? "导入中..." : "开始导入" }}
          </button>
        </div>
        <div v-if="importMsg" :class="['mt-4 text-sm px-3 py-2 rounded-lg', importOk ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400']">
          {{ importMsg }}
        </div>
      </div>

      <!-- 搜索和过滤 -->
      <div class="flex items-center gap-3 mb-6 flex-wrap">
        <div class="flex-1 min-w-[200px] flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-2">
          <Search :size="16" class="text-[#5C6E8A]" />
          <input v-model="search" @keyup.enter="onSearch" placeholder="搜索卡密..."
            class="flex-1 bg-transparent outline-none text-white text-sm" />
        </div>
        <div class="flex gap-2">
          <button v-for="f in [{k:'all',l:'全部'},{k:'unused',l:'未用'},{k:'used',l:'已用'}]" :key="f.k"
            @click="onFilter(f.k)"
            :class="['px-4 py-2 rounded-lg text-sm transition-colors', usedFilter === f.k ? 'bg-[#D4A843]/20 text-[#F0C060] border border-[#D4A843]/30' : 'bg-white/5 text-[#8B9CB5] border border-white/10']">
            {{ f.l }}
          </button>
        </div>
      </div>

      <!-- 表格 -->
      <div class="bg-[#132238] border border-white/10 rounded-2xl overflow-hidden">
        <Loader2 v-if="loading" :size="24" class="mx-auto my-12 text-[#8B9CB5] animate-spin" />
        <template v-else>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-white/10 text-left">
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium w-[180px]">卡密</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">面值</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">状态</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">使用者</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">核销时间</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/5">
                <tr v-for="c in codes" :key="c.id" class="hover:bg-white/[0.02]">
                  <td class="px-4 py-3 font-mono text-[#E8EDF5]">{{ maskCode(c.code) }}</td>
                  <td class="px-4 py-3">
                    <span :class="c.ticket_value === 20 ? 'text-[#F0C060] font-semibold' : 'text-[#8B9CB5]'">{{ c.ticket_value }} 点</span>
                  </td>
                  <td class="px-4 py-3">
                    <span v-if="c.is_used" class="text-xs px-2 py-0.5 bg-red-500/10 text-red-400 rounded-full">已用</span>
                    <span v-else class="text-xs px-2 py-0.5 bg-green-500/10 text-green-400 rounded-full">未用</span>
                  </td>
                  <td class="px-4 py-3 text-[#8B9CB5]">{{ c.used_by || "-" }}</td>
                  <td class="px-4 py-3 text-[#5C6E8A]">{{ c.used_at ? new Date(c.used_at).toLocaleString("zh-CN") : "-" }}</td>
                </tr>
                <tr v-if="codes.length === 0">
                  <td colspan="5" class="px-4 py-12 text-center text-[#5C6E8A]">暂无数据</td>
                </tr>
              </tbody>
            </table>
          </div>
          <!-- 分页 -->
          <div class="flex items-center justify-between px-4 py-3 border-t border-white/10 text-sm text-[#8B9CB5]">
            <span>共 {{ total }} 条</span>
            <div class="flex items-center gap-2">
              <button @click="prevPage" :disabled="page <= 1" class="p-1 hover:text-[#E8EDF5] disabled:opacity-30"><ChevronLeft :size="16" /></button>
              <span>{{ page }} / {{ totalPages }}</span>
              <button @click="nextPage" :disabled="page >= totalPages" class="p-1 hover:text-[#E8EDF5] disabled:opacity-30"><ChevronRight :size="16" /></button>
            </div>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>
