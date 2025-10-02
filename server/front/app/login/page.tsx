'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store/useAppStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Lock } from 'lucide-react';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const router = useRouter();
  const setServerPassword = useAppStore((state) => state.setServerPassword);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerPassword(password);
    router.push('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 dark:from-gray-800 dark:to-gray-900">
      <div className="w-full max-w-md p-4">
        <Card className="w-full max-w-md mx-auto shadow-2xl backdrop-blur-sm bg-white/95 dark:bg-gray-800/95">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">Welcome to Ternak Lele</CardTitle>
            <p className="text-sm text-muted-foreground">Please enter your password to continue</p>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
                <Button type="submit" className="w-full">
                  Login
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
