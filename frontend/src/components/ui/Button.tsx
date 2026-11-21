import type { ButtonHTMLAttributes } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const variants: Record<Variant, string> = {
  primary: 'bg-brand-gradient text-white shadow-soft hover:shadow-glow hover:brightness-110 active:brightness-95',
  secondary: 'bg-slate-800 text-slate-100 hover:bg-slate-700 shadow-soft active:bg-slate-900',
  outline: 'border border-slate-700 bg-transparent text-slate-200 hover:border-slate-500 hover:bg-slate-800/60',
  ghost: 'text-slate-300 hover:bg-slate-800 active:bg-slate-700',
  danger: 'bg-red-600/90 text-white hover:bg-red-600 shadow-soft active:bg-red-700',
};

const sizes: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
};

export function Button({ variant = 'primary', size = 'md', loading = false, className, children, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex select-none items-center justify-center gap-2 rounded-xl font-medium transition-all duration-150',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500/50 focus-visible:ring-offset-1 focus-visible:ring-offset-slate-950',
        'disabled:pointer-events-none disabled:opacity-60',
        sizes[size],
        variants[variant],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}
