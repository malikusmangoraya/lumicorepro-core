import TemplateShell from '../../_shared/TemplateShell';
import { Card, Button } from '@/components/ui';
import { services } from './data/mockData';

export default function ServicesPage() {
  return (
    <TemplateShell
      title="Services"
      description="Service cards with clear next steps."
      category="Business"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {services.map((s, i) => (
          <Card
            key={s.title}
            className="flex flex-col hover-lift"
            animate="fade-up"
            animationDelay={i * 60}
          >
            <h3 className="font-display text-lg font-semibold">{s.title}</h3>
            <p className="mt-2 flex-1 text-sm text-muted-foreground">{s.text}</p>
            <p className="mt-4 text-sm font-medium text-primary">{s.price}</p>
            <Button className="mt-4" variant="outline">
              Learn more
            </Button>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
