<template>
  <div class="flags-form-container">
    <div class="form-header">
      <div class="header-content">
        <q-icon name="filter_alt" size="sm" color="primary" />
        <h3 class="form-title">Filter Flags</h3>
      </div>
      <div class="header-actions">
        <q-btn
          flat
          size="sm"
          @click="clearAllFilters"
          :disable="!hasActiveFilters"
          class="clear-btn"
        >
          <q-icon name="clear_all" size="xs" />
          Clear All
        </q-btn>
      </div>
    </div>

    <div class="form-content">
      <q-form @submit.prevent="onSubmit" class="filter-form">
        <!-- Primary Filters Row -->
        <div class="filter-row primary-filters">
          <div class="filter-group">
            <label class="filter-label">Sploit</label>
            <q-select
              v-model="sploit"
              :options="sploitOptions"
              placeholder="Select sploit"
              outlined
              dense
              clearable
              class="filter-select"
              behavior="menu"
            >
              <template v-slot:prepend>
                <q-icon name="code" size="sm" color="grey-6" />
              </template>
            </q-select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Team</label>
            <q-select
              v-model="team"
              :options="teamOptions"
              placeholder="Select team"
              outlined
              dense
              clearable
              class="filter-select"
              behavior="menu"
            >
              <template v-slot:prepend>
                <q-icon name="group" size="sm" color="grey-6" />
              </template>
            </q-select>
          </div>

          <div class="filter-group">
            <label class="filter-label">Status</label>
            <q-select
              v-model="status"
              :options="statusOptions"
              placeholder="Select status"
              outlined
              dense
              clearable
              class="filter-select"
              behavior="menu"
            >
              <template v-slot:prepend>
                <q-icon name="task_alt" size="sm" color="grey-6" />
              </template>
            </q-select>
          </div>
        </div>

        <!-- Secondary Filters Row -->
        <div class="filter-row secondary-filters">
          <div class="filter-group">
            <label class="filter-label">Flag Content</label>
            <q-input
              v-model="flag"
              placeholder="Search flag content"
              outlined
              dense
              clearable
              class="filter-input"
            >
              <template v-slot:prepend>
                <q-icon name="flag" size="sm" color="grey-6" />
              </template>
              <template v-slot:hint>
                <span class="input-hint">Substring search, case-insensitive</span>
              </template>
            </q-input>
          </div>

          <div class="filter-group">
            <label class="filter-label">Checksystem Response</label>
            <q-input
              v-model="checksystemResponse"
              placeholder="Search response"
              outlined
              dense
              clearable
              class="filter-input"
            >
              <template v-slot:prepend>
                <q-icon name="psychology" size="sm" color="grey-6" />
              </template>
              <template v-slot:hint>
                <span class="input-hint">Substring search, case-insensitive</span>
              </template>
            </q-input>
          </div>
        </div>

        <!-- Date Range Filters -->
        <div class="filter-row date-filters">
          <div class="filter-group">
            <label class="filter-label">Since</label>
            <q-input
              v-model="since"
              placeholder="yyyy-mm-dd hh:mm"
              outlined
              dense
              clearable
              class="filter-input date-input"
            >
              <template v-slot:prepend>
                <q-icon name="schedule" size="sm" color="grey-6" />
              </template>
              <template v-slot:hint>
                <span class="input-hint">{{ serverTZ || 'Server timezone' }}</span>
              </template>
            </q-input>
          </div>

          <div class="filter-group">
            <label class="filter-label">Until</label>
            <q-input
              v-model="until"
              placeholder="yyyy-mm-dd hh:mm"
              outlined
              dense
              clearable
              class="filter-input date-input"
            >
              <template v-slot:prepend>
                <q-icon name="event" size="sm" color="grey-6" />
              </template>
              <template v-slot:hint>
                <span class="input-hint">{{ serverTZ || 'Server timezone' }}</span>
              </template>
            </q-input>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <q-btn
            type="submit"
            color="primary"
            class="filter-btn"
            :loading="isLoading"
            unelevated
          >
            <q-icon name="search" left />
            Apply Filters
          </q-btn>
          
          <q-btn
            type="button"
            flat
            @click="resetForm"
            class="reset-btn"
            :disable="!hasActiveFilters"
          >
            <q-icon name="restart_alt" left />
            Reset
          </q-btn>
        </div>

        <!-- Active Filters Display -->
        <div v-if="hasActiveFilters" class="active-filters">
          <div class="active-filters-header">
            <q-icon name="filter_list" size="sm" />
            <span>Active Filters:</span>
          </div>
          <div class="active-filters-list">
            <q-chip
              v-for="filter in activeFiltersList"
              :key="filter.key"
              removable
              @remove="removeFilter(filter.key)"
              color="primary"
              text-color="white"
              size="sm"
              class="filter-chip"
            >
              <strong>{{ filter.label }}:</strong> {{ filter.value }}
            </q-chip>
          </div>
        </div>
      </q-form>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions, mapMutations } from "vuex";

