import APIService from "./services/api"

type CallbackFunction = () => void

interface ContentHash {
  flags_hash: string
  chart_hash: string
  timestamp: number
}

class AutoRefreshService {
  private isEnabled = true
  private interval = 5000 // 5 seconds
  private intervalId: NodeJS.Timeout | null = null
  private callbacks: {
    flags: CallbackFunction[]
    chart: CallbackFunction[]
  } = {
    flags: [],
    chart: [],
  }
  private lastHashes: {
    flags: string | null
    chart: string | null
  } = {
    flags: null,
    chart: null,
  }

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

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }
  }

  enable() {
    this.isEnabled = true
    if (!this.intervalId) {
      this.start()
    }
  }

  disable() {
    this.isEnabled = false
    this.stop()
  }

  setInterval(interval: number) {
    this.interval = interval
    if (this.intervalId) {
      this.stop()
      this.start()
    }
  }

  onFlagsUpdate(callback: CallbackFunction) {
    this.callbacks.flags.push(callback)
  }

  onChartUpdate(callback: CallbackFunction) {
    this.callbacks.chart.push(callback)
  }

  off(type: "flags" | "chart", callback: CallbackFunction) {
    const index = this.callbacks[type].indexOf(callback)
    if (index > -1) {
      this.callbacks[type].splice(index, 1)
    }
  }

  async checkForUpdates() {
    if (!this.isEnabled) {
      return
    }

    try {
      const response = await APIService.get("/content-hash")
      const { flags_hash, chart_hash } = response.data

      // Check if flags data has changed
      if (this.lastHashes.flags !== null && this.lastHashes.flags !== flags_hash) {
        this.callbacks.flags.forEach((callback) => {
          try {
            callback()
          } catch (error) {
            console.error("Error in flags update callback:", error)
          }
        })
      }

      // Check if chart data has changed
      if (this.lastHashes.chart !== null && this.lastHashes.chart !== chart_hash) {
        this.callbacks.chart.forEach((callback) => {
          try {
            callback()
          } catch (error) {
            console.error("Error in chart update callback:", error)
          }
        })
      }

      // Update stored hashes
      this.lastHashes.flags = flags_hash
      this.lastHashes.chart = chart_hash
    } catch (error) {
      console.error("Error checking for content updates:", error)
    }
  }

  getStatus() {
    return {
      isEnabled: this.isEnabled,
      isRunning: this.intervalId !== null,
      interval: this.interval,
      lastHashes: { ...this.lastHashes },
    }
  }
}

// Create a singleton instance
const autoRefreshService = new AutoRefreshService()

export default autoRefreshService
