import APIService from '@/services/api'

class AutoRefreshService {
  constructor() {
    this.isEnabled = true
    this.interval = 1000 // 1 second
    this.intervalId = null
    this.callbacks = {
      flags: [],
      chart: []
    }
    this.lastHashes = {
      flags: null,
      chart: null
    }
  }

  /**
   * Start the auto-refresh polling
   */
  start() {
    if (this.intervalId) {
      this.stop()
    }

    this.intervalId = setInterval(() => {
      this.checkForUpdates()
    }, this.interval)

    // Initial check
    this.checkForUpdates()
  }

  /**
   * Stop the auto-refresh polling
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }

  /**
   * Enable auto-refresh
   */
  enable() {
    this.isEnabled = true
    if (!this.intervalId) {
      this.start()
    }
  }

  /**
   * Disable auto-refresh
   */
  disable() {
    this.isEnabled = false
    this.stop()
  }

  /**
   * Set the polling interval
   * @param {number} interval - Interval in milliseconds
   */
  setInterval(interval) {
    this.interval = interval
    if (this.intervalId) {
      this.stop()
      this.start()
    }
  }

  /**
   * Register a callback for flags updates
   * @param {Function} callback - Function to call when flags data changes
   */
  onFlagsUpdate(callback) {
    this.callbacks.flags.push(callback)
  }

  /**
   * Register a callback for chart updates
   * @param {Function} callback - Function to call when chart data changes
   */
  onChartUpdate(callback) {
    this.callbacks.chart.push(callback)
  }

  /**
   * Unregister a callback
   * @param {string} type - 'flags' or 'chart'
   * @param {Function} callback - The callback function to remove
   */
  off(type, callback) {
    const index = this.callbacks[type].indexOf(callback)
    if (index > -1) {
      this.callbacks[type].splice(index, 1)
    }
  }

  /**
   * Check for content updates by comparing hashes
   */
  async checkForUpdates() {
    if (!this.isEnabled) {
      return
    }

    try {
      const response = await APIService.get('/content-hash')
      const { flags_hash, chart_hash } = response.data

      // Check if flags data has changed
      if (this.lastHashes.flags !== null && this.lastHashes.flags !== flags_hash) {
        this.callbacks.flags.forEach(callback => {
          try {
            callback()
          } catch (error) {
            console.error('Error in flags update callback:', error)
          }
        })
      }

      // Check if chart data has changed
      if (this.lastHashes.chart !== null && this.lastHashes.chart !== chart_hash) {
        this.callbacks.chart.forEach(callback => {
          try {
            callback()
          } catch (error) {
            console.error('Error in chart update callback:', error)
          }
        })
      }

      // Update stored hashes
      this.lastHashes.flags = flags_hash
      this.lastHashes.chart = chart_hash

    } catch (error) {
      console.error('Error checking for content updates:', error)
      // Don't spam the console with errors, but continue trying
    }
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      isEnabled: this.isEnabled,
      isRunning: this.intervalId !== null,
      interval: this.interval,
      lastHashes: { ...this.lastHashes }
    }
  }
}

// Create a singleton instance
const autoRefreshService = new AutoRefreshService()

export default autoRefreshService