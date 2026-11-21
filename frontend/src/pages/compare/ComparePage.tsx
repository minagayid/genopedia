import { useEffect, useState, type FormEvent } from 'react';
import { GitCompareArrows } from 'lucide-react';
import { compareAnalyses, listAnalyses } from '../../api';
import type { AnalysisListItem, ComparisonResult } from '../../api/types';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { formatDate } from '../../lib/utils';

export function ComparePage() {
  const [items, setItems] = useState<AnalysisListItem[]>([]);
  const [referenceId, setReferenceId] = useState<number | ''>('');
  const [sampleId, setSampleId] = useState<number | ''>('');
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listAnalyses()
      .then((data) => setItems(data.analyses.filter((a) => a.record_count > 0)))
      .catch(() => setError('Could not load analyses.'));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (referenceId === '' || sampleId === '') return;
    setError('');
    setResult(null);
    setLoading(true);
    try {
      setResult(await compareAnalyses(Number(referenceId), Number(sampleId)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed.');
    } finally {
      setLoading(false);
    }
  }

  const selectClass =
    'h-10 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100 focus:border-brand-500 focus:outline-none';

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-2xl font-bold">Compare sequences</h1>
      <p className="mb-6 text-sm text-slate-400">
        Compare the first stored record of two analyses. Positions are zero-based; review evidence before any conclusion.
      </p>
      <Card variant="glass">
        {items.length < 2 ? (
          <p className="py-8 text-center text-sm text-slate-400">
            You need at least two analyses with sequence records to compare.
          </p>
        ) : (
          <form onSubmit={onSubmit} className="flex flex-col gap-4">
            <div>
              <label htmlFor="reference" className="mb-1.5 block text-sm font-medium text-slate-300">
                Reference
              </label>
              <select id="reference" required value={referenceId} onChange={(e) => setReferenceId(e.target.value === '' ? '' : Number(e.target.value))} className={selectClass}>
                <option value="">Choose reference…</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.total_bases.toLocaleString()} bases, {formatDate(item.created_at)})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="sample" className="mb-1.5 block text-sm font-medium text-slate-300">
                Sample
              </label>
              <select id="sample" required value={sampleId} onChange={(e) => setSampleId(e.target.value === '' ? '' : Number(e.target.value))} className={selectClass}>
                <option value="">Choose sample…</option>
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.total_bases.toLocaleString()} bases, {formatDate(item.created_at)})
                  </option>
                ))}
              </select>
            </div>
            {error && <p className="text-sm text-red-400">{error}</p>}
            <Button type="submit" loading={loading} disabled={referenceId === '' || sampleId === '' || referenceId === sampleId}>
              <GitCompareArrows className="h-4 w-4" /> Compare
            </Button>
          </form>
        )}
      </Card>

      {result && (
        <Card variant="glass" className="mt-6">
          <h2 className="mb-3 font-semibold">
            {result.variant_count} difference{result.variant_count === 1 ? '' : 's'} · reference {result.reference_length.toLocaleString()} bp / sample{' '}
            {result.sample_length.toLocaleString()} bp
          </h2>
          {result.variants.length > 0 && (
            <div className="max-h-96 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-slate-900">
                  <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                    <th className="pb-2 pr-4">Position</th>
                    <th className="pb-2 pr-4">Type</th>
                    <th className="pb-2 pr-4">Ref</th>
                    <th className="pb-2">Obs</th>
                  </tr>
                </thead>
                <tbody>
                  {result.variants.map((variant, i) => (
                    <tr key={i} className="border-b border-slate-800/60 font-mono text-xs">
                      <td className="py-2 pr-4">{variant.position}</td>
                      <td className="py-2 pr-4">{variant.variant_type}</td>
                      <td className="py-2 pr-4">{variant.reference || '—'}</td>
                      <td className="py-2">{variant.observed || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="mt-3 text-xs text-slate-500">{result.safety}</p>
        </Card>
      )}
    </div>
  );
}
