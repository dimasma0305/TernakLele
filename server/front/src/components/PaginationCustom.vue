<template>
  <div class="pagination">
    <span class="message">
      {{ paginationMessage }}
    </span>
    <div class="pagination-buttons">
      <q-btn
        v-if="pagesNumber > 2"
        icon="first_page"
        :color="$q.dark.isActive ? 'secondary' : 'primary'"
        round
        dense
        flat
        :disable="isFirstPage"
        @click="$emit('firstPage')"
      >
        <q-tooltip>First Page</q-tooltip>
      </q-btn>

      <q-btn
        icon="chevron_left"
        :color="$q.dark.isActive ? 'secondary' : 'primary'"
        round
        dense
        flat
        :disable="isFirstPage"
        @click="$emit('prevPage')"
      >
        <q-tooltip>Previous Page</q-tooltip>
      </q-btn>

      <q-btn
        icon="chevron_right"
        :color="$q.dark.isActive ? 'secondary' : 'primary'"
        round
        dense
        flat
        :disable="isLastPage"
        @click="$emit('nextPage')"
      >
        <q-tooltip>Next Page</q-tooltip>
      </q-btn>
      
      <q-btn
        v-if="pagesNumber > 2"
        icon="last_page"
        :color="$q.dark.isActive ? 'secondary' : 'primary'"
        round
        dense
        flat
        :disable="isLastPage"
        @click="$emit('lastPage')"
      >
        <q-tooltip>Last Page</q-tooltip>
      </q-btn>
    </div>
  </div>
</template>

<script>
export default {
  name: "PaginationCustom",
  props: {
    pagesNumber: Number,
    isFirstPage: Boolean,
    isLastPage: Boolean,

    page: Number,
    pageSize: Number,
    total: Number,
  },
  computed: {
    paginationMessage: function () {
      const firstRow = this.pageSize * (this.page - 1) + 1;
      const lastRow = Math.min(this.pageSize * this.page, this.total);
      return `${firstRow}-${lastRow} of ${this.total}`;
    },
  },
  emits: ["firstPage", "prevPage", "nextPage", "lastPage"],
};
</script>

<style lang="scss" scoped>
.pagination {
  font-size: 0.9em;
  display: flex;
  align-items: center;

  > .message {
    margin-right: 1em;
    font-weight: 500;
  }
  
  .pagination-buttons {
    display: flex;
    align-items: center;
    
    .q-btn {
      margin: 0 2px;
      transition: all 0.2s ease;
      
      &:not(:disabled):hover {
        background: rgba(0, 0, 0, 0.05);
        
        .body--dark & {
          background: rgba(255, 255, 255, 0.1);
        }
      }
      
      &:disabled {
        opacity: 0.5;
      }
    }
  }
}
</style>
