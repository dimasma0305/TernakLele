import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "flags",
    component: () => import("@/views/Flags.vue"),
    meta: { layout: 'base-layout' }
  },
  {
    path: "/teams",
    name: "teams",
    component: () => import("@/views/Teams.vue"),
    meta: { layout: 'base-layout' }
  },

  {
    path: "/login",
    name: "login",
    component: () => import("@/views/Login.vue"),
    meta: { layout: 'base-layout' }
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
