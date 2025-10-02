'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Home, Users, LogOut } from 'lucide-react';
import { useAppStore } from '@/lib/store/useAppStore';
import { useRouter } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const setServerPassword = useAppStore((state) => state.setServerPassword);

  const handleLogout = () => {
    setServerPassword(null);
    router.push('/login');
  };

  const navItems = [
    { href: '/', label: 'Flags', icon: Home },
    { href: '/teams', label: 'Teams', icon: Users },
  ];

  return (
    <Card className="w-full mb-0">
      <div className="flex items-center justify-between px-4 py-2">
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? 'default' : 'ghost'}
                  size="icon"
                  title={item.label}
                >
                  <Icon className="h-4 w-4" />
                </Button>
              </Link>
            );
          })}
        </nav>
        
        <Button
          variant="outline"
          size="icon"
          onClick={handleLogout}
          title="Logout"
        >
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
}
