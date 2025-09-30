<template>
  <q-card class="teams-table-card pa-md">
    <q-table
      virtual-scroll
      dense
      :rows="teams"
      :columns="columns"
      :rows-per-page-options="[0]"
      style="height: 80vh"
      row-key="name"
      no-data-label="No teams to attack"
      class="teams-table"
      :card-class="$q.dark.isActive ? 'bg-dark' : 'bg-white'"
      flat
      bordered
    >
      <template v-slot:top>
        <div class="table-header">
          <div class="text-h5">{{ teams.length }} teams total</div>
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
              v-if="props.col.name === 'address'"
              size="sm"
              flat
              round
              :color="$q.dark.isActive ? 'secondary' : 'primary'"
              icon="content_copy"
              @click="copyToClipboard(props.value)"
              class="copy-btn"
              aria-label="Copy to clipboard"
            >
              <q-tooltip>Copy to clipboard</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>
  </q-card>
</template>

<script>
import { mapState } from "vuex";
import { copyToClipboard } from "quasar";

export default {
  data: function () {
    return {
      columns: [
        { name: "name", label: "Name", field: "name", align: "center" },
        {
          name: "address",
          label: "Address",
          field: "address",
          align: "center",
        },
      ],
    };
  },
  computed: mapState(["teams"]),
  methods: { copyToClipboard },
};
</script>

<style lang="scss">
.teams-table-card {
  /* Removed all styling that could cause visual effects */
}

.teams-table {
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
