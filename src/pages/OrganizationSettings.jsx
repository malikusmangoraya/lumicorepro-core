import { useCallback, useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Building2, ArrowLeft, UserPlus, Trash2, Save } from 'lucide-react';
import { useOrg } from '@/context/OrgContext';
import { useAppContext } from '@/context/AppContext';
import orgService from '@/services/orgs';
import { Card, Input, Button, Alert, Badge, Select, Table } from '@/components/ui';

export default function OrganizationSettingsPage() {
  const { id } = useParams();
  const { current, permissions, isManager } = useOrg();
  const { user, addNotification } = useAppContext();
  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [cur, mem, rol] = await Promise.all([
        orgService.current(),
        orgService.members(id),
        orgService.roles(id),
      ]);
      setOrg(cur.data?.org || null);
      setMembers(mem.data?.members || []);
      setRoles(rol.data?.roles || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to load organization');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteEmail)) return;
    try {
      await orgService.invite(id, inviteEmail.trim(), inviteRole);
      setInviteEmail('');
      addNotification('Invitation sent', 'success');
      load();
    } catch (err) {
      addNotification(err.response?.data?.error || err.message || 'Invite failed', 'danger');
    }
  };

  const handleRoleChange = async (userId, role) => {
    try {
      await orgService.updateMember(id, userId, { role });
      addNotification('Role updated', 'success');
      load();
    } catch (err) {
      addNotification(err.response?.data?.error || err.message || 'Update failed', 'danger');
    }
  };

  const handleRemove = async (userId) => {
    try {
      await orgService.removeMember(id, userId);
      addNotification('Member removed', 'success');
      load();
    } catch (err) {
      addNotification(err.response?.data?.error || err.message || 'Remove failed', 'danger');
    }
  };

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl py-10 px-4">
        <p className="text-sm text-muted-foreground">Loading organization...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8 py-10 px-4">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/orgs" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-1">
            <ArrowLeft className="h-3.5 w-3.5" /> All organizations
          </Link>
          <h1 className="font-display text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-primary" /> {org?.name || 'Organization'}
          </h1>
        </div>
        {current?.id === Number(id) && <Badge variant="success">Active workspace</Badge>}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}
      {!isManager && (
        <Alert variant="info">
          You have view access. Ask an admin for invite/role-management permissions.
        </Alert>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card animate="fade-up" title={`Members (${members.length})`} className="md:col-span-2">
          <Table
            head={['Name', 'Email', 'Role', 'Status']}
            rows={members.map((m) => [
              m.name || '—',
              m.email || '—',
              isManager ? (
                <Select
                  key={m.id}
                  className="w-36"
                  value={m.role || 'member'}
                  onChange={(e) => handleRoleChange(m.userId, e.target.value)}
                >
                  {roles.map((r) => (
                    <option key={r.id} value={r.name}>{r.name}</option>
                  ))}
                </Select>
              ) : (
                m.role
              ),
              <Badge key={m.id} variant={m.status === 'active' ? 'success' : 'outline'}>
                {m.status}
              </Badge>,
              isManager && String(m.userId) !== String(user?.id) ? (
                <Button key={m.id} variant="ghost" size="xs" onClick={() => handleRemove(m.userId)}>
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              ) : null,
            ])}
          />
        </Card>

        {isManager && (
          <Card animate="fade-up" title="Invite member" className="md:col-span-2">
            <form onSubmit={handleInvite} className="flex flex-col sm:flex-row gap-3 sm:items-end">
              <div className="flex-1">
                <Input
                  label="Email"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="teammate@example.com"
                  leftIcon={<UserPlus className="h-4 w-4" />}
                />
              </div>
              <div className="w-full sm:w-40">
                <label className="block text-sm font-medium text-foreground mb-1.5">Role</label>
                <Select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}>
                  {roles.map((r) => (
                    <option key={r.id} value={r.name}>{r.name}</option>
                  ))}
                </Select>
              </div>
              <Button type="submit" variant="primary">
                <UserPlus className="h-4 w-4 mr-1.5" /> Invite
              </Button>
            </form>
          </Card>
        )}

        <Card animate="fade-up" title="Roles & permissions" className="md:col-span-2">
          <ul className="divide-y divide-border">
            {roles.map((r) => (
              <li key={r.id} className="py-3 grid gap-1 md:grid-cols-[140px_1fr]">
                <span className="font-medium flex items-center gap-2">
                  {r.name} {r.is_system && <Badge variant="outline">system</Badge>}
                </span>
                <span className="flex flex-wrap gap-1.5">
                  {r.permissions.map((p) => (
                    <Badge key={p} variant="outline">{p}</Badge>
                  ))}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            Permissions: {permissions.length ? permissions.join(' · ') : 'none in this workspace'}
          </p>
        </Card>
      </div>
    </div>
  );
}