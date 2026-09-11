import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Plus, Check, Users } from 'lucide-react';
import { useOrg } from '@/context/OrgContext';
import { useAppContext } from '@/context/AppContext';
import { Card, Input, Button, Alert, Badge } from '@/components/ui';

export default function OrganizationsPage() {
  const { orgs, current, loading, error, createOrg, switchOrg } = useOrg();
  const { addNotification } = useAppContext();
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setCreateError('Organization name is required');
      return;
    }
    setCreating(true);
    setCreateError('');
    try {
      await createOrg(name.trim());
      setName('');
      addNotification('Organization created', 'success');
    } catch (err) {
      setCreateError(err.response?.data?.error || err.message || 'Could not create organization');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-8 py-10 px-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-primary" /> Organizations
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Multi-tenant workspaces — switch between your teams and manage members & roles.
          </p>
        </div>
        <Link to="/settings">
          <Button variant="ghost" size="sm">Back to Settings</Button>
        </Link>
      </div>

      {error && (
        <Alert variant="danger" dismissible onDismiss={() => {}}>
          {error}
        </Alert>
      )}

      <Card animate="fade-up" title="Create organization">
        <form onSubmit={handleCreate} noValidate className="space-y-4">
          {createError && (
            <Alert variant="danger" dismissible onDismiss={() => setCreateError('')}>
              {createError}
            </Alert>
          )}
          <Input
            label="Organization name"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setCreateError('');
            }}
            placeholder="Acme Studios"
            leftIcon={<Building2 className="h-4 w-4" />}
            error={createError}
          />
          <Button type="submit" variant="primary" loading={creating} loadingText="Creating..." fullWidth>
            <Plus className="h-4 w-4 mr-1.5" /> Create Organization
          </Button>
        </form>
      </Card>

      <Card animate="fade-up" title={`Your organizations (${orgs.length})`}>
        {loading && !orgs.length ? (
          <p className="text-sm text-muted-foreground">Loading...</p>
        ) : !orgs.length ? (
          <p className="text-sm text-muted-foreground">
            No organizations yet. Create one above to get started.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {orgs.map(({ org, role, status }) => (
              <li key={org.id} className="py-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="h-9 w-9 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                    <Users className="h-4 w-4 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium truncate flex items-center gap-2">
                      {org.name}
                      {current?.id === org.id && (
                        <Badge variant="success">Active</Badge>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {role} · {status}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Link to={`/orgs/${org.id}`}>
                    <Button variant="outline" size="xs">Manage</Button>
                  </Link>
                  {current?.id !== org.id && (
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={() => switchOrg(org.id)}
                      rightIcon={<Check className="h-3.5 w-3.5" />}
                    >
                      Switch
                    </Button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}