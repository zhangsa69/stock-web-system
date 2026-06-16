<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { Mail, ArrowRight, Check, Sparkles } from "lucide-vue-next";

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
  errorMsg.value = ""; successMsg.value = "";
  if (!email.value || !password.value) { errorMsg.value = "请填写邮箱和密码"; return; }
  if (password.value.length < 6) { errorMsg.value = "密码至少6位"; return; }
  btnLoading.value = true;
  const result = await auth.doRegister(email.value, password.value);
  btnLoading.value = false;
  if (result.ok) { successMsg.value = result.message; step.value = "verify"; }
  else { errorMsg.value = result.message; }
}

async function handleVerify() {
  errorMsg.value = ""; successMsg.value = "";
  if (!code.value || code.value.length !== 6) { errorMsg.value = "请输入6位验证码"; return; }
  btnLoading.value = true;
  const result = await auth.doVerify(email.value, code.value);
  btnLoading.value = false;
  if (result.ok) { successMsg.value = "验证成功！请登录"; step.value = "login"; }
  else { errorMsg.value = result.message; }
}

async function handleLogin() {
  errorMsg.value = ""; successMsg.value = "";
  if (!email.value || !password.value) { errorMsg.value = "请填写邮箱和密码"; return; }
  btnLoading.value = true;
  const result = await auth.doLogin(email.value, password.value);
  btnLoading.value = false;
  if (result.ok) { router.push("/"); }
  else { errorMsg.value = result.message; }
}
</script>

<template>
  <div class="login-page">
    <!-- Animated background -->
    <div class="login-bg">
      <div class="login-blob login-blob-1" />
      <div class="login-blob login-blob-2" />
    </div>

    <div class="login-card animate-scale-in">
      <!-- Logo -->
      <div class="login-logo">
        <svg width="36" height="36" viewBox="0 0 28 28" fill="none">
          <defs>
            <linearGradient id="login-grad" x1="0" y1="0" x2="28" y2="28">
              <stop offset="0%" stop-color="#0052ff"/><stop offset="100%" stop-color="#3b82f6"/>
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="24" height="24" rx="6" stroke="url(#login-grad)" stroke-width="2.5"/>
          <rect x="7" y="7" width="5" height="13" rx="1.5" fill="url(#login-grad)"/>
          <rect x="14" y="10" width="5" height="10" rx="1.5" fill="url(#login-grad)" opacity="0.6"/>
        </svg>
        <span>AI 财报分析</span>
      </div>

      <!-- Register -->
      <template v-if="step === 'register'">
        <h2>创建账号</h2>
        <div class="input-group">
          <input v-model="email" type="email" placeholder="邮箱地址" autocomplete="email" />
          <input v-model="password" type="password" placeholder="设置密码（至少6位）" autocomplete="new-password" />
        </div>
        <p class="hint">注册后系统将发送 6 位验证码到您的邮箱</p>
        <div v-if="errorMsg" class="msg msg-err">{{ errorMsg }}</div>
        <div v-if="successMsg" class="msg msg-ok"><Check :size="14" />{{ successMsg }}</div>
        <button @click="handleRegister" :disabled="btnLoading" class="btn-full">
          {{ btnLoading ? "发送中..." : "注册" }}
          <ArrowRight v-if="!btnLoading" :size="16" />
        </button>
        <p class="switch-text">已有账号？<button @click="step='login'">登录</button></p>
      </template>

      <!-- Verify -->
      <template v-if="step === 'verify'">
        <h2>验证邮箱</h2>
        <p class="verify-email">验证码已发送至 <span>{{ email }}</span></p>
        <input
          v-model="code" type="text" maxlength="6"
          placeholder="输入6位验证码"
          class="code-input"
          @keyup.enter="handleVerify"
        />
        <div v-if="errorMsg" class="msg msg-err">{{ errorMsg }}</div>
        <div v-if="successMsg" class="msg msg-ok"><Check :size="14" />{{ successMsg }}</div>
        <button @click="handleVerify" :disabled="btnLoading" class="btn-full">
          {{ btnLoading ? "验证中..." : "验证" }}
        </button>
        <p class="switch-text"><button @click="step='register'">返回注册</button></p>
      </template>

      <!-- Login -->
      <template v-if="step === 'login'">
        <h2>登录</h2>
        <div class="input-group">
          <input v-model="email" type="email" placeholder="邮箱地址" autocomplete="email" />
          <input v-model="password" type="password" placeholder="密码" @keyup.enter="handleLogin" autocomplete="current-password" />
        </div>
        <div v-if="errorMsg" class="msg msg-err">{{ errorMsg }}</div>
        <button @click="handleLogin" :disabled="btnLoading" class="btn-full">
          {{ btnLoading ? "登录中..." : "登录" }}
          <ArrowRight v-if="!btnLoading" :size="16" />
        </button>
        <p class="switch-text">还没有账号？<button @click="step='register'">注册</button></p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  position: relative; padding: 24px;
}
.login-bg { position: fixed; inset: 0; z-index: 0; overflow: hidden; }
.login-blob {
  position: absolute; border-radius: 50%; filter: blur(120px); opacity: 0.08;
}
.login-blob-1 {
  width: 500px; height: 500px; background: #0052ff;
  top: -10%; left: -10%;
  animation: blob-login 10s ease-in-out infinite alternate;
}
.login-blob-2 {
  width: 400px; height: 400px; background: #7c3aed;
  bottom: -10%; right: -10%;
  animation: blob-login 14s ease-in-out infinite alternate-reverse;
}
@keyframes blob-login {
  0% { transform: translate(0,0) scale(1); }
  50% { transform: translate(40px,-30px) scale(1.1); }
  100% { transform: translate(-20px,20px) scale(0.95); }
}

