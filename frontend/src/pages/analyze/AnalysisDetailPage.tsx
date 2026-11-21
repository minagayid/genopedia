import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { AlertTriangle, ArrowLeft, Download, FileText } from 'lucide-react';
import { fetchReportHtml, getAnalysis } from '../../api';
import type { AnalysisDetail } from '../../api/types';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Spinner } from '../../components/ui/Spinner';
import { formatDate } from '../../lib/utils';
import { paths } from '../../routes/paths';

const BASE_COLORS: Record<string, string> = {
  A: 'text-base-a',
  C: 'text-base-c',
  G: 'text-base-g',
  T: 'text-base-t',
  U: 'text-base-u',
};

function SequenceView({ sequence }: { sequence: string }) {
  const shown = sequence.slice(0, 2000);
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-4 leading-7">
      {shown.split('').map((base, i) => (
        <span key={i} className={`seq-base ${BASE_COLORS[base] ?? 'text-base-n'}`}>
          {base}
        </span>
      ))}
      {sequence.length > shown.length && (
        <p className="mt-2 font-sans text-xs text-slate-500">
          Showing first {shown.length.toLocaleString()} of {sequence.length.toLocaleString()} bases
        </p>
      )}
    </div>
  );
}

export function AnalysisDetailPage() {
  const { id } = useParams();
  const [item, setItem] = useState<AnalysisDetail | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getAnalysis(Number(id))
      .then(setItem)
      .catch(() => setError('Could not load this analysis.'));
  }, [id]);

  const gcAverage = useMemo(() => {
    if (!item || item.summary.records.length === 0) return null;
    const avg = item.summary.records.reduce((sum, r) => sum + r.gc_fraction, 0) / item.summary.records.length;
    return `${(avg * 100).toFixed(1)}%`;
  }, [item]);

  async function downloadReport() {
    if (!item) return;
    const html = await fetchReportHtml(item.id);
    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${item.name.replace(/[^a-z0-9-_]+/gi, '_')}-report.html`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (error) return <p className="text-red-400">{error}</p>;
  if (!item)
    return (
      <div className="flex justify-center py-20">
        <Spinner size="lg" />
      </div>
    );

  const { summary } = item;
  return (
    <div className="mx-auto max-w-5xl">
      <Link to={paths.dashboard} className="mb-4 inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200">
        <ArrowLeft className="h-4 w-4" /> All analyses
      </Link>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{item.name}</h1>
          <p className="mt-1 text-xs text-slate-500">
            {formatDate(item.created_at)} · {item.input_format.toUpperCase()} · sha256 {item.sequence_sha256.slice(0, 12)}…
          </p>
        </div>
        <Button variant="outline" onClick={downloadReport}>
          <Download className="h-4 w-4" /> Download HTML report
        </Button>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: 'Records', value: String(item.record_count) },
          { label: 'Total bases', value: item.total_bases.toLocaleString() },
          { label: 'Mean GC', value: gcAverage ?? '—' },
          { label: 'Anomalies', value: String(summary.sequence_anomalies.length) },
        ].map(({ label, value }) => (
          <Card key={label} variant="glass" className="p-4">
            <p className="text-xs text-slate-500">{label}</p>
            <p className="mt-1 text-xl font-semibold">{value}</p>
          </Card>
        ))}
      </div>

      {summary.sequence_anomalies.length > 0 && (
        <Card variant="glass" className="mb-6">
          <h2 className="mb-3 flex items-center gap-2 font-semibold">
            <AlertTriangle className="h-4 w-4 text-amber-400" /> Quality anomalies
          </h2>
          <div className="flex flex-col gap-2">
            {summary.sequence_anomalies.map((anomaly, i) => (
              <div key={i} className="rounded-xl border border-slate-800 bg-slate-900/50 p-3 text-sm">
                <div className="flex items-center gap-2">
                  <Badge tone={anomaly.severity === 'high' ? 'red' : 'amber'}>{anomaly.severity}</Badge>
                  <span className="font-medium">{anomaly.category.replace(/_/g, ' ')}</span>
                  <span className="text-xs text-slate-500">{anomaly.identifier}</span>
                </div>
                <p className="mt-1 text-slate-400">{anomaly.evidence}</p>
                <p className="mt-1 text-xs text-slate-500">Suggested: {anomaly.suggested_action}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card variant="glass" className="mb-6">
        <h2 className="mb-3 font-semibold">Records</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                <th className="pb-2 pr-4">Identifier</th>
                <th className="pb-2 pr-4">Length</th>
                <th className="pb-2 pr-4">GC</th>
                <th className="pb-2 pr-4">Ambiguous</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {summary.records.map((record) => (
                <tr key={record.identifier} className="border-b border-slate-800/60">
                  <td className="py-2 pr-4 font-mono text-xs">{record.identifier}</td>
                  <td className="py-2 pr-4">{record.length.toLocaleString()}</td>
                  <td className="py-2 pr-4">{(record.gc_fraction * 100).toFixed(1)}%</td>
                  <td className="py-2 pr-4">{record.ambiguous_count}</td>
                  <td className="py-2">
                    <Badge tone={record.status === 'pass' ? 'green' : record.status === 'warn' ? 'amber' : 'red'}>{record.status}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {summary.records.some((r) => r.warnings.length > 0) && (
          <div className="mt-3 text-xs text-slate-500">
            {summary.records.flatMap((r) => r.warnings.map((w, i) => <p key={`${r.identifier}-${i}`}>• {r.identifier}: {w}</p>))}
          </div>
        )}
      </Card>

      {summary.variants.length > 0 && (
        <Card variant="glass" className="mb-6">
          <h2 className="mb-3 font-semibold">Variants ({summary.variants.length})</h2>
          <div className="max-h-80 overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-900">
                <tr className="border-b border-slate-800 text-left text-xs text-slate-500">
                  <th className="pb-2 pr-4">Position</th>
                  <th className="pb-2 pr-4">Type</th>
                  <th className="pb-2 pr-4">Ref</th>
                  <th className="pb-2 pr-4">Obs</th>
                  <th className="pb-2">Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {summary.variants.map((variant, i) => (
                  <tr key={i} className="border-b border-slate-800/60 font-mono text-xs">
                    <td className="py-2 pr-4">{variant.chromosome}:{variant.position}</td>
                    <td className="py-2 pr-4">{variant.variant_type}</td>
                    <td className="py-2 pr-4">{variant.reference || '—'}</td>
                    <td className="py-2 pr-4">{variant.observed || '—'}</td>
                    <td className="py-2 font-sans">{variant.interpretation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {item.records.length > 0 && (
        <Card variant="glass" className="mb-6">
          <h2 className="mb-3 font-semibold">Sequence viewer</h2>
          <div className="flex flex-col gap-4">
            {item.records.map((record) => (
              <div key={record.identifier}>
                <p className="mb-2 font-mono text-xs text-slate-500">
                  {record.identifier} {record.truncated && '(truncated for storage)'}
                </p>
                <SequenceView sequence={record.sequence} />
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card variant="outline" className="mb-6 flex items-start gap-3 p-4 text-xs text-slate-500">
        <FileText className="mt-0.5 h-4 w-4 shrink-0" />
        <p>{summary.safety} Positions from VCF input stay one-based; comparison positions are zero-based. Genopedia never rewrites an observed sequence.</p>
      </Card>
    </div>
  );
}
