<template>
  <q-dialog v-model="showDialog" persistent>
    <q-card class="auto-refresh-settings" style="min-width: 400px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">Auto-Refresh Settings</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <div class="q-gutter-md">
          <q-toggle
            v-model="isEnabled"
            label="Enable Auto-Refresh"
            color="primary"
            @update:model-value="toggleAutoRefresh"
          />
          
          <div v-if="isEnabled" class="q-mt-md">
            <q-item-label class="q-mb-sm">Refresh Interval</q-item-label>
            <q-slider
              v-model="intervalSeconds"
              :min="1"
              :max="30"
              :step="1"
              label
              label-always
              color="primary"
              @update:model-value="updateInterval"
            />
            <div class="text-caption text-grey-6 q-mt-xs">
              {{ intervalSeconds }} seconds ({{ Math.round(intervalSeconds / 60 * 100) / 100 }} minutes)
            </div>
          </div>

          <q-separator class="q-my-md" />

          <div class="status-section">
            <q-item-label class="q-mb-sm">Status</q-item-label>
            <div class="row items-center q-gutter-sm">
              <q-icon 
                :name="status.isRunning ? 'play_circle' : 'pause_circle'" 
                :color="status.isRunning ? 'positive' : 'grey'" 
                size="sm"
              />
              <span class="text-body2">
                {{ status.isRunning ? 'Running' : 'Stopped' }}
              </span>
            </div>
            
            <div v-if="status.lastHashes.flags || status.lastHashes.chart" class="q-mt-sm">
              <div class="text-caption text-grey-6">Last Content Hashes:</div>
              <div v-if="status.lastHashes.flags" class="text-caption">
                Flags: {{ status.lastHashes.flags.substring(0, 8) }}...
              </div>
              <div v-if="status.lastHashes.chart" class="text-caption">
                Chart: {{ status.lastHashes.chart.substring(0, 8) }}...
              </div>
            </div>
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="Close" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import autoRefreshService from '@/services/autoRefresh'

export default {
  name: 'AutoRefreshSettings',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const isEnabled = ref(true)
    const intervalSeconds = ref(5)
    const status = ref({})
    let statusInterval = null

    const showDialog = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const updateStatus = () => {
      status.value = autoRefreshService.getStatus()
      isEnabled.value = status.value.isEnabled
      intervalSeconds.value = Math.round(status.value.interval / 1000)
    }

    const toggleAutoRefresh = (enabled) => {
      if (enabled) {
        autoRefreshService.enable()
      } else {
        autoRefreshService.disable()
      }
      updateStatus()
    }

    const updateInterval = (seconds) => {
      const milliseconds = seconds * 1000
      autoRefreshService.setInterval(milliseconds)
      updateStatus()
    }

    onMounted(() => {
      updateStatus()
      // Update status every second while dialog is open
      statusInterval = setInterval(updateStatus, 1000)
    })

    onBeforeUnmount(() => {
      if (statusInterval) {
        clearInterval(statusInterval)
      }
    })

    return {
      showDialog,
      isEnabled,
      intervalSeconds,
      status,
      toggleAutoRefresh,
      updateInterval
    }
  }
}
</script>

<style lang="scss" scoped>
.auto-refresh-settings {
  .status-section {
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: 8px;
    padding: 12px;
    
    .body--dark & {
      background-color: rgba(255, 255, 255, 0.05);
    }
  }
}
</style>