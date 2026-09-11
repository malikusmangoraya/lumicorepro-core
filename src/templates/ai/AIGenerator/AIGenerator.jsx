import { useState } from 'react';
import { Copy, Sparkles } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button, Input, Textarea, Badge } from '@/components/ui';
import { models } from './data/mockData';

export default function AIGenerator() {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState(models[0]);
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const generate = () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setTimeout(() => {
      setResult(
        `## Result (${model})\n\n${prompt}\n\n— Generated with a clean, production-ready tone.`
      );
      setLoading(false);
    }, 800);
  };

  return (
    <TemplateShell title="AI Generator" description="Prompt in, polished output out." category="AI">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="space-y-4" animate="fade-up">
          <div className="flex flex-wrap gap-2">
            {models.map((m) => (
              <Badge
                key={m}
                variant={model === m ? 'default' : 'outline'}
                onClick={() => setModel(m)}
                className="cursor-pointer"
              >
                {m}
              </Badge>
            ))}
          </div>
          <Textarea
            label="Prompt"
            rows={6}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you need…"
          />
          <Button loading={loading} leftIcon={Sparkles} onClick={generate} className="w-full">
            Generate
          </Button>
        </Card>
        <Card animate="fade-up" animationDelay={100}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-display font-semibold">Output</h3>
            <Button
              size="sm"
              variant="ghost"
              leftIcon={Copy}
              disabled={!result}
              onClick={() => navigator.clipboard.writeText(result)}
            >
              Copy
            </Button>
          </div>
          <pre className="whitespace-pre-wrap text-sm text-muted-foreground min-h-[200px]">
            {result || 'Your generation will appear here.'}
          </pre>
        </Card>
      </div>
    </TemplateShell>
  );
}
