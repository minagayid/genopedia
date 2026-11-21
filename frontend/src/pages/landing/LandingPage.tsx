import { Link } from 'react-router-dom';
import { Dna, FileBarChart, FlaskConical, GitCompareArrows, ShieldCheck, Sparkles } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { paths } from '../../routes/paths';

const features = [
  {
    icon: FlaskConical,
    title: 'Sequence analysis',
    body: 'Upload FASTA, FASTQ, VCF, or paste raw sequence. Get GC content, quality flags, motif regions, and anomaly signals in seconds.',
  },
  {
    icon: FileBarChart,
    title: 'Reproducible reports',
    body: 'Every analysis produces a self-contained HTML report and structured JSON you can download, share, and re-run.',
  },
  {
    icon: GitCompareArrows,
    title: 'Sequence comparison',
    body: 'Compare any two stored analyses and inspect substitutions, insertions, and deletions with transparent positions.',
  },
  {
    icon: ShieldCheck,
    title: 'Private by design',
    body: 'Your sequences belong to your account. Analyses are visible only to you, and access tokens never touch browser storage.',
  },
  {
    icon: Sparkles,
    title: 'Research AI assistant',
    body: 'A Genopedia model is in training. Once it passes evaluation, the assistant will answer questions grounded in your analysis results.',
  },
];

export function LandingPage() {
  const { user } = useAuth();
  return (
    <div className="min-h-screen bg-slate-950 bg-mesh-dark text-slate-100">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <Dna className="h-7 w-7 text-brand-400" />
          <span className="text-xl font-bold text-gradient">Genopedia</span>
        </div>
        <div className="flex items-center gap-3">
          {user ? (
            <Link to={paths.dashboard}>
              <Button>Open workspace</Button>
            </Link>
          ) : (
            <>
              <Link to={paths.login} className="text-sm text-slate-300 hover:text-white">
                Sign in
              </Link>
              <Link to={paths.register}>
                <Button>Create account</Button>
              </Link>
            </>
          )}
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 pb-16 pt-16 text-center">
        <p className="mx-auto mb-4 inline-block rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1 text-xs font-medium text-brand-300">
          Research use only — not for clinical or diagnostic use
        </p>
        <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight md:text-6xl">
          Your <span className="text-gradient">sequence analysis</span> workspace
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400">
          Inspect DNA and RNA sequences, generate reproducible quality reports, and keep every experiment in one private
          account. Offline-deterministic core, cloud workspace, and an AI assistant that activates when its model is
          validated.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link to={user ? paths.dashboard : paths.register}>
            <Button size="lg">Start analyzing</Button>
          </Link>
          <Link to={paths.login}>
            <Button size="lg" variant="outline">
              Sign in
            </Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 pb-20 md:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, body }) => (
          <Card key={title} variant="glass" className="animate-fade-up">
            <Icon className="mb-3 h-6 w-6 text-brand-400" />
            <h3 className="mb-2 font-semibold">{title}</h3>
            <p className="text-sm leading-relaxed text-slate-400">{body}</p>
          </Card>
        ))}
      </section>

      <footer className="border-t border-slate-800 px-6 py-8 text-center text-xs text-slate-500">
        Genopedia is a research tool. It does not provide medical advice, diagnosis, or treatment, and it never performs
        automatic sequence edits.
      </footer>
    </div>
  );
}
