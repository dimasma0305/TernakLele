'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Settings } from 'lucide-react';
import autoRefreshService from '@/lib/auto-refresh';

interface AutoRefreshSettingsProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function AutoRefreshSettings({ open, onOpenChange }: AutoRefreshSettingsProps) {
  const [enabled, setEnabled] = useState(false);
  const [interval, setInterval] = useState(30); // seconds

  useEffect(() => {
    // Load settings from auto-refresh service
    const status = autoRefreshService.getStatus();
    setEnabled(status.isEnabled);
    setInterval(status.interval / 1000); // Convert ms to seconds
  }, [open]);

  const handleSave = () => {
    // Update auto-refresh service settings
    autoRefreshService.setInterval(interval * 1000); // Convert seconds to ms
    
    if (enabled) {
      autoRefreshService.enable();
    } else {
      autoRefreshService.disable();
    }
    
    onOpenChange(false);
  };

  const handleCancel = () => {
    // Reset to current service values
    const status = autoRefreshService.getStatus();
    setEnabled(status.isEnabled);
    setInterval(status.interval / 1000);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Auto-Refresh Settings
          </DialogTitle>
          <DialogDescription>
            Configure automatic refresh settings for the flags table.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <Label htmlFor="auto-refresh">Enable Auto-Refresh</Label>
            <Switch
              id="auto-refresh"
              checked={enabled}
              onCheckedChange={setEnabled}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="refresh-interval">Refresh Interval (seconds)</Label>
            <Input
              id="refresh-interval"
              type="number"
              min="1"
              max="300"
              value={interval}
              onChange={(e) => setInterval(parseInt(e.target.value) || 30)}
              disabled={!enabled}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Settings
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
