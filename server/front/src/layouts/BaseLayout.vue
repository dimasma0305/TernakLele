<template>
  <q-layout view="hHh lpR fFf" class="modern-layout">
    <q-header elevated class="modern-header">
      <q-toolbar class="modern-toolbar">
        <!-- Brand Section -->
        <div class="brand-section">
          <q-avatar size="40px" class="brand-avatar">
            <img src="@/assets/favicon.ico" alt="Ternak Lele Logo" />
          </q-avatar>
          <div class="brand-text">
            <div class="brand-title">Ternak Lele</div>
            <div class="brand-subtitle">CTF Platform</div>
          </div>
        </div>

        <!-- Navigation Section -->
        <div class="nav-section">
          <q-tabs 
            class="modern-tabs" 
            indicator-color="primary"
            active-color="primary"
            align="center"
          >
            <q-route-tab 
              :to="{ name: 'flags' }" 
              label="Flags" 
              icon="flag"
              class="modern-tab"
            />
            <q-route-tab 
              :to="{ name: 'teams' }" 
              label="Teams" 
              icon="groups"
              class="modern-tab"
            />
          </q-tabs>
        </div>

        <!-- Utility Section -->
        <div class="utility-section">
          <!-- Connection Status Indicator -->
          <div class="connection-status" :class="{ 'connected': isConnected }">
            <q-icon 
              :name="isConnected ? 'wifi' : 'wifi_off'" 
              :color="isConnected ? 'positive' : 'negative'"
              size="sm"
            />
            <span class="status-text hide-on-mobile">
              {{ isConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>

          <!-- Theme Toggle -->
          <theme-toggle :compact="$q.screen.lt.md" />

          <!-- Settings Menu (Future expansion) -->
          <q-btn 
            flat 
            round 
            icon="more_vert" 
            class="settings-btn"
            v-if="false"
          >
            <q-menu>
              <q-list>
                <q-item clickable>
                  <q-item-section>
                    <q-item-label>Settings</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </div>
      </q-toolbar>
    </q-header>

    <q-page-container class="modern-page-container">
      <div class="page-content">
        <slot />
      </div>
    </q-page-container>
  </q-layout>
</template>

<script>
import ThemeToggle from '@/components/ThemeToggle.vue';

export default {
  name: 'BaseLayout',
  
  components: {
    ThemeToggle,
  },
  
  data() {
    return {
      isConnected: true, // This could be connected to actual connection status
    };
  },
  
  mounted() {
    // Simulate connection monitoring
    this.monitorConnection();
  },
  
  methods: {
    monitorConnection() {
      // This is a placeholder for actual connection monitoring
      // In a real app, this might check API connectivity
      if (typeof navigator !== 'undefined' && 'onLine' in navigator) {
        this.isConnected = navigator.onLine;
        
        window.addEventListener('online', () => {
          this.isConnected = true;
        });
        
        window.addEventListener('offline', () => {
          this.isConnected = false;
        });
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.modern-layout {
  font-family: 'JetBrains Mono', monospace;
}

.modern-header {
  background: var(--surface) !important;
  color: var(--text-primary) !important;
  border-bottom: 1px solid var(--border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  
  :root[data-theme='dark'] & {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  }
}

.modern-toolbar {
  padding: 0 $spacing-lg;
  min-height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-lg;
  
  @include mobile-and-tablet {
    padding: 0 $spacing-md;
    gap: $spacing-md;
    min-height: 56px;
  }
  
  @include mobile {
    padding: 0 $spacing-sm;
    gap: $spacing-sm;
    flex-wrap: wrap;
  }
}

// Brand Section
.brand-section {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-shrink: 0;
  min-width: 0; // Allows text truncation
  
  .brand-avatar {
    background: var(--primary);
    border: 2px solid var(--border);
    transition: all $transition-normal ease-out;
    flex-shrink: 0;
    
    &:hover {
      transform: scale(1.05);
      box-shadow: var(--shadow-md);
    }
    
    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }
  
  .brand-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
    
    @include mobile {
      display: none;
    }
    
    .brand-title {
      font-size: $font-size-h3;
      font-weight: $font-weight-bold;
      color: var(--text-primary);
      line-height: 1.2;
      letter-spacing: -0.02em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .brand-subtitle {
      font-size: $font-size-caption;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      font-weight: $font-weight-medium;
      white-space: nowrap;
    }
  }
}

// Navigation Section
.nav-section {
  flex: 1;
  display: flex;
  justify-content: center;
  min-width: 0;
  
  @include mobile-and-tablet {
    flex: none;
    order: 3;
    width: 100%;
    justify-content: center;
    margin-top: $spacing-sm;
  }
}

.modern-tabs {
  background: transparent;
  color: var(--text-primary);
  
  :deep(.q-tab) {
    color: var(--text-secondary);
    font-weight: 500;
    font-size: 0.875rem;
    text-transform: none;
    letter-spacing: 0.02em;
    padding: 0.5rem 1.5rem;
    border-radius: 0.5rem;
    margin: 0 0.25rem;
    transition: all 200ms ease-out;
    
    &:hover {
      background: var(--hover);
      color: var(--text-primary);
    }
    
    &.q-tab--active {
      color: var(--primary);
      background: var(--selected);
      font-weight: 600;
    }
    
    .q-tab__icon {
      font-size: 1.1rem;
      margin-right: 0.5rem;
      
      @media (max-width: 479px) {
        margin-right: 0;
      }
    }
    
    .q-tab__label {
      @media (max-width: 479px) {
        display: none;
      }
    }
  }
  
  :deep(.q-tabs__arrow) {
    color: var(--text-secondary);
  }
  
  :deep(.q-tab-panels) {
    background: transparent;
  }
}

// Utility Section
.utility-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-shrink: 0;
  
  @media (max-width: 599px) {
    gap: 0.5rem;
  }
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  background: var(--background-secondary);
  border: 1px solid var(--border);
  transition: all 200ms ease-out;
  
  &.connected {
    background: var(--success-bg);
    border-color: var(--success);
  }
  
  .status-text {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
  }
  
  &.connected .status-text {
    color: var(--success);
  }
}

.settings-btn {
  color: var(--text-secondary);
  
  &:hover {
    background: var(--hover);
    color: var(--text-primary);
  }
}

// Page Container
.modern-page-container {
  background: var(--background-primary);
}

.page-content {
  min-height: calc(100vh - 64px);
  background: var(--background-primary);
  
  @media (max-width: 599px) {
    min-height: calc(100vh - 56px);
  }
}

// Responsive utilities
.hide-on-mobile {
  @media (max-width: 599px) {
    display: none;
  }
}

// Enhanced focus states for accessibility
.modern-toolbar {
  :deep(*:focus) {
    outline: 2px solid var(--focus-ring);
    outline-offset: 2px;
    border-radius: 0.25rem;
  }
}

// Smooth transitions for theme switching
.modern-header,
.modern-toolbar,
.brand-section,
.nav-section,
.utility-section {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}
</style>
