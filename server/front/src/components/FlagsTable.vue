<template>
  <div class="flags-table-container">
    <q-table
      :rows="flags"
      :columns="columns"
      :rows-per-page-options="[flagsPerPage]"
      v-model:pagination="pagination"
      @request="onRequest"
      row-key="flag"
      no-data-label="No flags available"
      class="modern-flags-table"
      dense
      flat
      bordered
    >
      <!-- Top section with stats and controls -->
      <template v-slot:top="scope">
        <div class="table-header-section">
          <div class="table-stats">
            <div class="stats-main">
              <q-icon name="flag" size="sm" color="primary" />
              <span class="stats-count">{{ scope.pagination.rowsNumber }}</span>
              <span class="stats-label">Total Flags</span>
            </div>
            <div v-if="scope.pagination.rowsNumber > 0" class="stats-secondary">
              <span class="stats-info">
                Showing {{ getShowingText(scope.pagination) }}
              </span>
            </div>
          </div>
          
          <div class="table-controls">
            <pagination-custom
              :pagesNumber="scope.pagesNumber"
              :isFirstPage="scope.isFirstPage"
              :isLastPage="scope.isLastPage"
              :page="scope.pagination.page"
              :pageSize="scope.pagination.rowsPerPage"
              :total="scope.pagination.rowsNumber"
              @firstPage="scope.firstPage"
              @prevPage="scope.prevPage"
              @nextPage="scope.nextPage"
              @lastPage="scope.lastPage"
              compact
            />
            
            <q-btn
              flat
              round
              dense
              :icon="scope.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
              @click="scope.toggleFullscreen"
              class="fullscreen-btn"
              :title="scope.inFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
            />
            
            <q-btn
              flat
              round
              dense
              icon="refresh"
              @click="refreshData"
              class="refresh-btn"
              :loading="isRefreshing"
              title="Refresh data"
            />
          </div>
        </div>
      </template>

      <!-- Empty state -->
      <template v-slot:no-data="{ message }">
        <div class="table-empty">
          <div class="empty-icon">
            <q-icon name="inbox" size="4rem" color="grey-4" />
          </div>
          <div class="empty-title">No Flags Found</div>
          <div class="empty-description">{{ message }}</div>
          <q-btn
            color="primary"
            outline
            @click="refreshData"
            class="empty-action"
          >
            <q-icon name="refresh" left />
            Refresh
          </q-btn>
        </div>
      </template>

      <!-- Enhanced header cells -->
      <template v-slot:header-cell="props">
        <q-th :props="props" class="table-header-cell">
          <div class="header-content">
            <span class="header-label">{{ props.col.label }}</span>
            <q-icon
              v-if="props.col.sortable !== false"
              name="unfold_more"
              size="xs"
              class="sort-icon"
            />
          </div>
        </q-th>
      </template>

      <!-- Enhanced body cells with proper formatting -->
      <template v-slot:body-cell="props">
        <q-td :props="props" class="table-body-cell">
          <div class="cell-content" :class="`cell-${props.col.name}`">
            <!-- Flag value with copy button -->
            <template v-if="props.col.name === 'flag'">
              <div class="flag-cell">
                <code class="flag-value">{{ props.value }}</code>
                <q-btn
                  size="sm"
                  flat
                  round
                  icon="content_copy"
                  @click="copyToClipboard(props.value)"
                  class="copy-btn"
                  title="Copy flag"
                />
              </div>
            </template>
            
            <!-- Status with colored badge -->
            <template v-else-if="props.col.name === 'status'">
              <div class="status-cell">
                <q-badge
                  :color="getStatusColor(props.value)"
                  :label="props.value"
                  class="status-badge"
                />
              </div>
            </template>
            
            <!-- Time with enhanced formatting -->
            <template v-else-if="props.col.name === 'time'">
              <div class="time-cell">
                <div class="time-value">{{ formatTime(props.value) }}</div>
                <div class="time-relative">{{ getRelativeTime(props.value) }}</div>
              </div>
            </template>
            
            <!-- Checksystem response with formatting -->
            <template v-else-if="props.col.name === 'checksystemResponse'">
              <div class="response-cell">
                <code class="response-text">{{ props.value }}</code>
                <q-btn
                  v-if="props.value && copyableColumns.includes(props.col.name)"
                  size="sm"
                  flat
                  round
                  icon="content_copy"
                  @click="copyToClipboard(props.value)"
                  class="copy-btn"
                  title="Copy response"
                />
              </div>
            </template>
            
            <!-- Other copyable fields -->
            <template v-else-if="copyableColumns.includes(props.col.name)">
              <div class="copyable-cell">
                <span class="cell-value">{{ props.value }}</span>
                <q-btn
                  size="sm"
                  flat
                  round
                  icon="content_copy"
                  @click="copyToClipboard(props.value)"
                  class="copy-btn"
                  title="Copy value"
                />
              </div>
            </template>
            
            <!-- Default cell -->
            <template v-else>
              <span class="cell-value">{{ props.value }}</span>
            </template>
          </div>
        </q-td>
      </template>

      <!-- Enhanced pagination -->
      <template v-slot:pagination="scope">
        <div class="table-pagination-section">
          <div class="pagination-info">
            <span>{{ getPaginationText(scope.pagination) }}</span>
          </div>
          
          <pagination-custom
            :pagesNumber="scope.pagesNumber"
            :isFirstPage="scope.isFirstPage"
            :isLastPage="scope.isLastPage"
            :page="scope.pagination.page"
            :pageSize="scope.pagination.rowsPerPage"
            :total="scope.pagination.rowsNumber"
            @firstPage="scope.firstPage"
            @prevPage="scope.prevPage"
            @nextPage="scope.nextPage"
            @lastPage="scope.lastPage"
          />
        </div>
      </template>
    </q-table>
  </div>
