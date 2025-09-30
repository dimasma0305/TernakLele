<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated :class="$q.dark.isActive ? 'bg-dark' : 'bg-primary'" class="modern-header">
      <q-toolbar class="q-px-lg">
        <div class="row items-center">
          <q-avatar class="q-mr-md" size="42px">
            <img src="@/assets/favicon.ico" />
          </q-avatar>
          <q-toolbar-title class="text-weight-bold text-h5" @click="goHome" @keydown.enter="goHome" tabindex="0" aria-label="Go to home page" style="cursor: pointer;">
            Ternak Lele
          </q-toolbar-title>
        </div>
        
        <q-space />
        
        <q-tabs shrink class="q-ml-md desktop-only">
          <q-route-tab :to="{ name: 'flags' }" label="Flags" icon="flag" />
          <q-route-tab :to="{ name: 'teams' }" label="Teams" icon="people" />
        </q-tabs>
        
        <q-space />
        
        <div class="row items-center">
          <q-btn flat round :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'" @click="toggleDarkMode" aria-label="Toggle dark mode">
            <q-tooltip>Toggle Dark Mode</q-tooltip>
          </q-btn>
        </div>
        
        <q-btn flat dense round icon="menu" class="mobile-only q-ml-sm" @click="toggleLeftDrawer" aria-label="Toggle navigation menu" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" bordered class="mobile-only" :class="$q.dark.isActive ? 'bg-dark' : 'bg-white'">
      <q-list>
        <q-item-label header>Navigation</q-item-label>
        <q-item clickable :to="{ name: 'flags' }">
          <q-item-section avatar>
            <q-icon name="flag" />
          </q-item-section>
          <q-item-section>Flags</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'teams' }">
          <q-item-section avatar>
            <q-icon name="people" />
          </q-item-section>
          <q-item-section>Teams</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <div class="container-fluid q-pa-md q-pa-lg-lg fade-in">
        <slot />
      </div>
    </q-page-container>
    
    <q-footer :class="$q.dark.isActive ? 'bg-dark text-white' : 'bg-white text-dark'" class="modern-footer">
      <q-toolbar class="q-px-lg">
        <div class="text-caption">Ternak Lele © {{ new Date().getFullYear() }}</div>
        <q-space />
        <div class="text-caption">@dimasc.tf</div>
      </q-toolbar>
    </q-footer>
  </q-layout>
</template>

<script>
export default {
  name: "BaseLayout",
  data() {
    return {
      leftDrawerOpen: false
    }
  },
  methods: {
    toggleDarkMode() {
      this.$q.dark.toggle();
      localStorage.setItem('darkMode', this.$q.dark.isActive);
    },
    toggleLeftDrawer() {
      this.leftDrawerOpen = !this.leftDrawerOpen;
    },
    goHome() {
      this.$router.push('/');
    }
  },
  mounted() {
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode !== null) {
      this.$q.dark.set(savedDarkMode === 'true');
    }
  }
};
</script>

<style lang="scss">
.modern-header {
  transition: background-color 0.3s ease;
  box-shadow: 0 var(--space-sm) var(--space-2xl) rgba(0, 0, 0, 0.08);
  
  .body--dark & {
    box-shadow: 0 var(--space-sm) var(--space-2xl) rgba(0, 0, 0, 0.2);
  }
  
  .q-toolbar {
    min-height: 70px;
    padding: 0 var(--space-lg);
  }
  
  .q-tab {
    transition: all 0.3s ease;
    border-radius: var(--radius-md);
    margin: 0 var(--space-xs);
    position: relative;
    overflow: hidden;
    
    &--active {
      font-weight: var(--font-weight-semibold);
      background: rgba(255, 255, 255, 0.15);
      
      &::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: currentColor;
        opacity: 0.8;
        transform: scaleX(1);
        transition: transform 0.3s ease;
      }
    }
    
    &:hover:not(.q-tab--active) {
      background: rgba(255, 255, 255, 0.1);
    }
    
    &:active {
      transform: translateY(1px);
    }
  }
}

.modern-footer {
  border-top: 1px solid;
  
  .body--light & {
    border-color: rgba(0, 0, 0, 0.05);
  }
  
  .body--dark & {
    border-color: rgba(255, 255, 255, 0.05);
  }
}

.container-fluid {
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 1023px) {
  .desktop-only {
    display: none;
  }
}

@media (min-width: 1024px) {
  .mobile-only {
    display: none;
  }
}
</style>
