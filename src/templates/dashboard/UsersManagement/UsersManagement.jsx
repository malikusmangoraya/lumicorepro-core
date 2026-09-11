import { useMemo, useState } from 'react';
import { Search, Plus } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Badge, Input, Avatar, Empty } from '@/components/ui';
import { users as seed } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';

export default function UsersManagement() {
  const [query, setQuery] = useState('');
  const [users] = useState(seed);
  const q = useDebounce(query, 200);
  const filtered = useMemo(
    () => users.filter((u) => `${u.name} ${u.email}`.toLowerCase().includes(q.toLowerCase())),
    [users, q]
  );

  return (
    <TemplateShell
      title="Users Management"
      description="Search, filter, and manage team members."
      category="Dashboard"
      actions={
        <Button size="sm" leftIcon={Plus}>
          Add user
        </Button>
      }
    >
      <Card padding="md">
        <div className="mb-4 max-w-sm">
          <Input
            leftIcon={Search}
            placeholder="Search users…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        {filtered.length === 0 ? (
          <Empty title="No users found" description="Try another search." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="pb-3 font-medium">User</th>
                  <th className="pb-3 font-medium">Role</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u, i) => (
                  <tr
                    key={u.id}
                    className="border-b border-border/60 animate-fade-in-up"
                    style={{ animationDelay: `${i * 40}ms` }}
                  >
                    <td className="py-3">
                      <div className="flex items-center gap-3">
                        <Avatar name={u.name} size="sm" />
                        <div>
                          <p className="font-medium">{u.name}</p>
                          <p className="text-xs text-muted-foreground">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <Badge variant="secondary" size="sm">
                        {u.role}
                      </Badge>
                    </td>
                    <td>
                      <Badge variant={u.status === 'active' ? 'success' : 'warning'} size="sm" dot>
                        {u.status}
                      </Badge>
                    </td>
                    <td className="text-right">
                      <Button variant="ghost" size="sm">
                        Edit
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </TemplateShell>
  );
}
