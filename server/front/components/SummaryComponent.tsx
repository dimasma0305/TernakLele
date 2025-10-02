'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, AlertCircle, BarChart3, RefreshCw } from 'lucide-react';
import APIService from '@/lib/services/api';
import { Skeleton } from '@/components/ui/skeleton';

interface SummaryData {
  sploit_name: string;
  teams: Array<{
    team: string;
    team_status: string;
  }>;
}

export default function SummaryComponent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryData, setSummaryData] = useState<SummaryData[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadSummaryData = async (isInitial = false) => {
    // Only show loading for initial load or when no data exists
    if (isInitial || summaryData.length === 0) {
      setLoading(true);
    } else {
      // For background refresh, just set refreshing state
      setIsRefreshing(true);
    }
    setError(null);

    try {
      const { data } = await APIService.get('/summary');
      // Only update state once we have complete new data - atomic update
      setSummaryData(data);
      setLoading(false);
    } catch (err: any) {
      console.error('Error loading summary data:', err);
      setError(err.response?.data?.error || 'Failed to load summary data');
      setSummaryData([]);
      setLoading(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadSummaryData(true);
  }, []);

  const renderSummary = () => {
    if (summaryData.length === 0) return null;

    return (
      <div className="space-y-4">
        {summaryData.map((sploit, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle className="text-lg">{sploit.sploit_name}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {sploit.teams.map((team, teamIndex) => (
                  <div key={teamIndex} className="border rounded-lg p-3">
                    <div className="font-medium text-sm mb-2">{team.team}</div>
                    <div className="text-xs text-muted-foreground whitespace-pre-line">
                      {team.team_status}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Summary
          {isRefreshing && (
            <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="space-y-4">
            {Array.from({ length: 2 }, (_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-32" />
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Array.from({ length: 3 }, (_, j) => (
                      <div key={j} className="border rounded-lg p-3">
                        <Skeleton className="h-4 w-24 mb-2" />
                        <Skeleton className="h-3 w-full" />
                        <Skeleton className="h-3 w-3/4" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <p className="mt-4 text-destructive">{error}</p>
            <button 
              onClick={() => loadSummaryData(true)} 
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && summaryData.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <BarChart3 className="h-12 w-12 text-muted-foreground" />
            <p className="mt-4 text-muted-foreground">No summary data available</p>
          </div>
        )}

        {!loading && !error && summaryData.length > 0 && (
          <div className="w-full transition-opacity duration-300 relative">
            {renderSummary()}
            {isRefreshing && (
              <div className="absolute inset-0 bg-background/20 backdrop-blur-[1px] flex items-center justify-center pointer-events-none">
                <div className="bg-background/80 rounded-full p-2 shadow-sm">
                  <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
