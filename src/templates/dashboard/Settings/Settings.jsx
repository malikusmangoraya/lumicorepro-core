import { useState } from 'react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Switch, Divider } from '@/components/ui';
import { sections } from './data/mockData';

export default function Settings() {
  const [tab, setTab] = useState('general');
  const [emailAlerts, setEmailAlerts] = useState(true);
  return (
    <TemplateShell
      title="Settings"
      description="General, security, and notifications."
      category="Dashboard"
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card padding="sm" className="h-fit">
          <nav className="flex lg:flex-col gap-1">
            {sections.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setTab(s.id)}
                className={`rounded-lg px-3 py-2 text-sm text-left transition-colors ${
                  tab === s.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                {s.label}
              </button>
            ))}
          </nav>
        </Card>
        <Card className="lg:col-span-3 animate-fade-in" key={tab}>
          {tab === 'general' && (
            <div className="space-y-4 max-w-lg">
              <Input label="Workspace name" defaultValue="My Workspace" />
              <Input label="Support email" type="email" defaultValue="hello@company.com" />
              <Button>Save changes</Button>
            </div>
          )}
          {tab === 'security' && (
            <div className="space-y-4 max-w-lg">
              <Input label="Current password" type="password" />
              <Input label="New password" type="password" />
              <Button variant="secondary">Update password</Button>
            </div>
          )}
          {tab === 'notifications' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Email alerts</p>
                  <p className="text-sm text-muted-foreground">Product and billing updates</p>
                </div>
                <Switch checked={emailAlerts} onChange={(e) => setEmailAlerts(e.target.checked)} />
              </div>
              <Divider />
              <Button size="sm">Save preferences</Button>
            </div>
          )}
          {tab === 'danger' && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Permanently delete this workspace and all data.
              </p>
              <Button variant="danger">Delete workspace</Button>
            </div>
          )}
        </Card>
      </div>
    </TemplateShell>
  );
}
