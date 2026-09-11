import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Badge, Empty } from '@/components/ui';
import { history } from './data/mockData';
import useDebounce from '@/hooks/useDebounce';

export default function GenerationHistory() {
  const [query, setQuery] = useState('');
  const q = useDebounce(query);
  const list = useMemo(
    () => history.filter((h) => h.prompt.toLowerCase().includes(q.toLowerCase())),
    [q]
  );
  return (
    <TemplateShell
      title="Generation History"
      description="Search and reuse past generations."
      category="AI"
    >
      <div className="mb-4 max-w-md">
        <Input
          leftIcon={Search}
          placeholder="Search prompts…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      {list.length === 0 ? (
        <Empty title="No results" />
      ) : (
        <div className="space-y-3">
          {list.map((h, i) => (
            <Card
              key={h.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              animate="fade-up"
              animationDelay={i * 40}
            >
              <div className="min-w-0">
                <p className="font-medium truncate">{h.prompt}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {h.date} · {h.model}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge size="sm" variant="secondary">
                  {h.status}
                </Badge>
                <Button size="sm" variant="ghost">
                  Reuse
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </TemplateShell>
  );
}
