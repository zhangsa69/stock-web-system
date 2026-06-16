<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { adminSendCode, adminLogin } from "../api/admin";
import { Shield, Loader2, ArrowRight } from "lucide-vue-next";

const router = useRouter();
const email = ref("17832274061@163.com");
const code = ref("");
const step = ref<"send" | "verify">("send");
const loading = ref(false);
const msg = ref("");
const err = ref(false);
const countdown = ref(0);

async function doSend() {
  loading.value = true;
  msg.value = "";
  try {
    await adminSendCode(email.value);
    step.value = "verify";
    msg.value = "验证码已发送";
    err.value = false;
    countdown.value = 60;
    const timer = setInterval(() => {
      countdown.value--;
      if (countdown.value <= 0) clearInterval(timer);
    }, 1000);
  } catch (e: any) {
    msg.value = e.response?.data?.detail || "发送失败";
    err.value = true;
  } finally {
    loading.value = false;
  }
}

async function doLogin() {
  if (!code.value.trim()) return;
  loading.value = true;
  msg.value = "";
  try {
    const res = await adminLogin(email.value, code.value);
    localStorage.setItem("admin_token", res.access_token);
    router.push("/admin/dashboard");
  } catch (e: any) {
    msg.value = e.response?.data?.detail || "登录失败";
    err.value = true;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen bg-[#0A1929] flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <div class="w-14 h-14 mx-auto mb-4 rounded-xl bg-gradient-to-br from-[#D4A843] to-[#F0C060] flex items-center justify-center">
          <Shield :size="28" class="text-[#0A1929]" />
        </div>
        <h1 class="text-xl font-bold text-[#E8EDF5]">管理后台</h1>
        <p class="text-sm text-[#8B9CB5] mt-1">仅限管理员登录</p>
      </div>

      <div v-if="step === 'send'">
        <label class="text-sm text-[#8B9CB5] mb-2 block">管理员邮箱</label>
        <input
          v-model="email"
          type="email"
          class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-sm focus:border-[#D4A843] outline-none mb-4"
          @keyup.enter="doSend"
        />
        <button
          @click="doSend"
          :disabled="loading"
          class="w-full py-3 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Loader2 v-if="loading" :size="16" class="animate-spin" />
          {{ loading ? "发送中..." : "发送验证码" }}
        </button>
      </div>

      <div v-else>
        <p class="text-sm text-[#8B9CB5] mb-4 text-center">验证码已发送至 {{ email }}</p>
        <input
          v-model="code"
          type="text"
          maxlength="6"
          placeholder="输入6位验证码"
          class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white text-center text-2xl tracking-[0.5em] focus:border-[#D4A843] outline-none mb-4"
          @keyup.enter="doLogin"
        />
        <button
          @click="doLogin"
          :disabled="!code.trim() || loading"
          class="w-full py-3 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <Loader2 v-if="loading" :size="16" class="animate-spin" />
          {{ loading ? "验证中..." : "登录" }}
        </button>
        <button
          @click="step = 'send'"
          class="w-full mt-3 py-2 text-sm text-[#8B9CB5] hover:text-[#E8EDF5]"
        >
          重新发送 {{ countdown > 0 ? `(${countdown}s)` : "" }}
        </button>
      </div>

      <div
        v-if="msg"
        :class="['mt-4 text-sm text-center px-3 py-2 rounded-lg', err ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400']"
      >
        {{ msg }}
      </div>
    </div>
  </div>
</template>
