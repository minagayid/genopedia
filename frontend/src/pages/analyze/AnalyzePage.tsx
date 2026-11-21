import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileUp, Type } from 'lucide-react';
import { createAnalysis } from '../../api';
import { ApiError } from '../../api/client';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { paths } from '../../routes/paths';
import { cn } from '../../lib/utils';

const FORMATS = ['auto', 'fasta', 'fastq', 'vcf', 'text'] as const;
const MOLECULES = ['DNA', 'RNA', 'PROTEIN'] as const;

export function AnalyzePage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'paste' | 'upload'>('paste');
  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<(typeof FORMATS)[number]>('auto');
  const [molecule, setMolecule] = useState<(typeof MOLECULES)[number]>('DNA');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const analysisName = name.trim() || (file ? file.name : 'Untitled analysis');
      const detail = await createAnalysis({
        name: analysisName,
        content: mode === 'paste' ? content : undefined,
        file: mode === 'upload' ? (file ?? undefined) : undefined,
        format,
        molecule,
      });
      navigate(paths.analysis(detail.id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Analysis failed. Check the input and try again.');
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-2xl font-bold">New analysis</h1>
      <p className="mb-6 text-sm text-slate-400">
        Deterministic, offline-grade analysis: quality control, GC content, motif regions, and anomaly signals. Research
        use only.
      </p>

      <Card variant="glass">
        <div className="mb-5 flex gap-2 rounded-xl border border-slate-800 bg-slate-900/60 p-1">
          {(
            [
              { key: 'paste', label: 'Paste sequence', icon: Type },
              { key: 'upload', label: 'Upload file', icon: FileUp },
            ] as const
          ).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              type="button"
              onClick={() => setMode(key)}
              className={cn(
                'flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                mode === key ? 'bg-brand-500/15 text-brand-300' : 'text-slate-400 hover:text-slate-200',
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <Input
            label="Analysis name (optional)"
            name="name"
            placeholder="e.g. BRCA1 fragment batch 3"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          {mode === 'paste' ? (
            <div>
              <label htmlFor="content" className="mb-1.5 block text-sm font-medium text-slate-300">
                Sequence content
              </label>
              <textarea
                id="content"
                required
                rows={10}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={'>seq1\nACGTACGTACGT…'}
                className="w-full rounded-xl border border-slate-700 bg-slate-900 p-3 font-mono text-sm text-slate-100 placeholder:text-slate-600 focus:border-brand-500 focus:outline-none"
              />
              <p className="mt-1 text-xs text-slate-500">Up to 512 KB. FASTA, FASTQ, VCF, or raw sequence text.</p>
            </div>
          ) : (
            <div>
              <label htmlFor="file" className="mb-1.5 block text-sm font-medium text-slate-300">
                Sequence file
              </label>
              <input
                id="file"
                type="file"
                required
                accept=".fasta,.fa,.fna,.fastq,.fq,.vcf,.txt,.gz"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full rounded-xl border border-dashed border-slate-700 bg-slate-900 p-6 text-sm text-slate-400 file:mr-4 file:rounded-lg file:border-0 file:bg-brand-500/15 file:px-4 file:py-2 file:text-brand-300"
              />
              <p className="mt-1 text-xs text-slate-500">Up to 512 KB. .fasta, .fastq, .vcf, .vcf.gz, or .txt</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="format" className="mb-1.5 block text-sm font-medium text-slate-300">
                Format
              </label>
              <select
                id="format"
                value={format}
                onChange={(e) => setFormat(e.target.value as (typeof FORMATS)[number])}
                className="h-10 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100 focus:border-brand-500 focus:outline-none"
              >
                {FORMATS.map((f) => (
                  <option key={f} value={f}>
                    {f === 'auto' ? 'Auto-detect' : f.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="molecule" className="mb-1.5 block text-sm font-medium text-slate-300">
                Molecule
              </label>
              <select
                id="molecule"
                value={molecule}
                onChange={(e) => setMolecule(e.target.value as (typeof MOLECULES)[number])}
                className="h-10 w-full rounded-xl border border-slate-700 bg-slate-900 px-3 text-sm text-slate-100 focus:border-brand-500 focus:outline-none"
              >
                {MOLECULES.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}
          <Button type="submit" loading={loading} size="lg" className="mt-2">
            Run analysis
          </Button>
        </form>
      </Card>
    </div>
  );
}
