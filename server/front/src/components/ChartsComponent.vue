<template>
  <div class="charts-container">
    <q-card class="chart-card pa-md">
      <q-card-section>
        <div class="chart-wrapper" v-if="!loading && chartData">
          <v-chart
            :option="chartOption"
            :style="{ height: '400px', width: '100%' }"
            autoresize
          />
        </div>
        
        <div v-else-if="loading" class="chart-loading text-center q-pa-xl">
          <q-spinner-dots size="50px" color="primary" />
          <p class="q-mt-md text-grey-6">Loading chart data...</p>
        </div>
        
        <div v-else-if="error" class="chart-error text-center q-pa-xl">
          <q-icon name="error" size="50px" color="negative" />
          <p class="q-mt-md text-negative">{{ error }}</p>
          <q-btn color="primary" @click="loadChartData">Retry</q-btn>
        </div>
        
        <div v-else class="chart-empty text-center q-pa-xl">
          <q-icon name="bar_chart" size="50px" color="grey-5" />
          <p class="q-mt-md text-grey-6">No data available</p>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import APIService from '@/services/api'
import { useQuasar } from 'quasar'
import autoRefreshService from '@/services/autoRefresh'

// Register ECharts components
use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

export default {
  name: 'ChartsComponent',
  components: {
    VChart
  },
  setup() {
    const $q = useQuasar()
    
    const loading = ref(false)
    const error = ref(null)
    const chartData = ref(null)
    
    const chartOption = computed(() => {
      if (!chartData.value) return {}
      
      const isDark = $q.dark.isActive
      const textColor = isDark ? '#ffffff' : '#333333'
      const backgroundColor = isDark ? 'transparent' : 'transparent'
      
      return {
        backgroundColor,
        textStyle: {
          color: textColor
        },
        title: {
          text: chartData.value.title,
          left: 'center',
          textStyle: {
            color: textColor,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        tooltip: {
          trigger: 'axis',
          backgroundColor: isDark ? '#424242' : '#ffffff',
          borderColor: isDark ? '#616161' : '#e0e0e0',
          textStyle: {
            color: textColor
          }
        },
        legend: {
          orient: 'horizontal',
          top: '8%',
          textStyle: {
            color: textColor
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '15%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: chartData.value.xAxis,
          axisLabel: {
            color: textColor,
            rotate: chartData.value.xAxis?.length > 5 ? 45 : 0
          },
          axisLine: {
            lineStyle: {
              color: isDark ? '#616161' : '#e0e0e0'
            }
          }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: textColor
          },
          axisLine: {
            lineStyle: {
              color: isDark ? '#616161' : '#e0e0e0'
            }
          },
          splitLine: {
            lineStyle: {
              color: isDark ? '#424242' : '#f0f0f0'
            }
          }
        },
        series: chartData.value.series.map(series => ({
          ...series,
          type: 'bar',
          stack: 'total',
          itemStyle: {
            color: series.color
          }
        }))
      }
    })
    
    const loadChartData = async () => {
      loading.value = true
      error.value = null
      
      try {
        const response = await APIService.get('/chart-data')
        chartData.value = response.data
      } catch (err) {
        console.error('Error loading chart data:', err)
        error.value = err.response?.data?.error || 'Failed to load chart data'
        chartData.value = null
      } finally {
        loading.value = false
      }
    }
    
    const handleAutoRefresh = async () => {
      // Auto-refresh callback - refresh chart when content changes
      await loadChartData()
    }
    
    onMounted(() => {
      loadChartData()
      
      // Register for auto-refresh updates
      autoRefreshService.onChartUpdate(handleAutoRefresh)
      
      // Start auto-refresh service if not already running
      if (!autoRefreshService.getStatus().isRunning) {
        autoRefreshService.start()
      }
    })
    
    onBeforeUnmount(() => {
      // Unregister callback when component is destroyed
      autoRefreshService.off('chart', handleAutoRefresh)
    })
    
    return {
      loading,
      error,
      chartData,
      chartOption,
      loadChartData
    }
  }
}
</script>

<style lang="scss" scoped>
.charts-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.chart-card {
  border-radius: var(--radius-lg);
  box-shadow: var(--space-sm) var(--space-sm) var(--space-2xl) rgba(0, 0, 0, 0.1);
  
  .body--dark & {
    background-color: var(--color-bg-dark);
    box-shadow: var(--space-sm) var(--space-sm) var(--space-2xl) rgba(0, 0, 0, 0.3);
  }
}

.chart-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-light);
  
  .body--dark & {
    color: var(--color-text-dark);
  }
}

.chart-controls {
  align-items: center;
}

.chart-wrapper {
  width: 100%;
  min-height: 400px;
}

.chart-loading,
.chart-error,
.chart-empty {
  min-height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

// Responsive adjustments
@media (max-width: 768px) {
  .chart-controls {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-sm);
    
    .q-select {
      min-width: auto !important;
    }
  }
  
  .chart-title {
    font-size: var(--font-size-lg);
    margin-bottom: var(--space-md);
  }
  
  .chart-wrapper {
    min-height: 300px;
  }
}
</style>