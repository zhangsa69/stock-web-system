import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器 — 自动附加 token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
    }
    const message = error.response?.data?.detail || error.message || "请求失败";
    console.error("API Error:", message);
    return Promise.reject(error);
  }
);

export default client;
