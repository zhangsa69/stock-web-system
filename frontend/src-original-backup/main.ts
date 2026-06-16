import { createApp } from "vue";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";
import { createPinia } from "pinia";
import router from "./router";
import App from "./App.vue";
import "./styles/index.css";

const app = createApp(App);

// Element Plus
app.use(ElementPlus, { locale: zhCn });

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// Pinia 状态管理
app.use(createPinia());

// Vue Router
app.use(router);

app.mount("#app");
