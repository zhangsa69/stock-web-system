<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { Mail } from "lucide-vue-next";

const router = useRouter();
const auth = useAuthStore();

type Step = "register" | "verify" | "login";
const step = ref<Step>("register");
const email = ref("");
const password = ref("");
const code = ref("");
const errorMsg = ref("");
const successMsg = ref("");
const btnLoading = ref(false);

async function handleRegister() {
  errorMsg.value = "";
  successMsg.value = "";
  if (!email.value || !password.value) {
    errorMsg.value = "请填写邮箱和密码";
    return;
  }
  if (password.value.length < 6) {
    errorMsg.value = "密码至少 6 位";
    return;
  }
  btnLoading.value = true;
  const result = await auth.doRegister(email.value, password.value);
  btnLoading.value = false;
  if (result.ok) {
    successMsg.value = result.message;
    step.value = "verify";
  } else {
    errorMsg.value = result.message;
  }
}

async function handleVerify() {
  errorMsg.value = "";
  successMsg.value = "";
  if (!code.value || code.value.length !== 6) {
    errorMsg.value = "请输入 6 位验证码";
    return;
  }
  btnLoading.value = true;
  const result = await auth.doVerify(email.value, code.value);
  btnLoading.value = false;
  if (result.ok) {
    successMsg.value = "验证成功！请登录";
    step.value = "login";
  } else {
    errorMsg.value = result.message;
  }
}

async function handleLogin() {
  errorMsg.value = "";
  successMsg.value = "";
  if (!email.value || !password.value) {
    errorMsg.value = "请填写邮箱和密码";
    return;
  }
  btnLoading.value = true;
  const result = await auth.doLogin(email.value, password.value);
  btnLoading.value = false;
  if (result.ok) {
    router.push("/");
  } else {
    errorMsg.value = result.message;
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#0A1628] px-6">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center gap-2.5">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#D4A843] to-[#F0C060] flex items-center justify-center">
            <Mail :size="22" class="text-[#0D1B2A]" />
          </div>
          <span class="text-2xl font-bold text-[#E8EDF5]">AI 财报分析</span>
        </div>
      </div>

      <!-- Card -->
      <div class="bg-[#132238]/60 backdrop-blur border border-white/10 rounded-2xl p-8">
        <!-- Register -->
        <template v-if="step === 'register'">
          <h2 class="text-xl font-bold text-[#E8EDF5] mb-6">注册账号</h2>
          <div class="space-y-4">
            <input
              v-model="email"
              type="email"
              placeholder="输入邮箱地址"
              class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] focus:border-[#D4A843] outline-none transition-colors"
            />
            <input
              v-model="password"
              type="password"
              placeholder="设置密码（至少6位）"
              class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] focus:border-[#D4A843] outline-none transition-colors"
            />
            <p class="text-xs text-[#5C6E8A]">注册后系统将发送 6 位验证码到您的邮箱</p>
          </div>
          <div v-if="errorMsg" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
            {{ errorMsg }}
          </div>
          <div v-if="successMsg" class="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-sm text-green-400">
            {{ successMsg }}
          </div>
          <button
            @click="handleRegister"
            :disabled="btnLoading"
            class="mt-6 w-full py-3 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            {{ btnLoading ? "发送中..." : "注册" }}
          </button>
          <p class="mt-4 text-center text-sm text-[#5C6E8A]">
            已有账号？<button @click="step = 'login'" class="text-[#F0C060] hover:underline ml-1">去登录</button>
          </p>
        </template>

        <!-- Verify -->
        <template v-if="step === 'verify'">
          <h2 class="text-xl font-bold text-[#E8EDF5] mb-2">验证邮箱</h2>
          <p class="text-sm text-[#5C6E8A] mb-6">验证码已发送至 <span class="text-[#F0C060]">{{ email }}</span></p>
          <input
            v-model="code"
            type="text"
            maxlength="6"
            placeholder="输入 6 位验证码"
            class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-center text-2xl tracking-[8px] placeholder:text-[#5C6E8A] focus:border-[#D4A843] outline-none transition-colors"
            @keyup.enter="handleVerify"
          />
          <div v-if="errorMsg" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
            {{ errorMsg }}
          </div>
          <div v-if="successMsg" class="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-sm text-green-400">
            {{ successMsg }}
          </div>
          <button
            @click="handleVerify"
            :disabled="btnLoading"
            class="mt-6 w-full py-3 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            {{ btnLoading ? "验证中..." : "验证" }}
          </button>
          <p class="mt-4 text-center text-sm text-[#5C6E8A]">
            <button @click="step = 'register'" class="text-[#F0C060] hover:underline">返回注册</button>
          </p>
        </template>

        <!-- Login -->
        <template v-if="step === 'login'">
          <h2 class="text-xl font-bold text-[#E8EDF5] mb-6">登录</h2>
          <div class="space-y-4">
            <input
              v-model="email"
              type="email"
              placeholder="输入邮箱地址"
              class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] focus:border-[#D4A843] outline-none transition-colors"
            />
            <input
              v-model="password"
              type="password"
              placeholder="输入密码"
              class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-[#5C6E8A] focus:border-[#D4A843] outline-none transition-colors"
              @keyup.enter="handleLogin"
            />
          </div>
          <div v-if="errorMsg" class="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
            {{ errorMsg }}
          </div>
          <button
            @click="handleLogin"
            :disabled="btnLoading"
            class="mt-6 w-full py-3 bg-gradient-to-r from-[#D4A843] to-[#F0C060] text-[#0A1929] font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            {{ btnLoading ? "登录中..." : "登录" }}
          </button>
          <p class="mt-4 text-center text-sm text-[#5C6E8A]">
            还没有账号？<button @click="step = 'register'" class="text-[#F0C060] hover:underline ml-1">去注册</button>
          </p>
        </template>
      </div>
    </div>
  </div>
</template>
