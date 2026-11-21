import { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';
import { aiStatus } from '../../api';
import type { AIStatus } from '../../api/types';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Spinner } from '../../components/ui/Spinner';

export function AiPage() {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    aiStatus()
      .then(setStatus)
      .catch(() => setError('Could not reach the assistant status endpoint.'));
  }, []);

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-2xl font-bold">AI assistant</h1>
      <p className="mb-6 text-sm text-slate-400">A research assistant grounded in your analysis results.</p>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {!status && !error && (
        <div className="flex justify-center py-16">
          <Spinner size="lg" />
        </div>
      )}

      {status && (
        <Card variant="glass" className="text-center">
          <Sparkles className="mx-auto mb-4 h-10 w-10 text-accent-400" />
          <div className="mb-3 flex items-center justify-center gap-2">
            <h2 className="text-lg font-semibold">Model status</h2>
            <Badge tone={status.available ? 'green' : 'amber'}>{status.available ? 'available' : status.state}</Badge>
          </div>
          <p className="mx-auto max-w-md text-sm leading-relaxed text-slate-400">{status.message}</p>
          {!status.available && (
            <p className="mx-auto mt-4 max-w-md text-xs leading-relaxed text-slate-500">
              The assistant stays off until the Genopedia model finishes training and passes evaluation. When it turns
              on, you will be able to ask questions about any of your stored analyses here — no fabricated answers in
              the meantime.
            </p>
          )}
        </Card>
      )}
    </div>
  );
}
