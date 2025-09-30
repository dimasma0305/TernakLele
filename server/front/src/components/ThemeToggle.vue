<template>
  <div class="theme-toggle">
    <!-- Simple toggle button for mobile/compact view -->
    <q-btn
      v-if="compact"
      flat
      round
      :icon="themeIcon"
      @click="toggleTheme"
      :title="themeTooltip"
      class="theme-toggle-btn"
    />
    
    <!-- Full theme selector for desktop -->
    <q-btn-dropdown
      v-else
      flat
      :icon="themeIcon"
      :label="compact ? '' : currentThemeLabel"
      class="theme-selector"
      :title="themeTooltip"
    >
      <q-list>
        <q-item
          v-for="option in themeOptions"
          :key="option.value"
          clickable
          v-close-popup
          @click="setThemeMode(option.value)"
          :class="{ 'bg-primary text-white': currentTheme === option.value }"
        >
          <q-item-section avatar>
            <q-icon :name="option.icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ option.label }}</q-item-label>
            <q-item-label caption>{{ option.description }}</q-item-label>
          </q-item-section>
          <q-item-section side v-if="currentTheme === option.value">
            <q-icon name="check" color="white" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-btn-dropdown>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';

export default {
  name: 'ThemeToggle',
  
  props: {
    compact: {
      type: Boolean,
      default: false,
    },
  },
  
  data() {
    return {
      themeOptions: [
        {
          value: 'light',
          label: 'Light Mode',
          description: 'Classic light theme',
          icon: 'light_mode',
        },
        {
          value: 'dark',
          label: 'Dark Mode',
          description: 'Easy on the eyes',
          icon: 'dark_mode',
        },
        {
          value: 'auto',
          label: 'Auto',
          description: 'Follow system preference',
          icon: 'brightness_auto',
        },
      ],
    };
  },
  
  computed: {
    ...mapState({
      currentTheme: (state) => state.ui.theme,
    }),
    
    ...mapGetters(['currentActiveTheme', 'isDarkMode']),
    
    themeIcon() {
      switch (this.currentTheme) {
        case 'light':
          return 'light_mode';
        case 'dark':
          return 'dark_mode';
        case 'auto':
          return 'brightness_auto';
        default:
          return 'brightness_auto';
      }
    },
    
    currentThemeLabel() {
      const option = this.themeOptions.find(opt => opt.value === this.currentTheme);
      return option ? option.label : 'Theme';
    },
    
    themeTooltip() {
      const option = this.themeOptions.find(opt => opt.value === this.currentTheme);
      return option ? `Current: ${option.label}` : 'Toggle theme';
    },
  },
  
  methods: {
    ...mapActions(['toggleTheme', 'setThemeMode']),
  },
};
</script>

<style lang="scss" scoped>
.theme-toggle {
  display: flex;
  align-items: center;
}

.theme-toggle-btn {
  color: var(--text-primary);
  transition: all 150ms ease-out;
  
  &:hover {
    background-color: var(--hover);
    transform: scale(1.05);
  }
  
  &:active {
    transform: scale(0.95);
  }
}

.theme-selector {
  color: var(--text-primary);
  
  :deep(.q-btn-dropdown__arrow) {
    color: var(--text-secondary);
  }
  
  &:hover {
    background-color: var(--hover);
  }
}

// Theme-specific icon animations
.theme-toggle-btn .q-icon {
  transition: transform 300ms ease-in-out;
}

// Rotate sun icon when switching to light mode
:root[data-theme='light'] .theme-toggle-btn .q-icon {
  transform: rotate(180deg);
}

// Subtle glow effect for dark mode icon
:root[data-theme='dark'] .theme-toggle-btn .q-icon {
  filter: drop-shadow(0 0 2px rgba(255, 255, 255, 0.3));
}

// Auto mode gets a subtle pulse
:root .theme-toggle-btn .q-icon[data-icon='brightness_auto'] {
  animation: theme-pulse 2s ease-in-out infinite;
}

@keyframes theme-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

// Mobile responsive adjustments
@media (max-width: 599px) {
  .theme-selector {
    :deep(.q-btn__content) {
      .q-btn__text {
        display: none;
      }
    }
  }
}
</style>