<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { getUsers, type UserItem } from "../api/admin";
import { Shield, Users, Search, Loader2, ChevronLeft, ChevronRight } from "lucide-vue-next";

const router = useRouter();
const users = ref<UserItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 50;
const search = ref("");
const loading = ref(false);
const totalPages = computed(() => Math.ceil(total.value / pageSize));

onMounted(() => {
  if (!localStorage.getItem("admin_token")) { router.push("/admin/login"); return; }
  fetchUsers();
});

async function fetchUsers() {
  loading.value = true;
  try {
    const res = await getUsers({ page: page.value, page_size: pageSize, search: search.value });
    users.value = res.items;
    total.value = res.total;
  } catch(e: any) {
    if (e?.response?.status === 401) { localStorage.removeItem("admin_token"); router.push("/admin/login"); }
  } finally {
    loading.value = false;
  }
}

function onSearch() { page.value = 1; fetchUsers(); }
function prevPage() { if (page.value > 1) { page.value--; fetchUsers(); } }
function nextPage() { if (page.value < totalPages.value) { page.value++; fetchUsers(); } }
function go(p: string) { router.push(p); }
function doLogout() { localStorage.removeItem("admin_token"); router.push("/admin/login"); }
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
        <button @click="go('/admin/codes')" class="text-[#8B9CB5] hover:text-[#E8EDF5]">卡密管理</button>
        <button @click="go('/admin/users')" class="text-[#F0C060] font-medium">用户管理</button>
        <button @click="doLogout" class="text-red-400 hover:text-red-300 ml-4">退出</button>
      </nav>
    </header>

    <main class="max-w-6xl mx-auto px-6 py-10">
      <h2 class="text-2xl font-bold text-[#E8EDF5] mb-8">用户管理</h2>

      <div class="flex items-center gap-3 mb-6">
        <div class="flex-1 max-w-sm flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-2">
          <Search :size="16" class="text-[#5C6E8A]" />
          <input v-model="search" @keyup.enter="onSearch" placeholder="搜索邮箱..."
            class="flex-1 bg-transparent outline-none text-white text-sm" />
        </div>
      </div>

      <div class="bg-[#132238] border border-white/10 rounded-2xl overflow-hidden">
        <Loader2 v-if="loading" :size="24" class="mx-auto my-12 text-[#8B9CB5] animate-spin" />
        <template v-else>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-white/10 text-left">
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">邮箱</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">点券余额</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">已验证</th>
                  <th class="px-4 py-3 text-[#8B9CB5] font-medium">注册时间</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-white/5">
                <tr v-for="u in users" :key="u.id" class="hover:bg-white/[0.02]">
                  <td class="px-4 py-3 text-[#E8EDF5]">{{ u.email }}</td>
                  <td class="px-4 py-3">
                    <span :class="u.tickets > 0 ? 'text-[#F0C060] font-semibold' : 'text-[#5C6E8A]'">{{ u.tickets }} 点券</span>
                  </td>
                  <td class="px-4 py-3">
                    <span v-if="u.is_verified" class="text-xs px-2 py-0.5 bg-green-500/10 text-green-400 rounded-full">是</span>
                    <span v-else class="text-xs px-2 py-0.5 bg-yellow-500/10 text-yellow-400 rounded-full">否</span>
                  </td>
                  <td class="px-4 py-3 text-[#5C6E8A]">{{ new Date(u.created_at).toLocaleString("zh-CN") }}</td>
                </tr>
                <tr v-if="users.length === 0">
                  <td colspan="4" class="px-4 py-12 text-center text-[#5C6E8A]">暂无数据</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="flex items-center justify-between px-4 py-3 border-t border-white/10 text-sm text-[#8B9CB5]">
            <span>共 {{ total }} 人</span>
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
