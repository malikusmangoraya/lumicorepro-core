import { Suspense, lazy, useState } from 'react';
import { Button, Card, CardHeader, CardTitle, CardDescription, CardContent, Badge, Input } from '../../components/shadcn';

const AntSection = lazy(() => import('./AntSection'));
const ChakraSection = lazy(() => import('./ChakraSection'));

const TABS = ['shadcn/ui', 'Ant Design', 'Chakra UI'];

function ShadcnSection() {
  return (
    <Card className="max-w-lg">
      <CardHeader>
        <CardTitle>shadcn/ui</CardTitle>
        <CardDescription>Composable primitives built on Radix + Tailwind, copied into the repo.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-3">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
        </div>
        <div className="flex gap-2">
          <Badge>Default</Badge>
          <Badge variant="secondary">Secondary</Badge>
          <Badge variant="outline">Outline</Badge>
        </div>
        <Input placeholder="you@example.com" />
      </CardContent>
    </Card>
  );
}

function SectionFallback() {
  return <div className="h-48 rounded-lg border border-border animate-pulse bg-muted" />;
}

export default function UiShowcase() {
  const [active, setActive] = useState(0);

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-3xl font-bold">UI / UX Library Showcase</h1>
      <p className="mt-2 text-muted-foreground">
        shadcn/ui, Ant Design and Chakra UI side by side — each on its own lazy chunk so the core
        bundle stays under budget.
      </p>

      <div className="mt-6 flex gap-2" role="tablist" aria-label="UI libraries">
        {TABS.map((label, i) => (
          <button
            key={label}
            type="button"
            role="tab"
            aria-selected={active === i}
            onClick={() => setActive(i)}
            className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              active === i
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground hover:bg-accent'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mt-6" role="tabpanel">
        {active === 0 && <ShadcnSection />}
        {active === 1 && (
          <Suspense fallback={<SectionFallback />}>
            <AntSection />
          </Suspense>
        )}
        {active === 2 && (
          <Suspense fallback={<SectionFallback />}>
            <ChakraSection />
          </Suspense>
        )}
      </div>
    </div>
  );
}
