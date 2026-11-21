import { useAuth } from '../../auth/AuthContext';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { formatDate } from '../../lib/utils';

export function SettingsPage() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold">Settings</h1>
      <Card variant="glass">
        <h2 className="mb-4 font-semibold">Account</h2>
        <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-3 text-sm">
          <dt className="text-slate-500">Email</dt>
          <dd>{user.email}</dd>
          <dt className="text-slate-500">Name</dt>
          <dd>{user.full_name ?? '—'}</dd>
          <dt className="text-slate-500">Email verified</dt>
          <dd>
            <Badge tone={user.email_verified ? 'green' : 'amber'}>{user.email_verified ? 'verified' : 'not yet'}</Badge>
          </dd>
          <dt className="text-slate-500">Member since</dt>
          <dd>{formatDate(user.created_at)}</dd>
        </dl>
      </Card>
      <Card variant="outline" className="mt-4 p-4 text-xs leading-relaxed text-slate-500">
        Sessions use short-lived access tokens held only in memory, plus a rotating HttpOnly refresh cookie. Signing
        out revokes the current refresh session. Email verification and password reset delivery are being connected
        next.
      </Card>
    </div>
  );
}