.login-card {
  position: relative; z-index: 10;
  width: 100%; max-width: 420px;
  background: var(--cb-surface-dark-elevated, #16181c);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 24px; padding: 40px 32px;
}
.login-logo {
  display: flex; align-items: center; justify-content: center; gap: 10px;
  margin-bottom: 36px;
}
.login-logo span {
  font-family: 'Inter', sans-serif;
  font-size: 22px; font-weight: 700;
  color: #0052ff; letter-spacing: -0.02em;
}
.login-card h2 {
  font-family: 'Inter', sans-serif;
  font-size: 24px; font-weight: 600;
  color: #ffffff; margin: 0 0 24px;
  text-align: center;
}
.input-group { display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px; }
.input-group input,
.code-input {
  width: 100%; box-sizing: border-box;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 14px 16px;
  color: #fff; font-size: 16px;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input-group input:focus,
.code-input:focus {
  border-color: #0052ff;
  box-shadow: 0 0 0 3px rgba(0,82,255,0.12);
}
.input-group input::placeholder,
.code-input::placeholder { color: rgba(255,255,255,0.25); }
.code-input {
  text-align: center; font-size: 28px; letter-spacing: 8px;
  font-family: var(--cb-font-mono, 'JetBrains Mono');
  font-weight: 500;
}
.hint { font-size: 13px; color: rgba(255,255,255,0.3); text-align: center; margin: 0 0 16px; }
.verify-email { font-size: 14px; color: rgba(255,255,255,0.35); text-align: center; margin: 0 0 20px; }
.verify-email span { color: #0052ff; font-weight: 500; }
.msg { padding: 12px 16px; border-radius: 12px; font-size: 14px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }
.msg-err { background: rgba(207,32,47,0.08); border: 1px solid rgba(207,32,47,0.15); color: #cf202f; }
.msg-ok { background: rgba(5,177,105,0.08); border: 1px solid rgba(5,177,105,0.15); color: #05b169; }
.btn-full {
  width: 100%;
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 14px 24px; border-radius: 9999px; border: none;
  background: #0052ff; color: #fff;
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-full:hover { background: #0045d9; box-shadow: 0 4px 20px rgba(0,82,255,0.3); }
.btn-full:active { transform: scale(0.98); }
.btn-full:disabled { background: rgba(0,82,255,0.3); cursor: not-allowed; box-shadow: none; }
.switch-text {
  text-align: center; font-size: 14px; color: rgba(255,255,255,0.3);
  margin: 24px 0 0;
}
.switch-text button {
  background: none; border: none;
  color: #0052ff; font-weight: 500; cursor: pointer;
  font-size: 14px;
}
.switch-text button:hover { text-decoration: underline; }

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.animate-scale-in { animation: scaleIn 0.5s cubic-bezier(0.34,1.56,0.64,1) both; }
</style>
