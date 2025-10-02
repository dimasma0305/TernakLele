import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Flag } from '@/lib/models/flag';
import { Team } from '@/lib/models/team';
import APIService from '@/lib/services/api';
import { flagsPerPage } from '@/lib/config';
import moment from 'moment';

interface FilterOptions {
  sploit: string[];
  team: string[];
  status: string[];
}

interface AppState {
  // Flags state
  totalFlags: number;
  selectedPage: number;
  flags: Flag[];
  flagFilters: any;
  serverTZ: string | null;
  
  // Filter options
  sploitFilterOptions: string[];
  teamFilterOptions: string[];
  statusFilterOptions: string[];
  flagFormat: string | null;
  
  // Teams state
  teams: Team[];
  
  // Auth state
  serverPassword: string | null;
  hasHydrated: boolean;
  
  // Loading state
  loading: boolean;
  initialLoading: boolean;
  
  // Actions
  setTotalFlags: (totalFlags: number) => void;
  setFlags: (flags: Flag[]) => void;
  setFlagFilters: (flagFilters: any) => void;
  setSelectedPage: (page: number) => void;
  setServerTZ: (tz: string) => void;
  setFilterOptions: (filterOptions: FilterOptions) => void;
  setFlagFormat: (flagFormat: string) => void;
  setTeams: (teams: Team[]) => void;
  setServerPassword: (password: string | null) => void;
  setHasHydrated: (hasHydrated: boolean) => void;
  setLoading: (loading: boolean) => void;
  setInitialLoading: (initialLoading: boolean) => void;
  
  // Async actions
  fetchFlags: (isInitial?: boolean) => Promise<void>;
  updatePage: (page: number) => Promise<void>;
  fetchFilterOptions: () => Promise<void>;
  fetchTeams: () => Promise<void>;
}

// Convert date string to timestamp
const convertToTimestamp = (dateString: string): string | undefined => {
  if (!dateString || dateString.trim() === '') {
    return undefined;
  }
  
  // Parse the date string in format "YYYY-MM-DD HH:MM"
  const momentDate = moment(dateString, 'YYYY-MM-DD HH:mm', true);
  
  if (!momentDate.isValid()) {
    console.warn(`Invalid date format: ${dateString}`);
    return undefined;
  }
  
  return momentDate.unix().toString();
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      totalFlags: 0,
      selectedPage: 1,
      flags: [],
      flagFilters: null,
      serverTZ: null,
      sploitFilterOptions: [],
      teamFilterOptions: [],
      statusFilterOptions: [],
      flagFormat: null,
      teams: [],
      serverPassword: null,
      hasHydrated: false,
      loading: false,
      initialLoading: false,

      // Synchronous actions
      setTotalFlags: (totalFlags) => set({ totalFlags }),
      setFlags: (flags) => set({ flags }),
      setFlagFilters: (flagFilters) => set({ flagFilters, selectedPage: 1 }),
      setSelectedPage: (selectedPage) => set({ selectedPage }),
      setServerTZ: (serverTZ) => set({ serverTZ }),
      setFilterOptions: (filterOptions) => set({
        sploitFilterOptions: filterOptions.sploit ?? [],
        teamFilterOptions: filterOptions.team ?? [],
        statusFilterOptions: filterOptions.status ?? [],
      }),
      setFlagFormat: (flagFormat) => set({ flagFormat }),
      setTeams: (teams) => set({ teams }),
      setServerPassword: (serverPassword) => set({ serverPassword }),
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
      setLoading: (loading) => set({ loading }),
      setInitialLoading: (initialLoading) => set({ initialLoading }),

      // Async actions
      fetchFlags: async (isInitial = false) => {
        const state = get();
        
        // Only show loading for initial load or when no data exists
        if (isInitial || state.flags.length === 0) {
          set({ initialLoading: true });
        }
        
        const filters = state.flagFilters;
        let params: any = {
          page: state.selectedPage,
          page_size: flagsPerPage,
        };
        
        if (filters) {
          // Convert date fields to timestamps for API call
          const apiFilters = Object.fromEntries(
            Object.entries(filters).map(([k, v]) => {
              // Convert date fields to timestamps for API
              if (k === 'since' || k === 'until') {
                const timestamp = convertToTimestamp(v as string);
                return [k, timestamp];
              }
              return [k, v];
            }).filter(([k, v]) => v !== undefined) // Remove any undefined timestamps
          );
          params = { ...params, ...apiFilters };
        }
        
        try {
          // Filter out null/undefined values from params
          const cleanParams: Record<string, string> = Object.fromEntries(
            Object.entries(params).filter(([key, value]) => 
              value !== null && value !== undefined && value !== ''
            ).map(([key, value]) => [key, String(value)])
          );
          
          const queryString = new URLSearchParams(cleanParams).toString();
          const { data } = await APIService.get(`/filter_flags?${queryString}`);
          const flags = data.flags.map((flag: any) => new Flag(flag));
          
          // Only update state once we have complete new data - atomic update
          set({ flags, totalFlags: data.total, initialLoading: false });
        } catch (e) {
          console.error('Error fetching flags', e);
          set({ initialLoading: false });
        }
        
        await get().fetchFilterOptions();
      },

      updatePage: async (page) => {
        set({ selectedPage: page });
        await get().fetchFlags();
      },

      fetchFilterOptions: async () => {
        try {
          const { data } = await APIService.get('/filter_config');
          set({
            sploitFilterOptions: data.filters.sploit ?? [],
            teamFilterOptions: data.filters.team ?? [],
            statusFilterOptions: data.filters.status ?? [],
            flagFormat: data.flag_format,
            serverTZ: data.server_tz,
          });
        } catch (e) {
          console.error('Error fetching filter options', e);
        }
      },

      fetchTeams: async () => {
        try {
          const { data } = await APIService.get('/teams');
          const teams = data.map((team: any) => new Team(team));
          set({ teams });
        } catch (e) {
          console.error('Error fetching teams', e);
        }
      },
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({ serverPassword: state.serverPassword }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.setHasHydrated(true);
        }
      },
    }
  )
);
