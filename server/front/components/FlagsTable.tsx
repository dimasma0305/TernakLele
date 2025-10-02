'use client';

import { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  RefreshCw, 
  Settings, 
  Copy, 
  Maximize2, 
  Minimize2 
} from 'lucide-react';
import { toast } from 'sonner';
import moment from 'moment';
import { flagsPerPage } from '@/lib/config';
import PaginationCustom from './PaginationCustom';
import AutoRefreshSettings from './AutoRefreshSettings';
import autoRefreshService from '@/lib/auto-refresh';
import { Skeleton } from '@/components/ui/skeleton';
import copy from 'copy-to-clipboard';

export default function FlagsTable() {
  const [refreshing, setRefreshing] = useState(false);
  const [showAutoRefreshSettings, setShowAutoRefreshSettings] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const {
    flags,
    totalFlags,
    selectedPage,
    fetchFlags,
    updatePage,
    initialLoading,
  } = useAppStore();
  
  const [isRefreshing, setIsRefreshing] = useState(false);

  const copyableColumns = ['sploit', 'team', 'flag', 'time', 'checksystemResponse'];

  const columns = [
    { name: 'sploit', label: 'Sploit', field: 'sploit' },
    { name: 'team', label: 'Team', field: 'team' },
    { name: 'flag', label: 'Flag', field: 'flag' },
    { name: 'time', label: 'Time', field: 'time' },
    { name: 'status', label: 'Status', field: 'status' },
    { name: 'checksystemResponse', label: 'Checksystem Response', field: 'checksystemResponse' },
  ];

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchFlags();
    } finally {
      setRefreshing(false);
    }
  };

  const renderSkeletonRows = () => {
    return Array.from({ length: flagsPerPage }, (_, index) => (
      <TableRow key={`skeleton-${index}`}>
        {columns.map((column) => (
          <TableCell key={column.name} className="text-center">
            <Skeleton className="h-4 w-full" />
          </TableCell>
        ))}
      </TableRow>
    ));
  };

  const handleCopyToClipboard = (text: string) => {
    const success = copy(text);
    if (success) {
      toast.success('Copied to clipboard');
    } else {
      toast.error('Failed to copy to clipboard');
    }
  };

  const formatTime = (timestamp: number) => {
    return moment.unix(timestamp).format('YYYY-MM-DD HH:mm');
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'queued':
        return 'secondary';
      case 'skipped':
        return 'outline';
      case 'accepted':
        return 'default';
      case 'rejected':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusBadgeStyle = (status: string) => {
    switch (status.toLowerCase()) {
      case 'queued':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-200';
      case 'skipped':
        return 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200';
      case 'accepted':
        return 'bg-green-100 text-green-800 border-green-200 hover:bg-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200 hover:bg-red-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200';
    }
  };

  // Generate consistent colors for team names
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
      'bg-blue-100 text-blue-800 border-blue-200',
      'bg-purple-100 text-purple-800 border-purple-200',
      'bg-pink-100 text-pink-800 border-pink-200',
      'bg-indigo-100 text-indigo-800 border-indigo-200',
      'bg-cyan-100 text-cyan-800 border-cyan-200',
      'bg-emerald-100 text-emerald-800 border-emerald-200',
      'bg-orange-100 text-orange-800 border-orange-200',
      'bg-rose-100 text-rose-800 border-rose-200',
      'bg-violet-100 text-violet-800 border-violet-200',
      'bg-teal-100 text-teal-800 border-teal-200',
      'bg-amber-100 text-amber-800 border-amber-200',
      'bg-lime-100 text-lime-800 border-lime-200',
    ];
    
    return teamColors[colorIndex];
  };

  // Auto-refresh handlers
  const handleAutoRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetchFlags();
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    // Initial data load with loading state
    fetchFlags(true);
    
    // Register for auto-refresh updates
    autoRefreshService.onFlagsUpdate(handleAutoRefresh);
    
    // Start auto-refresh service if not already running
    if (!autoRefreshService.getStatus().isRunning) {
      autoRefreshService.start();
    }

    return () => {
      // Unregister callback when component is destroyed
      autoRefreshService.off('flags', handleAutoRefresh);
    };
  }, [fetchFlags]);

  return (
    <Card className="w-full mb-0">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-semibold">
              {totalFlags} flags total
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <PaginationCustom
              currentPage={selectedPage}
              totalPages={Math.ceil(totalFlags / flagsPerPage)}
              onPageChange={updatePage}
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={refreshing || isRefreshing}
            >
              <RefreshCw className={`h-4 w-4 ${refreshing || isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowAutoRefreshSettings(true)}
            >
              <Settings className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead key={column.name} className="text-center">
                    {column.label}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody className="transition-opacity duration-300">
              {initialLoading ? (
                renderSkeletonRows()
              ) : flags.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length} className="text-center py-8">
                    <div className="flex flex-col items-center gap-2">
                      <div className="text-muted-foreground">No flags found</div>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                flags.map((flag, index) => (
                  <TableRow key={`${flag.flag}-${index}`}>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-2">
                        {copyableColumns.includes('sploit') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopyToClipboard(flag.sploit)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        )}
                        <span>{flag.sploit}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-2">
                        {copyableColumns.includes('team') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopyToClipboard(flag.team)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        )}
                        <Badge className={getTeamColor(flag.team)}>
                          {flag.team}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-2">
                        {copyableColumns.includes('flag') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopyToClipboard(flag.flag)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        )}
                        <span className="font-mono text-sm">{flag.flag}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-2">
                        {copyableColumns.includes('time') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopyToClipboard(formatTime(flag.time))}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        )}
                        <span>{formatTime(flag.time)}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge 
                        variant={getStatusBadgeVariant(flag.status)}
                        className={getStatusBadgeStyle(flag.status)}
                      >
                        {flag.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-left">
                      <div className="flex items-center gap-2">
                        {copyableColumns.includes('checksystemResponse') && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopyToClipboard(flag.checksystemResponse)}
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        )}
                        <span className="text-sm">{flag.checksystemResponse}</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>

      <AutoRefreshSettings 
        open={showAutoRefreshSettings}
        onOpenChange={setShowAutoRefreshSettings}
      />
    </Card>
  );
}
