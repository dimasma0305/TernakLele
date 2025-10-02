'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store/useAppStore';
import { flagsPerPage } from '@/lib/config';
import Navigation from '@/components/Navigation';
import ChartsComponent from '@/components/ChartsComponent';
import FlagsForm from '@/components/FlagsForm';
import FlagsSubmit from '@/components/FlagsSubmit';
import FlagsTable from '@/components/FlagsTable';

export default function FlagsPage() {
  const router = useRouter();
  const serverPassword = useAppStore((state) => state.serverPassword);
  const hasHydrated = useAppStore((state) => state.hasHydrated);
  const fetchFlags = useAppStore((state) => state.fetchFlags);

  useEffect(() => {
    // Wait for store to hydrate before checking authentication
    if (!hasHydrated) return;
    
    // Redirect to login if no password after hydration
    if (!serverPassword) {
      router.push('/login');
      return;
    }

    // Fetch flags on mount
    fetchFlags();
  }, [serverPassword, hasHydrated, router, fetchFlags]);

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
        {/* Charts Section */}
        <div className="w-full">
          <ChartsComponent />
        </div>

        {/* Forms Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-4 md:gap-x-6 gap-y-0">
          <div className="lg:col-span-2">
            <FlagsForm />
          </div>
          <div className="lg:col-span-1">
            <FlagsSubmit />
          </div>
        </div>

        {/* Table Section */}
        <div className="w-full">
          <FlagsTable />
        </div>
      </div>
    </div>
  );
}