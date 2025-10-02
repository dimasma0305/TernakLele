'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store/useAppStore';
import Navigation from '@/components/Navigation';
import TeamsTable from '@/components/TeamsTable';

export default function TeamsPage() {
  const router = useRouter();
  const serverPassword = useAppStore((state) => state.serverPassword);
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const fetchTeams = useAppStore((state) => state.fetchTeams);

  useEffect(() => {
    // Wait for store to hydrate before checking authentication
    if (!hasHydrated) return;
    
    // Redirect to login if no password after hydration
    if (!serverPassword) {
      router.push('/login');
      return;
    }

    // Fetch teams on mount
    fetchTeams();
  }, [serverPassword, hasHydrated, router, fetchTeams]);

  // Show loading while store is hydrating
  if (!hasHydrated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!serverPassword) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="w-full p-4 md:p-6 lg:p-8 space-y-4 md:space-y-6">
        <Navigation />
        <TeamsTable />
      </div>
    </div>
  );
}
