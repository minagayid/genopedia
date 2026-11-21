import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileBarChart, FlaskConical, Trash2 } from 'lucide-react';
import { deleteAnalysis, listAnalyses } from '../../api';
import type { AnalysisListItem } from '../../api/types';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Modal } from '../../components/ui/Modal';
import { Spinner } from '../../components/ui/Spinner';
import { formatDate } from '../../lib/utils';
import { paths } from '../../routes/paths';

export function DashboardPage() {
  const [items, setItems] = useState<AnalysisListItem[] | null>(null);
  const [error, setError] = useState('');
  const [pendingDelete, setPendingDelete] = useState<AnalysisListItem | null>(null);
  const [deleting, setDeleting] = useState(false);

  async function load() {
    try {
      const data = await listAnalyses();
      setItems(data.analyses);
    } catch {
      setError('Could not load your analyses.');
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    try {
      await deleteAnalysis(pendingDelete.id);
      setItems((prev) => (prev ?? []).filter((item) => item.id !== pendingDelete.id));
      setPendingDelete(null);
    } catch {
      setError('Delete failed. Try again.');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Your analyses</h1>
          <p className="text-sm text-slate-400">{items ? `${items.length} of 100 slots used` : 'Loading…'}</p>
        </div>
        <Link to={paths.analyze}>
          <Button>
            <FlaskConical className="h-4 w-4" /> New analysis
          </Button>
        </Link>
      </div>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      {items === null ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : items.length === 0 ? (
        <Card variant="glass" className="py-16 text-center">
          <FileBarChart className="mx-auto mb-4 h-10 w-10 text-slate-600" />
          <h2 className="mb-2 text-lg font-semibold">No analyses yet</h2>
          <p className="mx-auto mb-6 max-w-sm text-sm text-slate-400">
            Upload a FASTA, FASTQ, or VCF file, or paste a raw sequence to get your first quality report.
          </p>
          <Link to={paths.analyze}>
            <Button>Run your first analysis</Button>
          </Link>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {items.map((item) => (
            <Link key={item.id} to={paths.analysis(item.id)}>
              <Card variant="glass" className="flex flex-wrap items-center justify-between gap-3 py-4 transition-colors hover:border-brand-500/40">
                <div className="min-w-0">
                  <p className="truncate font-medium">{item.name}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {formatDate(item.created_at)} · {item.record_count} record{item.record_count === 1 ? '' : 's'} ·{' '}
                    {item.total_bases.toLocaleString()} bases
                    {item.variant_count > 0 && ` · ${item.variant_count} variants`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone="brand">{item.input_format.toUpperCase()}</Badge>
                  <Badge tone="gray">{item.molecule}</Badge>
                  <button
                    aria-label={`Delete ${item.name}`}
                    className="rounded-lg p-2 text-slate-500 hover:bg-red-500/10 hover:text-red-400"
                    onClick={(e) => {
                      e.preventDefault();
                      setPendingDelete(item);
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}

      <Modal
        open={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        title="Delete analysis"
        footer={
          <>
            <Button variant="ghost" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button variant="danger" loading={deleting} onClick={confirmDelete}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-sm text-slate-300">
          Delete “{pendingDelete?.name}”? The stored sequences and report are removed permanently.
        </p>
      </Modal>
    </div>
  );
}
