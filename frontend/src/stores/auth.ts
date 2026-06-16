import { defineStore } from "pinia";
import { ref, computed } from "vue";
import * as authApi from "../api/auth";
import client from "../api/client";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("auth_token"));
  const user = ref<authApi.UserInfo | null>(null);
  const loading = ref(false);

  const isLoggedIn = computed(() => !!token.value);

  // 设置 axios 请求头
  if (token.value) {
    client.defaults.headers.common["Authorization"] = `Bearer ${token.value}`;
  }

  async function doRegister(email: string, password: string) {
    loading.value = true;
    try {
      const res = await authApi.register({ email, password });
      return { ok: true, message: res.message };
    } catch (e: any) {
      return { ok: false, message: e.response?.data?.detail || "注册失败" };
    } finally {
      loading.value = false;
    }
  }

  async function doVerify(email: string, code: string) {
    loading.value = true;
    try {
      const res = await authApi.verifyEmail({ email, code });
      return { ok: true, message: res.message };
    } catch (e: any) {
      return { ok: false, message: e.response?.data?.detail || "验证失败" };
    } finally {
      loading.value = false;
    }
  }

  async function doLogin(email: string, password: string) {
    loading.value = true;
    try {
      const res = await authApi.login({ email, password });
      token.value = res.access_token;
      localStorage.setItem("auth_token", res.access_token);
      client.defaults.headers.common["Authorization"] = `Bearer ${res.access_token}`;
      await fetchUser();
      return { ok: true, message: "登录成功" };
    } catch (e: any) {
      return { ok: false, message: e.response?.data?.detail || "登录失败" };
    } finally {
      loading.value = false;
    }
  }

  async function fetchUser() {
    if (!token.value) return;
    try {
      user.value = await authApi.getMe();
    } catch {
      logout();
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem("auth_token");
    delete client.defaults.headers.common["Authorization"];
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    doRegister,
    doVerify,
    doLogin,
    fetchUser,
    logout,
  };
});
