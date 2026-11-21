import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-950 text-slate-200">
      <p className="text-6xl font-bold text-brand-400">404</p>
      <p className="text-slate-400">This page does not exist.</p>
      <Link to="/" className="text-brand-300 underline-offset-4 hover:underline">
        Back to Genopedia
      </Link>
    </div>
  );
}
