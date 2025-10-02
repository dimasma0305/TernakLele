'use client';

import { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Filter } from 'lucide-react';
import moment from 'moment';

export default function FlagsForm() {
  const {
    sploitFilterOptions,
    teamFilterOptions,
    statusFilterOptions,
    setFlagFilters,
    fetchFlags,
    flagFilters,
  } = useAppStore();

  const [filters, setFilters] = useState({
    sploit: flagFilters?.sploit || undefined,
    team: flagFilters?.team || undefined,
    status: flagFilters?.status || undefined,
    flag: flagFilters?.flag || undefined,
    checksystem_response: flagFilters?.checksystem_response || undefined,
    since: flagFilters?.since || undefined,
    until: flagFilters?.until || undefined,
  });

  useEffect(() => {
    // Load filter options when component mounts (without showing loading since data already exists)
    fetchFlags();
  }, [fetchFlags]);

  // Sync local filters with store filters
  useEffect(() => {
    setFilters({
      sploit: flagFilters?.sploit || undefined,
      team: flagFilters?.team || undefined,
      status: flagFilters?.status || undefined,
      flag: flagFilters?.flag || undefined,
      checksystem_response: flagFilters?.checksystem_response || undefined,
      since: flagFilters?.since || undefined,
      until: flagFilters?.until || undefined,
    });
  }, [flagFilters]);


  const handleFilterChange = (key: string, value: string | undefined) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    
    // Store original values (including date strings) in global state
    // Filter out undefined/null values - only send filters that have actual values
    const apiFilters = Object.fromEntries(
      Object.entries(newFilters).filter(([k, v]) => v !== undefined && v !== null && v !== '')
    );
    
    setFlagFilters(Object.keys(apiFilters).length > 0 ? apiFilters : null);
    fetchFlags();
  };

  const handleClearFilters = () => {
    setFilters({ 
      sploit: undefined, 
      team: undefined, 
      status: undefined,
      flag: undefined,
      checksystem_response: undefined,
      since: undefined,
      until: undefined,
    });
    setFlagFilters(null);
    fetchFlags();
  };

  const handleClearFilter = (filterKey: string) => {
    const newFilters = { ...filters, [filterKey]: undefined };
    setFilters(newFilters);
    
    // Store original values (including date strings) in global state
    // Filter out undefined/null values - only send filters that have actual values
    const apiFilters = Object.fromEntries(
      Object.entries(newFilters).filter(([k, v]) => v !== undefined && v !== null && v !== '')
    );
    
    setFlagFilters(Object.keys(apiFilters).length > 0 ? apiFilters : null);
    fetchFlags();
  };

  return (
    <Card className="mb-0">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Filter Flags
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label htmlFor="sploit">Sploit</Label>
            <Select value={filters.sploit || "all"} onValueChange={(value) => handleFilterChange('sploit', value === "all" ? undefined : value)}>
              <SelectTrigger>
                <SelectValue placeholder="All Sploits" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sploits</SelectItem>
                {sploitFilterOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="team">Team</Label>
            <Select value={filters.team || "all"} onValueChange={(value) => handleFilterChange('team', value === "all" ? undefined : value)}>
              <SelectTrigger>
                <SelectValue placeholder="All Teams" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Teams</SelectItem>
                {teamFilterOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="status">Status</Label>
            <Select value={filters.status || "all"} onValueChange={(value) => handleFilterChange('status', value === "all" ? undefined : value)}>
              <SelectTrigger>
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {statusFilterOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Text Search Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="flag">Flag (contains)</Label>
            <Input
              id="flag"
              placeholder="Search in flags..."
              value={filters.flag || ''}
              onChange={(e) => handleFilterChange('flag', e.target.value || undefined)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="checksystem_response">Checksystem Response (contains)</Label>
            <Input
              id="checksystem_response"
              placeholder="Search in responses..."
              value={filters.checksystem_response || ''}
              onChange={(e) => handleFilterChange('checksystem_response', e.target.value || undefined)}
            />
          </div>
        </div>

        {/* Date Range Filters */}
        <div className="space-y-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="since">Since (YYYY-MM-DD HH:MM)</Label>
              <Input
                id="since"
                placeholder="2024-01-01 00:00"
                value={filters.since || ''}
                onChange={(e) => handleFilterChange('since', e.target.value || undefined)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="until">Until (YYYY-MM-DD HH:MM)</Label>
              <Input
                id="until"
                placeholder="2024-12-31 23:59"
                value={filters.until || ''}
                onChange={(e) => handleFilterChange('until', e.target.value || undefined)}
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Date format: YYYY-MM-DD HH:MM (e.g., 2024-01-15 14:30)
          </p>
        </div>

        <div className="flex gap-2 items-center justify-between">
          {/* Show active filters */}
          {Object.values(filters).some(filter => filter !== undefined) && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span>Active:</span>
              {filters.sploit && (
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-blue-200 transition-colors"
                      onClick={() => handleClearFilter('sploit')}>
                  Sploit: {filters.sploit} ×
                </span>
              )}
              {filters.team && (
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-green-200 transition-colors"
                      onClick={() => handleClearFilter('team')}>
                  Team: {filters.team} ×
                </span>
              )}
              {filters.status && (
                <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-purple-200 transition-colors"
                      onClick={() => handleClearFilter('status')}>
                  Status: {filters.status} ×
                </span>
              )}
              {filters.flag && (
                <span className="bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-orange-200 transition-colors"
                      onClick={() => handleClearFilter('flag')}>
                  Flag: {filters.flag} ×
                </span>
              )}
              {filters.checksystem_response && (
                <span className="bg-pink-100 text-pink-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-pink-200 transition-colors"
                      onClick={() => handleClearFilter('checksystem_response')}>
                  Response: {filters.checksystem_response} ×
                </span>
              )}
              {filters.since && (
                <span className="bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-indigo-200 transition-colors"
                      onClick={() => handleClearFilter('since')}>
                  Since: {filters.since} ×
                </span>
              )}
              {filters.until && (
                <span className="bg-teal-100 text-teal-800 px-2 py-1 rounded text-xs cursor-pointer hover:bg-teal-200 transition-colors"
                      onClick={() => handleClearFilter('until')}>
                  Until: {filters.until} ×
                </span>
              )}
            </div>
          )}
          
          <Button variant="outline" onClick={handleClearFilters}>
            Clear Filters
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
