import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: () => import("../views/Home.vue"),
    },
    {
      path: "/login",
      name: "Login",
      component: () => import("../views/Login.vue"),
      meta: { guest: true },
    },
    {
      path: "/analysis",
      name: "Analysis",
      component: () => import("../views/Analysis.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/analysis/:taskId",
      name: "AnalysisResult",
      component: () => import("../views/Analysis.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/history",
      name: "History",
      component: () => import("../views/History.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
});

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("auth_token");
  const isLoggedIn = !!token;

  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: "Login", query: { redirect: to.fullPath } });
  } else if (to.meta.guest && isLoggedIn) {
    next({ name: "Home" });
  } else {
    next();
  }
});

export default router;
