import type { HTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

type Tone = 'gray' | 'green' | 'red' | 'amber' | 'brand' | 'accent';

const tones: Record<Tone, string> = {
  gray: 'bg-slate-800 text-slate-300 ring-1 ring-inset ring-slate-700',
  green: 'bg-emerald-500/10 text-emerald-300 ring-1 ring-inset ring-emerald-500/30',
  red: 'bg-red-500/10 text-red-300 ring-1 ring-inset ring-red-500/30',
  amber: 'bg-amber-500/10 text-amber-300 ring-1 ring-inset ring-amber-500/30',
  brand: 'bg-brand-500/10 text-brand-300 ring-1 ring-inset ring-brand-500/30',
  accent: 'bg-accent-500/10 text-accent-300 ring-1 ring-inset ring-accent-500/30',
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = 'gray', className, ...props }: BadgeProps) {
  return (
    <span className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', tones[tone], className)} {...props} />
  );
}
