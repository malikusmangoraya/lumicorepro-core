import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';
import { createRef } from 'react';
import CountdownTimer from '../../components/common/CountdownTimer';
import FAQAccordion from '../../components/common/FAQAccordion';
import TestimonialGrid from '../../components/common/TestimonialGrid';
import BlogGrid from '../../components/common/BlogGrid';
import LegalDisclaimer from '../../components/common/LegalDisclaimer';
import WhatsAppFloat from '../../components/common/WhatsAppFloat';
import WorldClock from '../../components/common/WorldClock';
import SocialShare from '../../components/common/SocialShare';
import SEOMetaTags from '../../components/common/SEOMetaTags';
import Grid from '../../components/common/Grid';
import IconWrapper from '../../components/common/IconWrapper';
import MapEmbed from '../../components/common/MapEmbed';
import Analytics from '../../components/common/Analytics';

describe('CountdownTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-01T00:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the days/hours/minutes/seconds breakdown for the target', () => {
    render(<CountdownTimer target="2026-01-02T01:02:03.000Z" />);

    const timer = screen.getByRole('timer', { name: 'Offer ends in' });
    expect(within(timer).getByText('Days')).toBeInTheDocument();
    for (const value of ['01', '02', '03']) {
      expect(within(timer).getAllByText(value).length).toBeGreaterThanOrEqual(1);
    }
    expect(screen.getByText('Offer ends in')).toBeInTheDocument();
  });

  it('ticks down and calls onComplete once the deadline passes', () => {
    const onComplete = vi.fn();
    render(
      <CountdownTimer target="2025-12-31T23:59:59.000Z" onComplete={onComplete} title={null} />
    );

    vi.advanceTimersByTime(1000);

    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it('supports the solid variant and custom labels', () => {
    const { container } = render(
      <CountdownTimer
        target="2026-01-01T00:00:10.000Z"
        variant="solid"
        labels={{ days: 'D', hours: 'H', minutes: 'M', seconds: 'S' }}
        title={null}
      />
    );

    expect(container.querySelector('.bg-primary')).not.toBeNull();
    expect(screen.getByText('D')).toBeInTheDocument();
  });
});

describe('FAQAccordion', () => {
  it('opens the first item by default and toggles answers', () => {
    render(<FAQAccordion />);

    expect(
      screen.getByRole('heading', { name: 'Frequently Asked Questions' })
    ).toBeInTheDocument();
    const first = screen.getByRole('button', {
      name: /What is included with this template/,
    });
    expect(first).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/full production source code/)).toBeInTheDocument();

    const second = screen.getByRole('button', {
      name: /Can I use this for commercial client projects/,
    });
    fireEvent.click(second);

    expect(second).toHaveAttribute('aria-expanded', 'true');
    expect(first).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText(/unlimited commercial client websites/)).toBeInTheDocument();
    expect(screen.queryByText(/full production source code/)).toBeNull();
  });

  it('closes an open item and accepts custom content', () => {
    render(
      <FAQAccordion
        title="Custom FAQ"
        subtitle="Answers"
        items={[{ q: 'Only question?', a: 'Only answer.' }]}
      />
    );

    const question = screen.getByRole('button', { name: 'Only question?' });
    expect(question).toHaveAttribute('aria-expanded', 'true');
    fireEvent.click(question);
    expect(question).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Only answer.')).toBeNull();
    expect(screen.getByText('Custom FAQ')).toBeInTheDocument();
  });
});

describe('TestimonialGrid', () => {
  it('renders ratings, quotes and author details', () => {
    render(<TestimonialGrid />);

    expect(
      screen.getByRole('heading', { name: 'Trusted by 10,000+ Teams Worldwide' })
    ).toBeInTheDocument();
    expect(screen.getByText('Sarah Jenkins')).toBeInTheDocument();
    expect(screen.getByText('Principal Engineer at DevVenture')).toBeInTheDocument();
    expect(screen.getByText(/saved us at least 6 weeks/)).toBeInTheDocument();
    expect(screen.getAllByRole('img')).toHaveLength(3);
  });

  it('renders a custom testimonial set', () => {
    render(
      <TestimonialGrid
        title="Custom wall"
        subtitle=""
        testimonials={[
          {
            name: 'Ada',
            role: 'Engineer',
            avatar: '/ada.jpg',
            rating: 4,
            content: 'Excellent product',
          },
        ]}
      />
    );

    expect(screen.getByRole('heading', { name: 'Custom wall' })).toBeInTheDocument();
    expect(screen.getByText('Ada')).toBeInTheDocument();
    expect(screen.getByText(/Excellent product/)).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Ada' })).toHaveAttribute('src', '/ada.jpg');
  });
});

