import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Dna } from 'lucide-react';
import { signup } from '../../api';
import { ApiError } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { PasswordInput } from '../../components/ui/PasswordInput';
import { paths } from '../../routes/paths';

export function RegisterPage() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (password.length < 12) {
      setError('Password must be at least 12 characters.');
      return;
    }
    setLoading(true);
    try {
      const data = await signup(email, password, fullName.trim() || undefined);
      setUser(data.user);
      navigate(paths.dashboard);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) setError('An account with this email already exists.');
      else setError('Could not create the account. Check your details and try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 bg-mesh-dark p-4">
      <Card variant="glass" className="w-full max-w-md animate-fade-up">
        <div className="mb-6 flex items-center gap-2">
          <Dna className="h-6 w-6 text-brand-400" />
          <span className="text-lg font-bold text-gradient">Genopedia</span>
        </div>
        <h1 className="mb-1 text-xl font-semibold">Create your account</h1>
        <p className="mb-6 text-sm text-slate-400">A private workspace for your sequence analyses.</p>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <Input label="Full name (optional)" name="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          <Input label="Email" name="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <PasswordInput label="Password (12+ characters)" name="password" required autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <Button type="submit" loading={loading} className="mt-2">
            Create account
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-slate-400">
          Already registered?{' '}
          <Link to={paths.login} className="text-brand-300 hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}
