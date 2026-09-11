import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Avatar, Badge } from '@/components/ui';
import { profile, activity } from './data/mockData';

export default function Profile() {
  return (
    <TemplateShell
      title="Profile"
      description="Your identity, security, and activity."
      category="Dashboard"
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="text-center" animate="scale">
          <Avatar name={profile.name} size="xl" className="mx-auto" />
          <h2 className="mt-4 font-display text-xl font-semibold">{profile.name}</h2>
          <p className="text-sm text-muted-foreground">{profile.email}</p>
          <Badge className="mt-3" variant="info">
            {profile.role}
          </Badge>
          <Button className="mt-6 w-full" variant="outline" size="sm">
            Change avatar
          </Button>
        </Card>
        <Card className="lg:col-span-2 space-y-4" animate="fade-up">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Full name" defaultValue={profile.name} />
            <Input label="Email" type="email" defaultValue={profile.email} />
            <Input label="Title" defaultValue={profile.title} />
            <Input label="Location" defaultValue={profile.location} />
          </div>
          <Button>Save profile</Button>
          <div className="pt-4 border-t border-border">
            <h3 className="font-display font-semibold mb-3">Recent activity</h3>
            <ul className="space-y-2">
              {activity.map((a) => (
                <li key={a.id} className="text-sm text-muted-foreground flex justify-between gap-4">
                  <span>{a.text}</span>
                  <span className="shrink-0">{a.time}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      </div>
    </TemplateShell>
  );
}