</template>

<script>
import { mapState, mapActions } from "vuex";
import { copyToClipboard } from "quasar";
import moment from "moment";
import { flagsPerPage } from "@/config";
import PaginationCustom from "@/components/PaginationCustom.vue";

export default {
  name: 'FlagsTable',
  
  components: { PaginationCustom },
  
  data() {
    return {
      columns: [
        { 
          name: "sploit", 
          label: "Sploit", 
          field: "sploit", 
          align: "left",
          sortable: true,
        },
        { 
          name: "team", 
          label: "Team", 
          field: "team", 
          align: "left",
          sortable: true,
        },
        { 
          name: "flag", 
          label: "Flag", 
          field: "flag", 
          align: "left",
          sortable: false,
        },
        {
          name: "time",
          label: "Submitted",
          field: "time",
          align: "left",
          sortable: true,
          format: (val) => this.formatTime(val),
        },
        { 
          name: "status", 
          label: "Status", 
          field: "status", 
          align: "center",
          sortable: true,
        },
        {
          name: "checksystemResponse",
          label: "Response",
          field: "checksystemResponse",
          align: "left",
          sortable: false,
        },
      ],
      copyableColumns: ["sploit", "flag", "checksystemResponse"],
      flagsPerPage,
      isRefreshing: false,
    };
  },
  
  computed: {
    pagination: {
      get() {
        return {
          page: this.selectedPage,
          rowsPerPage: flagsPerPage,
          rowsNumber: this.totalFlags,
        };
      },
      set(newPagination) {
        if (newPagination.page) {
          this.updatePage(newPagination.page);
        }
      },
    },
    
    ...mapState(["flags", "totalFlags", "selectedPage"]),
  },
  
  methods: {
    async onRequest(props) {
      this.pagination = props.pagination;
    },
    
    async refreshData() {
      this.isRefreshing = true;
      try {
        await this.fetchFlags();
        this.$q.notify({
          type: 'positive',
          message: 'Data refreshed',
          timeout: 1000,
        });
      } catch (error) {
        this.$q.notify({
          type: 'negative',
          message: 'Failed to refresh data',
          timeout: 2000,
        });
      } finally {
        this.isRefreshing = false;
      }
    },
    
    copyToClipboard(value) {
      copyToClipboard(value);
      this.$q.notify({
        type: 'positive',
        message: 'Copied to clipboard',
        timeout: 1000,
        position: 'top',
      });
    },
    
    formatTime(timestamp) {
      return moment.unix(timestamp).format("MMM Do, HH:mm:ss");
    },
    
    getRelativeTime(timestamp) {
      return moment.unix(timestamp).fromNow();
    },
    
    getStatusColor(status) {
      const statusColors = {
        'ACCEPTED': 'positive',
        'REJECTED': 'negative',
        'PENDING': 'warning',
        'SUBMITTED': 'info',
        'ERROR': 'negative',
        'QUEUED': 'grey',
      };
      return statusColors[status?.toUpperCase()] || 'grey';
    },
    
    getShowingText(pagination) {
      const start = (pagination.page - 1) * pagination.rowsPerPage + 1;
      const end = Math.min(pagination.page * pagination.rowsPerPage, pagination.rowsNumber);
      return `${start}-${end} of ${pagination.rowsNumber}`;
    },
    
    getPaginationText(pagination) {
      const start = (pagination.page - 1) * pagination.rowsPerPage + 1;
      const end = Math.min(pagination.page * pagination.rowsPerPage, pagination.rowsNumber);
      return `Showing ${start} to ${end} of ${pagination.rowsNumber} entries`;
    },
    
    ...mapActions(["updatePage", "fetchFlags"]),
  },
};
</script>

