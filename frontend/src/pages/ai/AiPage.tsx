import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { Sparkles } from 'lucide-react';
import { aiStatus, askAi } from '../../api';
import type { AIStatus } from '../../api/types';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Spinner } from '../../components/ui/Spinner';
import { Button } from '../../components/ui/Button';

export function AiPage() {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [consent, setConsent] = useState(false);
  const [answer, setAnswer] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    aiStatus()
      .then(setStatus)
      .catch(() => setError('Could not reach the assistant status endpoint.'));
  }, []);

  async function submitQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent || !question.trim()) return;
    setConsent(false);
    setSending(true);
    setError('');
    setAnswer('');
    try {
      const result = await askAi(question.trim());
      setAnswer(result.answer);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'The assistant could not answer your question.');
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="mb-1 text-2xl font-bold">AI assistant</h1>
      <p className="mb-6 text-sm text-slate-400">Ask research questions about sequence analysis. This form does not send saved analyses.</p>

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
      {status?.available && (
        <Card variant="glass" className="mt-4">
          <form onSubmit={submitQuestion} className="space-y-4">
            <p className="text-sm text-slate-400">Research use only. Answers can be incorrect and are not medical advice.</p>
            <label htmlFor="ai-question" className="block text-sm font-medium text-slate-200">Your question</label>
            <textarea id="ai-question" value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={4000} required rows={4} className="w-full rounded-xl border border-slate-700 bg-slate-900 p-3 text-sm text-slate-100" />
            <label className="flex items-start gap-2 text-sm text-slate-300">
              <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
              <span>I agree to send my question to the configured model service and any upstream providers it uses. Do not include private or identifiable genomic information unless you have permission to share it.</span>
            </label>
            <Button type="submit" disabled={!consent || !question.trim()} loading={sending}>Ask assistant</Button>
          </form>
          {answer && <div className="mt-5 whitespace-pre-wrap text-sm text-slate-200" aria-live="polite">{answer}</div>}
        </Card>
      )}
    </div>
  );
}
