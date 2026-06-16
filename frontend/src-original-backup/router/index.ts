import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "Home",
      component: () => import("../views/Home.vue"),
      meta: { requiresAuth: true },
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
    // ── Admin Routes ──
    {
      path: "/admin/login",
      name: "AdminLogin",
      component: () => import("../views/AdminLogin.vue"),
    },
    {
      path: "/admin/dashboard",
      name: "AdminDashboard",
      component: () => import("../views/AdminDashboard.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/codes",
      name: "AdminCodes",
      component: () => import("../views/AdminCodes.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin/users",
      name: "AdminUsers",
      component: () => import("../views/AdminUsers.vue"),
      meta: { requiresAdmin: true },
    },
    {
      path: "/admin",
      redirect: "/admin/dashboard",
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
  const adminToken = localStorage.getItem("admin_token");
  const isLoggedIn = !!token;

  // Admin 路由独立鉴权
  if (to.meta.requiresAdmin) {
    if (!adminToken) {
      next({ name: "AdminLogin" });
    } else {
      next();
    }
    return;
  }

  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: "Login", query: { redirect: to.fullPath } });
  } else if (to.meta.guest && isLoggedIn) {
    next({ name: "Home" });
  } else {
    next();
  }
});

export default router;
