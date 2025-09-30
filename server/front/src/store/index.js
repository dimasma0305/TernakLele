import { flagsPerPage } from "@/config";
import Flag from "@/models/flag.js";
import Team from "@/models/team.js";
import APIService from "@/services/api";
import { createStore } from "vuex";
import createPersistedState from "vuex-persistedstate";

export default createStore({
  plugins: [createPersistedState({ paths: ["serverPassword", "ui"] })],
  state: {
    totalFlags: 0,
    selectedPage: 1,

    flags: [],
    flagFilters: null,
    serverTZ: null,

    sploitFilterOptions: [],
    teamFilterOptions: [],
    statusFilterOptions: [],

    flagFormat: null,

    teams: [],

    serverPassword: null,

    // UI and Theme Management
    ui: {
      theme: 'auto', // 'light', 'dark', 'auto'
      systemTheme: 'light',
      userPreference: null,
      themeTransition: false,
    },
  },
  mutations: {
    setTotalFlags(state, totalFlags) {
      state.totalFlags = totalFlags;
    },
    setFlags(state, flags) {
      state.flags = flags;
    },
    setFlagFilters(state, flagFilters) {
      state.flagFilters = flagFilters;
    },
    setSelectedPage(state, page) {
      state.selectedPage = page;
    },
    setServerTZ(state, tz) {
      state.serverTZ = tz;
    },

    setFilterOptions(state, filterOptions) {
      state.sploitFilterOptions = filterOptions.sploit ?? [];
      state.teamFilterOptions = filterOptions.team ?? [];
      state.statusFilterOptions = filterOptions.status ?? [];
    },
    setFlagFormat(state, flagFormat) {
      state.flagFormat = flagFormat;
    },

    setTeams(state, teams) {
      state.teams = teams;
    },

    setServerPassword(state, password) {
      state.serverPassword = password;
    },

    // Theme Management Mutations
    setTheme(state, theme) {
      state.ui.theme = theme;
    },
    setSystemTheme(state, systemTheme) {
      state.ui.systemTheme = systemTheme;
    },
    setUserPreference(state, preference) {
      state.ui.userPreference = preference;
    },
    setThemeTransition(state, transitioning) {
      state.ui.themeTransition = transitioning;
    },
  },
  actions: {
    fetchFlags: async function (context) {
      const filters = context.state.flagFilters;
      let params = {
        page: context.state.selectedPage,
        page_size: flagsPerPage,
      };
      if (filters) {
        params = { ...params, ...filters };
      }
      try {
        const { data } = await APIService.get("/filter_flags", { params });

        const flags = data.flags.map((flag) => new Flag(flag));
        context.commit("setFlags", flags);
        context.commit("setTotalFlags", data.total);
      } catch (e) {
        console.error("Error fetching tasks", e);
      }

      await context.dispatch("fetchFilterOptions");
    },

    updatePage: async function (context, page) {
      context.commit("setSelectedPage", page);
      await context.dispatch("fetchFlags");
    },

    fetchFilterOptions: async function (context) {
      try {
        const { data } = await APIService.get("/filter_config");
        context.commit("setFilterOptions", data.filters);
        context.commit("setFlagFormat", data.flag_format);
        context.commit("setServerTZ", data.server_tz);
      } catch (e) {
        console.error("Error fetching filter options", e);
      }
    },

    fetchTeams: async function (context) {
      try {
        const { data } = await APIService.get("/teams");
        const teams = data.map((team) => new Team(team));
        context.commit("setTeams", teams);
      } catch (e) {
        console.error("Error fetching teams", e);
      }
    },

    // Theme Management Actions
    initializeTheme: function (context) {
      // Detect system preference
      const systemPreference = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      context.commit('setSystemTheme', systemPreference);
      
      // Set initial theme based on user preference or system
      const currentTheme = context.state.ui.userPreference || context.state.ui.theme;
      if (currentTheme === 'auto') {
        context.dispatch('applyTheme', systemPreference);
      } else {
        context.dispatch('applyTheme', currentTheme);
      }
      
      // Listen for system theme changes
      if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
          const newSystemTheme = e.matches ? 'dark' : 'light';
          context.commit('setSystemTheme', newSystemTheme);
          if (context.state.ui.theme === 'auto') {
            context.dispatch('applyTheme', newSystemTheme);
          }
        });
      }
    },

    toggleTheme: function (context) {
      const currentTheme = context.getters.currentActiveTheme;
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      context.commit('setUserPreference', newTheme);
      context.commit('setTheme', newTheme);
      context.dispatch('applyTheme', newTheme);
    },

    setThemeMode: function (context, mode) {
      context.commit('setTheme', mode);
      context.commit('setUserPreference', mode);
      
      if (mode === 'auto') {
        context.dispatch('applyTheme', context.state.ui.systemTheme);
      } else {
        context.dispatch('applyTheme', mode);
      }
    },

    applyTheme: function (context, theme) {
      context.commit('setThemeTransition', true);
      
      // Apply theme to document
      document.documentElement.setAttribute('data-theme', theme);
      document.body.classList.remove('body--light', 'body--dark');
      document.body.classList.add(`body--${theme}`);
      
      // Apply Quasar dark mode
      if (typeof window !== 'undefined' && window.Quasar) {
        window.Quasar.dark.set(theme === 'dark');
      }
      
      setTimeout(() => {
        context.commit('setThemeTransition', false);
      }, 200);
    },

    resetThemePreferences: function (context) {
      context.commit('setUserPreference', null);
      context.commit('setTheme', 'auto');
      context.dispatch('applyTheme', context.state.ui.systemTheme);
    },
  },
  getters: {
    currentActiveTheme: (state) => {
      if (state.ui.theme === 'auto') {
        return state.ui.systemTheme;
      }
      return state.ui.theme;
    },
    isDarkMode: (state, getters) => {
      return getters.currentActiveTheme === 'dark';
    },
    isLightMode: (state, getters) => {
      return getters.currentActiveTheme === 'light';
    },
  },
  modules: {},
});
