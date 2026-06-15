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
      path: "/analysis",
      name: "Analysis",
      component: () => import("../views/Analysis.vue"),
    },
    {
      path: "/analysis/:taskId",
      name: "AnalysisResult",
      component: () => import("../views/Analysis.vue"),
    },
    {
      path: "/history",
      name: "History",
      component: () => import("../views/History.vue"),
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/",
    },
  ],
});

export default router;