<style lang="scss" scoped>
.flags-table-container {
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  :root[data-theme='dark'] & {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}

.modern-flags-table {
  background: transparent;
  
  // Enhanced header styling
  :deep(.q-table__top) {
    padding: 1.5rem;
    background: var(--background-secondary);
    border-bottom: 1px solid var(--border);
  }
  
  :deep(.q-table__bottom) {
    padding: 1rem 1.5rem;
    background: var(--background-secondary);
    border-top: 1px solid var(--border);
  }
  
  // Table header styling
  :deep(thead tr) {
    background: var(--background-secondary);
  }
  
  :deep(th) {
    background: var(--background-secondary) !important;
    color: var(--text-primary) !important;
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 1rem;
    border-bottom: 2px solid var(--border);
  }
  
  // Table body styling
  :deep(tbody tr) {
    background: var(--surface);
    transition: background-color 150ms ease-out;
    
    &:hover {
      background: var(--hover) !important;
    }
    
    &:nth-child(even) {
      background: var(--background-secondary);
      
      &:hover {
        background: var(--hover) !important;
      }
    }
  }
  
  :deep(td) {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    color: var(--text-primary);
  }
  
  // Remove default Quasar styling
  :deep(.q-table__card) {
    box-shadow: none;
    border-radius: 0;
  }
}

// Table header section
.table-header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
}

.table-stats {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  
  .stats-main {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    
    .stats-count {
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--primary);
    }
    
    .stats-label {
      font-size: 1rem;
      font-weight: 500;
      color: var(--text-primary);
    }
  }
  
  .stats-secondary {
    .stats-info {
      font-size: 0.875rem;
      color: var(--text-secondary);
    }
  }
}

.table-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  .fullscreen-btn,
  .refresh-btn {
    color: var(--text-secondary);
    transition: all 150ms ease-out;
    
    &:hover {
      color: var(--text-primary);
      background: var(--hover);
    }
  }
}

// Enhanced table cells
.table-header-cell {
  .header-content {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    
    .header-label {
      flex: 1;
    }
    
    .sort-icon {
      opacity: 0.5;
      transition: opacity 150ms ease-out;
    }
  }
  
  &:hover .sort-icon {
    opacity: 1;
  }
}

.table-body-cell {
  .cell-content {
    min-height: 2rem;
    display: flex;
    align-items: center;
  }
}

// Specialized cell types
.flag-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  .flag-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
    background: var(--code-bg);
    color: var(--code-text);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--code-border);
    word-break: break-all;
    flex: 1;
  }
}

.status-cell {
  .status-badge {
    font-weight: 500;
    font-size: 0.75rem;
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }
}

.time-cell {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  
  .time-value {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 0.875rem;
  }
  
  .time-relative {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-style: italic;
  }
}

.response-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  .response-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8125rem;
    background: var(--code-bg);
    color: var(--code-text);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    border: 1px solid var(--code-border);
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.copyable-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  .cell-value {
    flex: 1;
  }
}

.copy-btn {
  opacity: 0;
  transition: opacity 150ms ease-out;
  color: var(--text-secondary);
  
  &:hover {
    color: var(--primary);
  }
}

.table-body-cell:hover .copy-btn {
  opacity: 1;
}

// Empty state
.table-empty {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--text-secondary);
  
  .empty-icon {
    margin-bottom: 1rem;
  }
  
  .empty-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
  }
  
  .empty-description {
    margin-bottom: 1.5rem;
    font-size: 0.875rem;
  }
  
  .empty-action {
    border-radius: 6px;
  }
}

// Pagination section
.table-pagination-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
  
  .pagination-info {
    font-size: 0.875rem;
    color: var(--text-secondary);
    
    @media (max-width: 768px) {
      order: 2;
    }
  }
}

// Loading state
.modern-flags-table[loading] {
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--surface);
    opacity: 0.8;
    z-index: 1;
  }
}

// Responsive adjustments
@media (max-width: 768px) {
  .flags-table-container {
    border-radius: 8px;
  }
  
  .modern-flags-table {
    :deep(.q-table__top),
    :deep(.q-table__bottom) {
      padding: 1rem;
    }
    
    :deep(th),
    :deep(td) {
      padding: 0.75rem 0.5rem;
    }
  }
  
  .flag-cell .flag-value,
  .response-cell .response-text {
    max-width: 150px;
  }
}

// Smooth theme transitions
.flags-table-container,
.modern-flags-table,
.table-header-section,
.table-stats,
.table-controls {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}
</style>
