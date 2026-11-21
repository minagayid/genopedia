import type { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'outline';
}

const variants = {
  default: 'rounded-2xl border border-slate-800 bg-slate-900 shadow-card',
  glass: 'glass-card',
  outline: 'rounded-2xl border border-slate-800 bg-transparent',
};

export function Card({ variant = 'default', className, ...props }: CardProps) {
  return <div className={cn(variants[variant], 'p-6', className)} {...props} />;
}
