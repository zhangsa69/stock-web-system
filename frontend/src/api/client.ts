import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 全局错误回调
let globalErrorHandler: ((msg: string) => void) | null = null;
export function setGlobalErrorHandler(fn: (msg: string) => void) {
  globalErrorHandler = fn;
}

// 请求拦截器 — 自动附加 token 或 admin_token
client.interceptors.request.use((config) => {
  const adminToken = localStorage.getItem("admin_token");
  if (adminToken && config.url?.startsWith("/admin")) {
    config.headers.Authorization = `Bearer ${adminToken}`;
  } else {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// 响应拦截器
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const detail = error.response?.data?.detail;

    if (status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("admin_token");
    }

    // 网络错误（无响应）
    if (!error.response) {
      const msg = "网络连接失败，请检查网络";
      console.error("API Error:", msg);
      if (globalErrorHandler) globalErrorHandler(msg);
      return Promise.reject(error);
    }

    // 服务端错误
    if (status >= 500) {
      const msg = "服务器繁忙，请稍后重试";
      console.error("API 5xx:", detail || msg);
      if (globalErrorHandler) globalErrorHandler(msg);
    }

    const message = detail || error.message || "请求失败";
    console.error("API Error:", message);
    return Promise.reject(error);
  }
);

export default client;