describe('BlogGrid', () => {
  const posts = [
    {
      id: 1,
      title: 'First post',
      excerpt: 'First excerpt',
      image: '/first.jpg',
      date: '2026-01-01',
      tag: 'Engineering',
      readTime: '3 min',
    },
    {
      id: 2,
      title: 'Second post',
      excerpt: 'Second excerpt',
      date: '2026-02-01',
    },
  ];

  it('renders each post with metadata and a read action', () => {
    render(<BlogGrid posts={posts} title="Blog title" subtitle="Blog subtitle" />);

    expect(screen.getByRole('heading', { name: 'Blog title' })).toBeInTheDocument();
    expect(screen.getByText('First post')).toBeInTheDocument();
    expect(screen.getByText('Engineering')).toBeInTheDocument();
    expect(screen.getByText('3 min read')).toBeInTheDocument();
    expect(screen.getByText('2026-01-01')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^Read:/ })).toHaveLength(2);
  });

  it('reports the clicked post to onPostClick', () => {
    const onPostClick = vi.fn();
    render(<BlogGrid posts={posts} onPostClick={onPostClick} />);

    fireEvent.click(screen.getByRole('button', { name: 'Read: Second post' }));

    expect(onPostClick).toHaveBeenCalledWith(posts[1]);
  });
});

describe('LegalDisclaimer', () => {
  it('renders the default disclaimer as a labelled region', () => {
    render(<LegalDisclaimer />);

    expect(screen.getByRole('region', { name: 'Legal disclaimer' })).toBeInTheDocument();
    expect(screen.getByText(/without warranties of any kind/)).toBeInTheDocument();
  });

  it('supports custom copy and hiding the icon', () => {
    const { container } = render(
      <LegalDisclaimer title="Terms" body="Custom legal copy" showIcon={false} />
    );

    expect(screen.getByText('Custom legal copy')).toBeInTheDocument();
    expect(container.querySelector('.lucide-scroll-text')).toBeNull();
  });
});

describe('WhatsAppFloat', () => {
  it('renders nothing without a phone number', () => {
    const { container } = render(<WhatsAppFloat />);
    expect(container.firstElementChild).toBeNull();
  });

  it('builds a sanitised wa.me link with the encoded message', () => {
    render(
      <WhatsAppFloat
        phoneNumber="+1 (555) 123-4567"
        message="Hi there & welcome"
        position="left"
        label="Chat now"
      />
    );

    const link = screen.getByRole('link', { name: 'Chat now' });
    expect(link).toHaveAttribute(
      'href',
      'https://wa.me/15551234567?text=Hi%20there%20%26%20welcome'
    );
    expect(link).toHaveAttribute('target', '_blank');
    expect(link.className).toContain('left-5');
  });
});

describe('WorldClock', () => {
  it('renders a row per timezone with formatted times', () => {
    const { container } = render(<WorldClock />);

    expect(screen.getByRole('heading', { name: 'World clock' })).toBeInTheDocument();
    for (const city of ['New York', 'London', 'Dubai', 'Singapore']) {
      expect(screen.getByText(city)).toBeInTheDocument();
    }
    expect(container.querySelectorAll('time')).toHaveLength(4);
  });

  it('accepts custom zones and a title', () => {
    render(<WorldClock title="Offices" zones={[{ city: 'Tokyo', zone: 'Asia/Tokyo' }]} />);

    expect(screen.getByRole('complementary', { name: 'Offices' })).toBeInTheDocument();
    expect(screen.getByText('Tokyo')).toBeInTheDocument();
    expect(screen.getAllByRole('time').length).toBe(1);
  });
});

