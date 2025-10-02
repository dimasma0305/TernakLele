'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Loader2, AlertCircle, BarChart3, RefreshCw } from 'lucide-react';
import APIService from '@/lib/services/api';
import autoRefreshService from '@/lib/auto-refresh';
import { Skeleton } from '@/components/ui/skeleton';

interface ChartData {
  type: string;
  title: string;
  xAxis: string[];
  series: Array<{
    name: string;
    data: number[];
    color: string;
  }>;
}

export default function ChartsComponent() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Generate consistent colors for team names (same as FlagsTable)
  const getTeamColor = (teamName: string) => {
    // Create a simple hash from the team name for consistent color assignment
    let hash = 0;
    for (let i = 0; i < teamName.length; i++) {
      const char = teamName.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    // Use absolute value and modulo to get a positive index
    const colorIndex = Math.abs(hash) % 12;
    
    const teamColors = [
      '#3B82F6', // blue-500
      '#8B5CF6', // violet-500
      '#EC4899', // pink-500
      '#6366F1', // indigo-500
      '#06B6D4', // cyan-500
      '#10B981', // emerald-500
      '#F59E0B', // amber-500
      '#F43F5E', // rose-500
      '#8B5CF6', // violet-500
      '#14B8A6', // teal-500
      '#F59E0B', // amber-500
      '#84CC16', // lime-500
    ];
    
    return teamColors[colorIndex];
  };

  // Get flag status colors (same as FlagsTable)
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'queued':
        return '#EAB308'; // yellow-500
      case 'skipped':
        return '#6B7280'; // gray-500
      case 'accepted':
        return '#22C55E'; // green-500
      case 'rejected':
        return '#EF4444'; // red-500
      default:
        return '#6B7280'; // gray-500
    }
  };

  const loadChartData = async (isInitial = false) => {
    // Only show skeleton loading for initial load when no data exists
    const shouldShowSkeleton = isInitial && !chartData;
    const isBackgroundRefresh = !isInitial && chartData;
    
    if (shouldShowSkeleton) {
      setLoading(true);
    } else if (isBackgroundRefresh) {
      // For background refresh when data exists, just set refreshing state
      setIsRefreshing(true);
    }
    setError(null);

    try {
      const response = await APIService.get('/chart-data');
      
      // Check if the response has valid chart data
      const data = response.data;
      const hasValidData = data && 
        data.xAxis && 
        Array.isArray(data.xAxis) && 
        data.xAxis.length > 0 &&
        data.series && 
        Array.isArray(data.series) && 
        data.series.length > 0;
      
      // Only update state once we have complete new data - atomic update
      setChartData(hasValidData ? data : null);
      // Clear any previous errors on successful fetch
      setError(null);
      // Always ensure loading is false after successful fetch
      setLoading(false);
    } catch (err: any) {
      console.error('Error loading chart data:', err);
      setError(err.response?.data?.error || 'Failed to load chart data');
      setChartData(null);
      setLoading(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Auto-refresh handler - explicitly not initial load
  const handleAutoRefresh = async () => {
    await loadChartData(false);
  };

  useEffect(() => {
    // Initial data load with loading state
    loadChartData(true);
    
    // Register for auto-refresh updates
    autoRefreshService.onChartUpdate(handleAutoRefresh);
    
    // Start auto-refresh service if not already running
    if (!autoRefreshService.getStatus().isRunning) {
      autoRefreshService.start();
    }

    return () => {
      // Unregister callback when component is destroyed
      autoRefreshService.off('chart', handleAutoRefresh);
    };
  }, []);

  // Custom Legend Component
  const CustomLegend = ({ payload }: any) => {
    if (!payload) return null;
    
    return (
      <div className="flex flex-wrap justify-center gap-4 mt-4">
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm font-medium" style={{ color: entry.color }}>
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  const renderChart = () => {
    if (!chartData) return null;

    const data = chartData.xAxis.map((x, index) => {
      const item: any = { name: x };
      chartData.series.forEach(series => {
        item[series.name] = series.data[index];
      });
      return item;
    });

    return (
      <div>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="name" 
              angle={chartData.xAxis.length > 5 ? -45 : 0}
              textAnchor={chartData.xAxis.length > 5 ? 'end' : 'middle'}
              height={chartData.xAxis.length > 5 ? 80 : 60}
            />
            <YAxis />
            <Tooltip />
            {chartData.series.map((series, index) => (
              <Bar 
                key={index}
                dataKey={series.name} 
                fill={getStatusColor(series.name)}
                stackId="total"
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
        <CustomLegend payload={chartData.series.map(series => ({ value: series.name, color: getStatusColor(series.name) }))} />
      </div>
    );
  };

  return (
    <Card className="w-full mb-0">
      <CardHeader>
        <CardTitle className="text-xl font-semibold flex items-center gap-2">
          Analytics
          {isRefreshing && (
            <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </CardTitle>
        {/* Status Legend - Show statuses in chart data */}
      </CardHeader>
      <CardContent>
        {(() => {
          // Show skeleton only when loading and no data exists
          if (loading && !chartData) {
            return (
              <div className="w-full">
                <Skeleton className="h-[400px] w-full mb-4" />
                <div className="flex justify-center">
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
            );
          }

          // Show error state
          if (error) {
            return (
              <div className="flex flex-col items-center justify-center py-12">
                <AlertCircle className="h-12 w-12 text-destructive" />
                <p className="mt-4 text-destructive">{error}</p>
                <Button onClick={() => loadChartData(true)} className="mt-4">
                  Retry
                </Button>
              </div>
            );
          }

          // Show no data state (when we have no chartData but no error either)
          if (!chartData && !error) {
            return (
              <div className="flex flex-col items-center justify-center py-12">
                <BarChart3 className="h-12 w-12 text-muted-foreground" />
                <p className="mt-4 text-muted-foreground">No data available</p>
              </div>
            );
          }

          // Show chart with optional refresh overlay
          return (
            <div className="w-full transition-opacity duration-300 relative">
              {renderChart()}
              {isRefreshing && (
                <div className="absolute inset-0 bg-background/20 backdrop-blur-[1px] flex items-center justify-center pointer-events-none">
                  <div className="bg-background/80 rounded-full p-2 shadow-sm">
                    <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
                  </div>
                </div>
              )}
            </div>
          );
        })()}
      </CardContent>
    </Card>
  );
}
