import type { Metadata, Viewport } from 'next';
import { Inter, Syne } from 'next/font/google';
import './globals.css';
import { SiteHeader } from '@/components/layout/site-header';
import { SiteFooter } from '@/components/layout/site-footer';

const syne = Syne({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-syne',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000';

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'Apex Motor Collective — Curated Performance Cars',
    template: '%s · Apex Motor Collective',
  },
  description:
    'A curated inventory of performance and collector cars, with provenance verification, private viewings and door-to-door delivery.',
  applicationName: 'Apex Motor Collective',
  keywords: [
    'performance cars',
    'collector cars',
    'car dealership',
    'auto brokerage',
    'vehicle provenance',
  ],
  openGraph: {
    type: 'website',
    siteName: 'Apex Motor Collective',
    title: 'Apex Motor Collective — Curated Performance Cars',
    description:
      'Your next car, found faster. A curated inventory with provenance verification and private viewings.',
    url: siteUrl,
    images: [{ url: '/og.jpg', width: 1200, height: 630, alt: 'Apex Motor Collective' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Apex Motor Collective — Curated Performance Cars',
    description: 'Your next car, found faster.',
  },
  alternates: { canonical: '/' },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: '#070913',
  colorScheme: 'dark',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${syne.variable} ${inter.variable}`}>
      <body className="min-h-dvh bg-canvas text-body antialiased">
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <SiteHeader />
        <main id="main" className="min-h-[60dvh]">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
