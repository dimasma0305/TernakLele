<template>
  <div class="analytics-page">
    <div class="page-header q-mb-lg">
      <h4 class="page-title text-weight-semibold q-ma-none">Analytics Dashboard</h4>
      <p class="page-subtitle text-grey-6 q-mt-sm q-mb-none">
        Visualize flag submission data and team performance metrics
      </p>
    </div>
    
    <ChartsComponent />
  </div>
</template>

<script>
import ChartsComponent from '@/components/ChartsComponent.vue'

export default {
  name: 'AnalyticsView',
  components: {
    ChartsComponent
  }
}
</script>

<style lang="scss" scoped>
.analytics-page {
  padding: var(--space-lg);
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
  .analytics-page {
    padding: var(--space-md);
  }
  
  .page-title {
    font-size: var(--font-size-xl);
  }
  
  .page-subtitle {
    font-size: var(--font-size-sm);
  }
}
</style>