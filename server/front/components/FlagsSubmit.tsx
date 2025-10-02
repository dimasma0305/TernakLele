'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Upload, Send, X } from 'lucide-react';
import { toast } from 'sonner';
import APIService from '@/lib/services/api';
import { useAppStore } from '@/lib/store/useAppStore';

export default function FlagsSubmit() {
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  const { flagFormat, setFlagFilters, fetchFlags } = useAppStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!text.trim()) {
      toast.error('Please enter text with flags');
      return;
    }

    setSubmitting(true);
    
    try {
      // Use regex to extract flags from text (like Vue version)
      const flagRegex = new RegExp(flagFormat || /FLG\{[A-Za-z0-9_]+\}/g, 'g');
      const matches = [...text.matchAll(flagRegex)];
      
      if (matches.length === 0) {
        toast.error('No valid flags found in the text');
        setSubmitting(false);
        return;
      }
      
      // Format flags like Vue version: { flag, team: "*", sploit: "Manual" }
      const formattedFlags = matches.map((match) => ({
        flag: match[0],
        team: "*",
        sploit: "Manual"
      }));
      
      await APIService.post('/post_flags', formattedFlags);
      
      toast.success(`Successfully submitted ${formattedFlags.length} flags`);
      setText(''); // Clear the form
      
      // Set filter to show manual flags and refresh
      setFlagFilters({ sploit: "Manual" });
      await fetchFlags();
      
    } catch (error: any) {
      console.error('Error submitting flags:', error);
      toast.error(error.response?.data?.error || 'Failed to submit flags');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setText(content);
    };
    reader.readAsText(file);
  };

  return (
    <Card className="mb-0">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Submit Flags
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="text">Text with flags</Label>
            <div className="relative">
              <Textarea
                id="text"
                placeholder="Enter text containing flags..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                className="font-mono text-sm pr-10"
              />
              {text && (
                <button
                  type="button"
                  onClick={() => setText('')}
                  className="absolute top-2 right-2 p-1 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            {flagFormat && (
              <p className="text-xs text-muted-foreground">
                Flag format: {flagFormat}
              </p>
            )}
          </div>

          <div className="flex gap-2">
            <Button 
              type="submit" 
              disabled={submitting || !text.trim()}
              className="flex-1"
            >
              {submitting ? 'Submitting...' : 'Submit'}
            </Button>
            
            <Button
              type="button"
              variant="outline"
              onClick={() => document.getElementById('file-upload')?.click()}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload File
            </Button>
          </div>

          <input
            id="file-upload"
            type="file"
            accept=".txt,.log"
            onChange={handleFileUpload}
            className="hidden"
          />
        </form>
      </CardContent>
    </Card>
  );
}