export default {
  name: 'FlagsForm',
  
  data() {
    return {
      sploit: null,
      team: null,
      flag: null,
      since: null,
      until: null,
      status: null,
      checksystemResponse: null,
      isLoading: false,
    };
  },
  
  computed: {
    ...mapState({
      sploitOptions: "sploitFilterOptions",
      teamOptions: "teamFilterOptions",
      statusOptions: "statusFilterOptions",
      serverTZ: "serverTZ",
    }),
    
    hasActiveFilters() {
      return !!(this.sploit || this.team || this.flag || this.since || this.until || this.status || this.checksystemResponse);
    },
    
    activeFiltersList() {
      const filters = [];
      
      if (this.sploit) filters.push({ key: 'sploit', label: 'Sploit', value: this.sploit });
      if (this.team) filters.push({ key: 'team', label: 'Team', value: this.team });
      if (this.flag) filters.push({ key: 'flag', label: 'Flag', value: this.flag });
      if (this.since) filters.push({ key: 'since', label: 'Since', value: this.since });
      if (this.until) filters.push({ key: 'until', label: 'Until', value: this.until });
      if (this.status) filters.push({ key: 'status', label: 'Status', value: this.status });
      if (this.checksystemResponse) filters.push({ key: 'checksystemResponse', label: 'Response', value: this.checksystemResponse });
      
      return filters;
    },
  },
  
  methods: {
    async onSubmit() {
      this.isLoading = true;
      
      try {
        const filters = {
          sploit: this.sploit,
          team: this.team,
          flag: this.flag,
          since: this.since,
          until: this.until,
          status: this.status,
          checksystem_response: this.checksystemResponse,
        };

        this.setFlagFilters(filters);
        this.setSelectedPage(1);
        await this.fetchFlags();
        
        // Show success notification
        this.$q.notify({
          type: 'positive',
          message: `Filters applied successfully`,
          timeout: 1500,
        });
        
      } catch (error) {
        this.$q.notify({
          type: 'negative',
          message: 'Failed to apply filters',
          timeout: 2000,
        });
      } finally {
        this.isLoading = false;
      }
    },
    
    resetForm() {
      this.sploit = null;
      this.team = null;
      this.flag = null;
      this.since = null;
      this.until = null;
      this.status = null;
      this.checksystemResponse = null;
      
      this.onSubmit(); // Apply empty filters
    },
    
    clearAllFilters() {
      this.resetForm();
    },
    
    removeFilter(filterKey) {
      this[filterKey] = null;
      this.onSubmit(); // Immediately apply the change
    },
    
    ...mapActions(["fetchFlags"]),
    ...mapMutations(["setSelectedPage", "setFlagFilters"]),
  },
};
</script>

<style lang="scss" scoped>
.flags-form-container {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  :root[data-theme='dark'] & {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: var(--background-secondary);
  border-bottom: 1px solid var(--border);
  
  .header-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    
    .form-title {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--text-primary);
    }
  }
  
  .header-actions {
    .clear-btn {
      color: var(--text-secondary);
      transition: all 150ms ease-out;
      
      &:hover:not(:disabled) {
        color: var(--text-primary);
        background: var(--hover);
      }
      
      &:disabled {
        opacity: 0.5;
      }
    }
  }
}

.form-content {
  padding: 1.5rem;
}

.filter-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.filter-row {
  display: grid;
  gap: 1rem;
  
  &.primary-filters {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  
  &.secondary-filters {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
  
  &.date-filters {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  
  .filter-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }
}

.filter-select,
.filter-input {
  :deep(.q-field__control) {
    border-radius: 8px;
    transition: all 200ms ease-out;
    min-height: 40px;
    
    &:hover {
      border-color: var(--border-hover);
    }
  }
  
  :deep(.q-field__native) {
    font-size: 0.875rem;
    padding: 0 0.75rem;
  }
  
  &:focus-within {
    :deep(.q-field__control) {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px var(--focus-ring);
    }
  }
}

.date-input {
  :deep(.q-field__native) {
    font-family: 'JetBrains Mono', monospace;
  }
}

.input-hint {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-style: italic;
}

.form-actions {
  display: flex;
  gap: 1rem;
  padding-top: 0.5rem;
  
  @media (max-width: 599px) {
    flex-direction: column;
  }
  
  .filter-btn {
    flex: 1;
    max-width: 200px;
    height: 44px;
    font-weight: 500;
    border-radius: 8px;
    transition: all 200ms ease-out;
    
    &:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    @media (max-width: 599px) {
      max-width: none;
    }
  }
  
  .reset-btn {
    color: var(--text-secondary);
    transition: all 150ms ease-out;
    
    &:hover:not(:disabled) {
      color: var(--text-primary);
      background: var(--hover);
    }
    
    &:disabled {
      opacity: 0.5;
    }
  }
}

.active-filters {
  background: var(--background-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 0.5rem;
  
  .active-filters-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .active-filters-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    
    .filter-chip {
      font-size: 0.75rem;
      border-radius: 6px;
      
      :deep(.q-chip__content) {
        padding: 0.25rem 0.5rem;
      }
      
      strong {
        margin-right: 0.25rem;
      }
    }
  }
}

// Enhanced focus states for accessibility
.filter-form {
  :deep(*:focus) {
    outline: 2px solid var(--focus-ring);
    outline-offset: 2px;
  }
}

// Loading state
.filter-btn {
  :deep(.q-spinner) {
    color: currentColor;
  }
}

// Smooth theme transitions
.flags-form-container,
.form-header,
.form-content,
.filter-group,
.active-filters {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}

// Responsive improvements
@media (max-width: 599px) {
  .form-header {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
    
    .header-content .form-title {
      font-size: 1.125rem;
    }
  }
  
  .form-content {
    padding: 1rem;
  }
  
  .filter-row {
    gap: 0.75rem;
  }
}
</style>
