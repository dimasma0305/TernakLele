export interface Flag {
  sploit: string
  flag: string
  team: string
  status: string
  checksystemResponse: string
  time: number
}

export interface Team {
  name: string
  address: string
}

export interface FlagFilters {
  sploit?: string | null
  team?: string | null
  flag?: string | null
  since?: string | null
  until?: string | null
  status?: string | null
  checksystem_response?: string | null
}

export interface FilterOptions {
  sploit: string[]
  team: string[]
  status: string[]
}

export interface FilterConfig {
  filters: FilterOptions
  flag_format: string
  server_tz: string
}

export interface ChartData {
  title: string
  xAxis: string[]
  series: Array<{
    name: string
    data: number[]
    color: string
  }>
}

export interface ContentHash {
  flags_hash: string
  chart_hash: string
}
