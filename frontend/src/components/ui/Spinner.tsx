import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export function Spinner({ className, size }: { className?: string; size?: 'sm' | 'lg' }) {
  return <Loader2 className={cn('animate-spin text-brand-400', size === 'lg' ? 'h-8 w-8' : 'h-4 w-4', className)} />;
}
