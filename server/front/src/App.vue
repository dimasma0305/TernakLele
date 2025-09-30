<template>
  <component :is="layout">
    <router-view v-slot="{ Component }">
      <transition name="page-transition" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </component>
</template>

<script>
export default {
  name: "App",
  computed: {
    layout() {
      return this.$route.meta.layout || "div";
    }
  }
};
</script>

<style lang="scss">
html,
body,
#app {
  height: 100%;
  margin: 0;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: "Inter", "Roboto", -apple-system, BlinkMacSystemFont, sans-serif !important;
  line-height: 1.6;
  letter-spacing: 0.015em;
  font-size: 16px;
  color: var(--q-text-light);
  
  .body--dark & {
    color: var(--q-text-dark);
  }
}

// Modern typography system
h1, h2, h3, h4, h5, h6, .text-h1, .text-h2, .text-h3, .text-h4, .text-h5, .text-h6 {
  font-weight: 600;
  line-height: 1.2;
  margin-top: 0;
  margin-bottom: 0.5em;
  letter-spacing: -0.01em;
}

.text-h1, h1 { font-size: 2.5rem; }
.text-h2, h2 { font-size: 2rem; }
.text-h3, h3 { font-size: 1.75rem; }
.text-h4, h4 { font-size: 1.5rem; }
.text-h5, h5 { font-size: 1.25rem; }
.text-h6, h6 { font-size: 1rem; }

.text-subtitle1 { 
  font-size: 1.1rem;
  font-weight: 500;
}

.text-subtitle2 {
  font-size: 0.9rem;
  font-weight: 500;
}

.text-body1 {
  font-size: 1rem;
  line-height: 1.6;
}

.text-body2 {
  font-size: 0.875rem;
  line-height: 1.6;
}

.text-caption {
  font-size: 0.75rem;
  letter-spacing: 0.03em;
  opacity: 0.8;
}

// Modern transitions
.page-transition-enter-active,
.page-transition-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-transition-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-transition-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

// Global styles
.text-cbs {
  color: var(--q-primary);
}

.bg-cbs {
  background-color: var(--q-primary);
}

// Dark mode styles
.body--dark {
  .q-card {
    background-color: var(--q-dark-page);
  }
  
  .q-table__container {
    background-color: var(--q-dark);
  }
  
  .q-table__card {
    color: white;
    background-color: var(--q-dark);
  }
  
  .q-table thead, .q-table tr, .q-table th, .q-table td {
    border-color: rgba(255, 255, 255, 0.08);
  }
  
  .q-table tbody td {
    color: white;
  }
  
  .q-table__bottom {
    color: white;
  }
  
  .q-btn {
    &:hover:not(.q-btn--flat):not(.q-btn--outline) {
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.4);
    }
  }
}

// Light mode enhancements
.body--light {
  .q-card {
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1);
  }
  
  .q-btn {
    &:hover:not(.q-btn--flat):not(.q-btn--outline) {
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
    }
  }
}

// Custom scrollbar
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.body--dark ::-webkit-scrollbar-thumb {
  background: #555;
}

// Global component styling
.q-card {
  border-radius: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  .body--dark & {
    /* Dark mode styling handled elsewhere */
  }
}

.q-btn {
  letter-spacing: 0.025em;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
  
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 120%;
    height: 120%;
    background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 70%);
    opacity: 0;
    transform: translate(-50%, -50%) scale(0.8);
    transition: opacity 0.5s, transform 0.5s;
  }
  
  &:active::after {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1);
    transition: opacity 0s, transform 0s;
  }
  
  &--round {
    border-radius: 50%;
  }
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
  }
  
  &:active:not(:disabled) {
    transform: translateY(1px);
  }
}

.q-table {
  border-radius: 16px;
  overflow: hidden;
  
  &__container {
    box-shadow: none;
  }
}

.q-field {
  &__control {
    border-radius: 8px;
    transition: all 0.3s ease;
    
    &--focused {
      box-shadow: 0 0 0 3px var(--q-focus-ring);
    }
  }
}
</style>
