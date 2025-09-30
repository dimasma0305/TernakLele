<template>
  <div class="teams-table-container">
    <q-table
      virtual-scroll
      dense
      :rows="teams"
      :columns="columns"
      :rows-per-page-options="[0]"
      style="height: 80vh"
      row-key="name"
      no-data-label="No teams to attack"
      class="modern-teams-table"
      flat
      bordered
    >
      <!-- Enhanced header -->
      <template v-slot:top>
        <div class="table-header-section">
          <div class="table-stats">
            <div class="stats-main">
              <q-icon name="groups" size="sm" color="primary" />
              <span class="stats-count">{{ teams.length }}</span>
              <span class="stats-label">Teams Available</span>
            </div>
            <div v-if="teams.length > 0" class="stats-secondary">
              <span class="stats-info">CTF target teams for exploitation</span>
            </div>
          </div>
          
          <div class="table-controls">
            <q-btn
              flat
              round
              dense
              icon="refresh"
              @click="refreshTeams"
              class="refresh-btn"
              :loading="isRefreshing"
              title="Refresh teams"
            />
          </div>
        </div>
      </template>

      <!-- Enhanced empty state -->
      <template v-slot:no-data="{ message }">
        <div class="table-empty">
          <div class="empty-icon">
            <q-icon name="groups_off" size="4rem" color="grey-4" />
          </div>
          <div class="empty-title">No Teams Available</div>
          <div class="empty-description">{{ message }}</div>
          <q-btn
            color="primary"
            outline
            @click="refreshTeams"
            class="empty-action"
          >
            <q-icon name="refresh" left />
            Refresh Teams
          </q-btn>
        </div>
      </template>

      <!-- Enhanced header cells -->
      <template v-slot:header-cell="props">
        <q-th :props="props" class="table-header-cell">
          <div class="header-content">
            <span class="header-label">{{ props.col.label }}</span>
          </div>
        </q-th>
      </template>

      <!-- Enhanced body cells -->
      <template v-slot:body-cell-name="props">
        <q-td :props="props" class="table-body-cell">
          <div class="team-name-cell">
            <q-avatar size="32px" class="team-avatar">
              <q-icon name="group" />
            </q-avatar>
            <div class="team-info">
              <div class="team-name">{{ props.value }}</div>
              <div class="team-status">Active Target</div>
            </div>
          </div>
        </q-td>
      </template>

      <template v-slot:body-cell-address="props">
        <q-td :props="props" class="table-body-cell">
          <div class="address-cell">
            <code class="address-value">{{ props.value }}</code>
            <q-btn
              size="sm"
              flat
              round
              icon="content_copy"
              @click="copyToClipboard(props.value)"
              class="copy-btn"
              title="Copy address"
            />
            <q-btn
              size="sm"
              flat
              round
              icon="launch"
              @click="openAddress(props.value)"
              class="launch-btn"
              title="Open in new tab"
            />
          </div>
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script>
import { mapState, mapActions } from "vuex";
import { copyToClipboard } from "quasar";

export default {
  name: 'TeamsTable',
  
  data() {
    return {
      columns: [
        { 
          name: "name", 
          label: "Team Name", 
          field: "name", 
          align: "left",
          sortable: true,
        },
        {
          name: "address",
          label: "Target Address",
          field: "address",
          align: "left",
          sortable: true,
        },
      ],
      isRefreshing: false,
    };
  },
  
  computed: {
    ...mapState(['teams']),
  },
  
  methods: {
    copyToClipboard(value) {
      copyToClipboard(value);
      this.$q.notify({
        type: 'positive',
        message: 'Address copied to clipboard',
        timeout: 1000,
      });
    },
    
    openAddress(address) {
      // Check if address has protocol, if not add http://
      const url = address.startsWith('http') ? address : `http://${address}`;
      window.open(url, '_blank');
    },
    
    async refreshTeams() {
      this.isRefreshing = true;
      try {
        await this.fetchTeams();
        this.$q.notify({
          type: 'positive',
          message: 'Teams refreshed',
          timeout: 1000,
        });
      } catch (error) {
        this.$q.notify({
          type: 'negative',
          message: 'Failed to refresh teams',
          timeout: 2000,
        });
      } finally {
        this.isRefreshing = false;
      }
    },
    
    ...mapActions(['fetchTeams']),
  },
};
</script>

<style lang="scss" scoped>
.teams-table-container {
  background: var(--surface);
  border-radius: 12px;
  border: 1px solid var(--border);
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  :root[data-theme='dark'] & {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}

.modern-teams-table {
  background: transparent;
  
  // Enhanced header styling
  :deep(.q-table__top) {
    padding: 1.5rem;
    background: var(--background-secondary);
    border-bottom: 1px solid var(--border);
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
  }
}

.table-body-cell {
  .cell-content {
    min-height: 3rem;
    display: flex;
    align-items: center;
  }
}

// Team name cell
.team-name-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  .team-avatar {
    background: var(--primary);
    color: var(--primary-contrast);
    border: 2px solid var(--border);
  }
  
  .team-info {
    display: flex;
    flex-direction: column;
    gap: 0.125rem;
    
    .team-name {
      font-weight: 600;
      color: var(--text-primary);
      font-size: 0.875rem;
    }
    
    .team-status {
      font-size: 0.75rem;
      color: var(--success);
      font-weight: 500;
      text-transform: uppercase;
      letter-spacing: 0.02em;
    }
  }
}

// Address cell
.address-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  .address-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.875rem;
    background: var(--code-bg);
    color: var(--code-text);
    padding: 0.375rem 0.75rem;
    border-radius: 6px;
    border: 1px solid var(--code-border);
    flex: 1;
    word-break: break-all;
  }
}

.copy-btn,
.launch-btn {
  opacity: 0;
  transition: opacity 150ms ease-out;
  color: var(--text-secondary);
  
  &:hover {
    color: var(--primary);
  }
}

.launch-btn:hover {
  color: var(--info);
}

.table-body-cell:hover {
  .copy-btn,
  .launch-btn {
    opacity: 1;
  }
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

// Responsive adjustments
@media (max-width: 768px) {
  .teams-table-container {
    border-radius: 8px;
  }
  
  .modern-teams-table {
    :deep(.q-table__top) {
      padding: 1rem;
    }
    
    :deep(th),
    :deep(td) {
      padding: 0.75rem 0.5rem;
    }
  }
  
  .team-name-cell {
    .team-avatar {
      width: 28px;
      height: 28px;
    }
    
    .team-info .team-name {
      font-size: 0.8125rem;
    }
  }
  
  .address-cell .address-value {
    padding: 0.25rem 0.5rem;
    font-size: 0.8125rem;
  }
}

// Smooth theme transitions
.teams-table-container,
.modern-teams-table,
.table-header-section,
.table-stats,
.table-controls {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}
</style>
