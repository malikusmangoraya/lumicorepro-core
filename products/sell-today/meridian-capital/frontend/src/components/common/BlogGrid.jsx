import React from 'react';
import { ArrowUpRight, Calendar } from 'lucide-react';
import { cn, img } from '../../utils';
import LazyImage from './LazyImage';

const defaultPosts = [
  {
    id: 1,
    title: 'How we scaled to 1M users on a budget',
    excerpt: 'A case study on architecture, caching and ruthless performance budgets.',
    image: img.business,
    date: '2026-09-01',
    tag: 'Engineering',
    readTime: '6 min',
  },
  {
    id: 2,
    title: 'Design systems that ship faster',
    excerpt: 'Token-driven design that keeps every page cohesive without slowing teams down.',
    image: img.creative,
    date: '2026-08-20',
    tag: 'Design',
    readTime: '4 min',
  },
  {
    id: 3,
    title: 'The playbook for global launches',
    excerpt: 'i18n, RTL, multi-currency and localization done the right way from day one.',
    image: img.people,
    date: '2026-08-02',
    tag: 'Growth',
    readTime: '8 min',
  },
];

const BlogGrid = ({
  posts = defaultPosts,
  title = 'Latest from the blog',
  subtitle = 'Tactical guides and behind-the-scenes stories.',
  onPostClick,
  className = '',
}) => {
  return (
    <section className={cn('w-full py-16', className)}>
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl space-y-3 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground">{title}</h2>
          {subtitle && <p className="text-base text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {posts.map((post) => (
            <article
              key={post.id}
              className="group overflow-hidden rounded-2xl border bg-card text-card-foreground shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <button
                type="button"
                onClick={() => typeof onPostClick === 'function' && onPostClick(post)}
                className="block w-full text-left"
                aria-label={`Read: ${post.title}`}
              >
                <div className="relative aspect-[16/10] overflow-hidden">
                  <LazyImage
                    src={post.image || img.business}
                    alt={post.title}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  {post.tag && (
                    <span className="absolute left-3 top-3 rounded-full bg-background/90 px-2.5 py-1 text-xs font-medium text-foreground backdrop-blur">
                      {post.tag}
                    </span>
                  )}
                </div>
                <div className="space-y-3 p-5">
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                      {post.date}
                    </span>
                    {post.readTime && <span>{post.readTime} read</span>}
                  </div>
                  <h3 className="line-clamp-2 text-lg font-semibold text-foreground transition-colors group-hover:text-primary">
                    {post.title}
                  </h3>
                  <p className="line-clamp-2 text-sm text-muted-foreground">{post.excerpt}</p>
                  <span className="inline-flex items-center gap-1 text-sm font-medium text-primary">
                    Read more
                    <ArrowUpRight
                      className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                      aria-hidden="true"
                    />
                  </span>
                </div>
              </button>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
};

export default BlogGrid;
