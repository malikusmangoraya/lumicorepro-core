import { Star, Check } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button } from '@/components/ui';
import { img } from '@/utils/images';

export default function IssueArchive() {
  const items = [
    { title: 'Item One', desc: 'Short description for the first item.', tag: 'Popular' },
    { title: 'Item Two', desc: 'Short description for the second item.', tag: 'New' },
    { title: 'Item Three', desc: 'Short description for the third item.', tag: null },
  ];

  return (
    <TemplateShell
      title="Newsletter Section"
      description="Past issue archive."
      category="Newsletter"
    >
      <div className="relative overflow-hidden rounded-2xl border border-border h-56 mb-6">
        <img
          src={img.business.hero}
          alt="Newsletter"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
        <div className="absolute inset-0 flex flex-col justify-end p-8">
          <Badge variant="warning" className="mb-2 w-fit">
            Newsletter
          </Badge>
          <h2 className="font-display text-3xl font-bold text-white">Newsletter — Newsletter</h2>
          <p className="mt-1 text-white/80 text-sm max-w-md">Past issue archive.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((it, i) => (
          <Card key={it.title} animate="fade-up" animationDelay={i * 60} className="hover-lift">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-display font-semibold text-sm">{it.title}</h3>
              {it.tag && (
                <Badge variant="success" size="sm">
                  {it.tag}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground mb-3">{it.desc}</p>
            <div className="flex items-center gap-1 text-xs text-muted-foreground mb-3">
              <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" /> 4.8 rating
            </div>
            <Button size="sm" variant="outline" className="w-full">
              <Check className="h-3.5 w-3.5 mr-1" />
              Learn More
            </Button>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
