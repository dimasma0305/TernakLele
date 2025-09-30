<template>
  <q-card class="flags-table-card pa-md">
    <q-table
      :rows="flags"
      :columns="columns"
      :rows-per-page-options="[flagsPerPage]"
      v-model:pagination="pagination"
      @request="onRequest"
      row-key="flag"
      no-data-label="No flags for you"
      class="flags-table"
      :card-class="$q.dark.isActive ? 'bg-dark' : 'bg-white'"
      flat
      bordered
      :dense="$q.screen.lt.md"
    >
      <template v-slot:top="scope">
        <div class="table-header">
          <div class="text-h5">{{ scope.pagination.rowsNumber }} flags total</div>
          <q-space />
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
          <q-btn
            flat
            round
            dense
            icon="refresh"
            @click="refreshFlags"
            :loading="refreshing"
            class="q-ml-md"
            aria-label="Refresh flags"
          >
            <q-tooltip>Refresh flags</q-tooltip>
          </q-btn>
          <q-btn
            flat
            round
            dense
            icon="settings"
            @click="showAutoRefreshSettings = true"
            class="q-ml-xs"
            aria-label="Auto-refresh settings"
          >
            <q-tooltip>Auto-refresh settings</q-tooltip>
          </q-btn>
          <q-btn
            flat
            round
            dense
            :icon="scope.inFullscreen ? 'fullscreen_exit' : 'fullscreen'"
            @click="scope.toggleFullscreen"
            class="q-ml-md"
            aria-label="Toggle fullscreen"
          />
        </div>
      </template>
      <template v-slot:no-data="{ message }">
        <div class="full-width row flex-center text-accent q-gutter-sm q-pa-lg">
          <q-icon size="2em" name="sentiment_dissatisfied" />
          <span> Well this is sad... {{ message }} </span>
        </div>
      </template>
      <template v-slot:header-cell="props">
        <q-th :props="props" :style="{ textAlign: 'center' }">
          {{ props.col.label }}
        </q-th>
      </template>
      <template v-slot:body-cell="props">
        <q-td :props="props">
          <div class="flex items-center justify-center">
            <span>{{ props.value }}</span>
            <q-btn
              size="sm"
              flat
              round
              :color="$q.dark.isActive ? 'secondary' : 'primary'"
              icon="content_copy"
              v-if="copyableColumns.includes(props.col.name)"
              @click="copyToClipboard(props.value)"
              class="copy-btn"
              aria-label="Copy to clipboard"
            >
              <q-tooltip>Copy to clipboard</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
      <template v-slot:pagination="scope">
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
          @lastPage="scope.lastPage" /></template
    ></q-table>
    
    <!-- Auto-refresh settings dialog -->
    <AutoRefreshSettings v-model="showAutoRefreshSettings" />
  </q-card>
</template>

<script>
import { mapState, mapActions } from "vuex";
import { copyToClipboard } from "quasar";
import moment from "moment";
import { flagsPerPage } from "@/config";
import PaginationCustom from "@/components/PaginationCustom.vue";
import autoRefreshService from "@/services/autoRefresh";
import AutoRefreshSettings from "@/components/AutoRefreshSettings.vue";

export default {
  components: { PaginationCustom, AutoRefreshSettings },
  data: function () {
    return {
      refreshing: false,
      showAutoRefreshSettings: false,
      columns: [
        { name: "sploit", label: "Sploit", field: "sploit", align: "center" },
        { name: "team", label: "Team", field: "team", align: "center" },
        { name: "flag", label: "Flag", field: "flag", align: "center" },
        {
          name: "time",
          label: "Time",
          field: "time",
          align: "center",
          format: (val) => moment.unix(val).format("MMMM Do YYYY, HH:mm:ss"),
        },
        { name: "status", label: "Status", field: "status", align: "center" },
        {
          name: "checksystemResponse",
          label: "Checksystem response",
          field: "checksystemResponse",
          align: "left",
        },
      ],
      copyableColumns: ["sploit", "flag", "checksystemResponse"],
      flagsPerPage,
    };
  },
  computed: {
    pagination: {
      get: function () {
        return {
          page: this.selectedPage,
          rowsPerPage: flagsPerPage,
          rowsNumber: this.totalFlags,
        };
      },
      set: function (newPagination) {
        if (newPagination.page) {
          this.updatePage(newPagination.page);
        }
      },
    },
    ...mapState(["flags", "totalFlags", "selectedPage"]),
  },
  methods: {
    onRequest: async function (props) {
      this.pagination = props.pagination;
    },
    refreshFlags: async function () {
      this.refreshing = true;
      try {
        await this.fetchFlags();
      } finally {
        this.refreshing = false;
      }
    },
    handleAutoRefresh: async function () {
      // Auto-refresh callback - refresh flags when content changes
      await this.fetchFlags();
    },
    copyToClipboard,

    ...mapActions(["updatePage", "fetchFlags"]),
  },
  mounted() {
    // Register for auto-refresh updates
    autoRefreshService.onFlagsUpdate(this.handleAutoRefresh);
    
    // Start auto-refresh service if not already running
    if (!autoRefreshService.getStatus().isRunning) {
      autoRefreshService.start();
    }
  },
  beforeUnmount() {
    // Unregister callback when component is destroyed
    autoRefreshService.off('flags', this.handleAutoRefresh);
  },
};
</script>

<style lang="scss">
.flags-table-card {
  /* Removed all styling that could cause visual effects */
}

.flags-table {
  border-radius: var(--radius-lg);
  overflow: hidden;
  
  .q-table__top {
    padding: var(--space-md) var(--space-lg);
    display: flex;
    align-items: center;
    
    .text-h5 {
      font-weight: var(--font-weight-semibold);
      font-size: var(--font-size-xl);
    }
  }
  
  .table-header {
    width: 100%;
    display: flex;
    align-items: center;
  }
  
  .q-table__container {
    border-radius: var(--radius-lg);
  }
  
  thead tr {
    height: 56px;
    
    th {
      font-weight: var(--font-weight-semibold);
      font-size: var(--font-size-sm);
      color: var(--color-primary);
      transition: all 0.3s ease;
      
      .body--dark & {
        color: var(--color-text-dark);
      }
    }
  }
  
  tbody tr {
    height: 52px;
    transition: background-color 0.2s ease;
    
    &:nth-child(odd) {
      background-color: rgba(0, 0, 0, 0.02);
      
      .body--dark & {
        background-color: rgba(255, 255, 255, 0.03);
      }
    }
    
    &:hover {
      background-color: var(--color-hover-light);
      
      .body--dark & {
        background-color: var(--color-hover-dark);
      }
    }
  }
  
  .copy-btn {
    opacity: 0.7;
    transition: opacity 0.2s ease;
    
    &:hover {
      opacity: 1;
    }
  }
}
</style>
