<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  computed: {
    layout() {
      return this.$route.meta.layout || "base-layout";
    },
  },
  
  async mounted() {
    // Initialize theme system
    await this.initializeTheme();
    
    // Apply initial theme
    const currentTheme = this.$store.getters.currentActiveTheme;
    document.documentElement.setAttribute('data-theme', currentTheme);
    document.body.classList.add(`body--${currentTheme}`);
    
    // Add theme transition class after initial load
    setTimeout(() => {
      document.body.classList.add('theme-transitions-enabled');
    }, 100);
  },
  
  methods: {
    ...mapActions(['initializeTheme']),
  },
};
</script>

<style lang="scss">
// Import Google Fonts
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');

// Global application styles
html,
body,
#app {
  height: 100%;
  margin: 0;
  padding: 0;
}

// Theme transition control
.theme-transitions-enabled * {
  transition: background-color 200ms ease-in-out, 
              color 200ms ease-in-out,
              border-color 200ms ease-in-out,
              box-shadow 200ms ease-in-out;
}

// Override default Quasar styles with our theme
.q-header {
  background: var(--background-primary) !important;
  color: var(--text-primary) !important;
}

// CTF-specific utility classes
.text-cbs {
  color: var(--primary-contrast) !important;
}

.bg-cbs {
  background: var(--primary) !important;
}

// Flag status indicators
.flag-submitted {
  color: var(--flag-submitted) !important;
}

.flag-accepted {
  color: var(--flag) !important;
}

.flag-rejected {
  color: var(--flag-rejected) !important;
}

.flag-pending {
  color: var(--flag-pending) !important;
}

// Team status indicators
.team-friendly {
  color: var(--team-friendly) !important;
}

.team-enemy {
  color: var(--team-enemy) !important;
}

.team-neutral {
  color: var(--team-neutral) !important;
}

// Copy button enhancement
.copy-btn {
  opacity: 0.7;
  transition: opacity 150ms ease-out;
  
  &:hover {
    opacity: 1;
  }
}

// Loading states
.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// Responsive visibility utilities
@media (max-width: 599px) {
  .hide-on-mobile {
    display: none !important;
  }
}

@media (min-width: 600px) and (max-width: 1023px) {
  .hide-on-tablet {
    display: none !important;
  }
}

@media (min-width: 1024px) {
  .hide-on-desktop {
    display: none !important;
  }
}

// Accessibility improvements
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  .theme-transitions-enabled * {
    transition: none !important;
  }
}

// High contrast mode support
@media (prefers-contrast: high) {
  :root {
    --border-light: #000000;
    --border-dark: #ffffff;
  }
}
</style>
