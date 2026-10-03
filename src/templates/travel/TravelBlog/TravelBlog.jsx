import { useState } from 'react';
import { Clock, CalendarDays, Tag, ArrowRight, Heart, Bookmark } from 'lucide-react';
import TemplateShell from '../../_shared/TemplateShell';
import { Card, Badge, Button, Avatar } from '@/components/ui';
import { cn } from '@/utils';
import { img } from '@/utils/images';
import { posts, categories } from './data/mockData';

const POST_IMGS = [
  img.travel.dest1,
  img.travel.dest2,
  img.travel.dest3,
  img.travel.dest4,
  img.travel.dest5,
  img.travel.dest6,
];

export default function TravelBlog() {
  const [category, setCategory] = useState('All');
  const list = category === 'All' ? posts : posts.filter((p) => p.tag === category);

  return (
    <TemplateShell
      title="The Desi Nomad Blog"
      description="Field guides, honest budgets, and hidden corners of Pakistan."
      category="Travel"
      actions={
        <Button size="sm">
          <Heart className="h-4 w-4 mr-1" />
          Follow Us
        </Button>
      }
    >
      {/* Featured post */}
      {list.length > 0 && (
        <Card animate="fade-up" className="overflow-hidden mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2">
            <div className="relative h-56 lg:h-auto">
              <img src={POST_IMGS[0]} alt={posts[0].title} className="h-full w-full object-cover" loading="lazy" decoding="async" />
              <Badge className="absolute top-4 left-4 bg-rose-500/90">Featured</Badge>
            </div>
            <div className="p-6 lg:p-8 flex flex-col justify-center">
              <Badge variant="secondary" className="w-fit mb-3 text-[10px]">
                <Tag className="h-3 w-3 mr-1" />
                {posts[0].tag}
              </Badge>
              <h2 className="font-display text-2xl font-bold leading-snug mb-2">
                {posts[0].title}
              </h2>
              <p className="text-sm text-muted-foreground mb-5">{posts[0].excerpt}</p>
              <div className="flex items-center gap-3 mb-5">
                <Avatar className="h-9 w-9">
                  <img
                    src={img.travel.plane}
                    alt={posts[0].author}
                    className="h-full w-full object-cover"
                    loading="lazy"
                    decoding="async"
                  />
                </Avatar>
                <div>
                  <p className="text-sm font-semibold">{posts[0].author}</p>
                  <p className="text-[11px] text-muted-foreground">
                    {posts[0].date} · {posts[0].readTime} read
                  </p>
                </div>
              </div>
              <Button className="w-fit">
                Read Guide <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Categories */}
      <div className="flex flex-wrap gap-2 mb-6">
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={cn(
              'px-4 py-2 rounded-full text-sm font-medium transition-all border',
              category === c
                ? 'bg-primary text-primary-foreground border-primary'
                : 'bg-card border-border text-muted-foreground hover:border-primary/50'
            )}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {list.map((p, i) => (
          <Card
            key={p.title}
            animate="fade-up"
            animationDelay={(i * 60) % 300}
            className="overflow-hidden flex flex-col"
          >
            <div className="relative h-44">
              <img
                src={POST_IMGS[i % POST_IMGS.length]}
                alt={p.title}
                className="h-full w-full object-cover"
                loading="lazy"
                decoding="async"
              />
              <Badge variant="secondary" className="absolute top-3 left-3 text-[10px]">
                {p.tag}
              </Badge>
              <button
                className="absolute top-3 right-3 h-8 w-8 rounded-full bg-black/50 backdrop-blur flex items-center justify-center text-white transition-colors hover:bg-rose-500"
                aria-label="Save post"
              >
                <Bookmark className="h-4 w-4" />
              </button>
            </div>
            <div className="p-4 flex flex-col flex-1">
              <div className="flex items-center gap-3 text-[11px] text-muted-foreground mb-2">
                <span className="flex items-center gap-1">
                  <CalendarDays className="h-3 w-3" />
                  {p.date}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {p.readTime} read
                </span>
              </div>
              <h3 className="font-display font-semibold leading-snug mb-2">{p.title}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed flex-1">{p.excerpt}</p>
              <div className="flex items-center justify-between pt-3 mt-3 border-t border-border/60">
                <p className="text-xs font-semibold">{p.author}</p>
                <span className="inline-flex items-center gap-1 text-xs font-semibold text-primary">
                  Read <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </TemplateShell>
  );
}
