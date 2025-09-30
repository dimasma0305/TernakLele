<template>
  <q-page class="q-pa-md"
    >
    <div class="row q-pt-md justify-center">
      <div class="col">
        <ChartsComponent />
      </div>
    </div>
    <div class="row justify-between q-col-gutter-md">
      <div class="col col-12 col-md-8"><flags-form /></div>
      <div class="col col-12 col-md-4"><flags-submit /></div>
    </div>
    <div class="row q-pt-md justify-center">
      <div class="col">
        <flags-table />
      </div>
    </div>
  </q-page>
</template>

<script>
import FlagsForm from "@/components/FlagsForm.vue";
import FlagsSubmit from "@/components/FlagsSubmit.vue";
import FlagsTable from "@/components/FlagsTable.vue";
import ChartsComponent from "@/components/ChartsComponent.vue";
import { mapActions } from "vuex";
import { flagsPerPage } from "@/config";
export default {
  components: { FlagsForm, FlagsSubmit, FlagsTable, ChartsComponent },
  methods: mapActions(["fetchFlags"]),
  created: async function () {
    await this.fetchFlags({ page: 1, pageSize: flagsPerPage });
  },
};
</script>

<style lang="scss" scoped>
.analytics-section {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: var(--space-2xl);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-light);
  
  .body--dark & {
    color: var(--color-text-dark);
  }
}

.page-subtitle {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary-light);
  
  .body--dark & {
    color: var(--color-text-secondary-dark);
  }
}

// Responsive adjustments
@media (max-width: 768px) {
  .page-title {
    font-size: var(--font-size-xl);
  }
  
  .page-subtitle {
    font-size: var(--font-size-sm);
  }
}
</style>