describe('SocialShare', () => {
  it('renders the default networks and opens the share URL', () => {
    const open = vi.spyOn(window, 'open').mockImplementation(() => null);
    const onShared = vi.fn();
    render(<SocialShare url="https://example.com/post" title="A post" onShared={onShared} />);

    expect(screen.getByRole('group', { name: 'Share this page' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Share on LinkedIn' }));

    expect(onShared).toHaveBeenCalledWith('linkedin');
    expect(open).toHaveBeenCalledWith(
      'https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fexample.com%2Fpost',
      '_blank',
      'noopener,noreferrer,width=600,height=500'
    );
    open.mockRestore();
  });

  it('copies the link and confirms it to the user', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    });

    render(<SocialShare url="https://example.com/x" networks={['copy']} />);
    fireEvent.click(screen.getByRole('button', { name: 'Copy link' }));

    expect(await screen.findByRole('button', { name: 'Link copied' })).toBeInTheDocument();
    expect(writeText).toHaveBeenCalledWith('https://example.com/x');
  });

  it('renders the labelled button variant', () => {
    render(<SocialShare networks={['twitter']} variant="button" title="Hello" />);

    expect(screen.getByText('Share')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Share on X' })).toBeInTheDocument();
  });
});

describe('SEOMetaTags', () => {
  it('writes document meta tags, canonical URL and JSON-LD', () => {
    const schema = { '@type': 'Organization', name: 'Lumicore' };
    const { unmount } = render(
      <SEOMetaTags
        title="Page title"
        description="Page description"
        canonical="https://example.com/page"
        ogImage="https://example.com/og.png"
        schema={schema}
      />
    );

    expect(document.title).toBe('Page title');
    expect(document.head.querySelector('meta[name="description"]').content).toBe(
      'Page description'
    );
    expect(document.head.querySelector('meta[property="og:image"]').content).toBe(
      'https://example.com/og.png'
    );
    expect(document.head.querySelector('meta[name="twitter:card"]').content).toBe(
      'summary_large_image'
    );
    expect(document.head.querySelector('link[rel="canonical"]').href).toBe(
      'https://example.com/page'
    );
    expect(
      JSON.parse(document.head.querySelector('script[data-schema-json]').textContent)
    ).toEqual(schema);

    unmount();
  });
});

describe('Grid', () => {
  it('maps column/gap props to responsive classes', () => {
    const { container } = render(
      <Grid cols={4} gap="lg" className="custom-grid">
        <span>Cell</span>
      </Grid>
    );

    const grid = container.firstElementChild;
    expect(grid).toHaveClass('grid', 'lg:grid-cols-4', 'gap-8', 'custom-grid');
    expect(screen.getByText('Cell')).toBeInTheDocument();
  });

  it('renders the requested element and forwards refs', () => {
    const ref = createRef();
    render(
      <Grid as="section" ref={ref} cols={2} aria-label="Cards">
        <span>Item</span>
      </Grid>
    );

    expect(ref.current.tagName).toBe('SECTION');
    expect(ref.current).toHaveAttribute('aria-label', 'Cards');
    expect(ref.current.className).toContain('sm:grid-cols-2');
  });
});

describe('IconWrapper', () => {
  it('renders the icon inside an aria-hidden tonal container', () => {
    const Star = ({ className }) => <svg data-testid="icon" className={className} />;
    const { container } = render(<IconWrapper icon={Star} size="lg" variant="success" />);

    const wrapper = container.firstElementChild;
    expect(wrapper).toHaveAttribute('aria-hidden', 'true');
    expect(wrapper.className).toContain('h-16');
    expect(wrapper.className).toContain('bg-green-600/10');
    expect(screen.getByTestId('icon')).toHaveClass('h-7');
  });

  it('renders an empty container when no icon is supplied', () => {
    const { container } = render(<IconWrapper />);
    expect(container.querySelector('svg')).toBeNull();
  });
});

describe('MapEmbed', () => {
  it('renders an encoded Google Maps iframe and location badge', () => {
    render(<MapEmbed query="Karachi, Pakistan" title="Our branch" zoom={12} />);

    const iframe = screen.getByTitle('Our branch');
    expect(iframe.getAttribute('src')).toContain('q=Karachi%2C%20Pakistan');
    expect(iframe.getAttribute('src')).toContain('z=12');
    expect(iframe).toHaveAttribute('loading', 'lazy');
    expect(screen.getByText('Karachi, Pakistan')).toBeInTheDocument();
  });
});

describe('Analytics', () => {
  it('renders nothing and injects no script when analytics is disabled', () => {
    const before = document.head.querySelectorAll('script[data-analytics-managed]').length;
    const { container } = render(<Analytics />);

    expect(container).toBeEmptyDOMElement();
    expect(document.head.querySelectorAll('script[data-analytics-managed]').length).toBe(before);
  });
});
