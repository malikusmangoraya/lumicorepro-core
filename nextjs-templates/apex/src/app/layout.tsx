import type { Metadata, Viewport } from 'next';
import { Inter, Syne } from 'next/font/google';
import { site } from '@/lib/site-config';
import './globals.css';

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
  verification: { google: process.env.NEXT_PUBLIC_GSC_VERIFICATION },
  robots: { index: true, follow: true },
};

export const viewport: Viewport = {
  themeColor: '#070913',
  colorScheme: 'dark',
  width: 'device-width',
  initialScale: 1,
};

/**
 * The root layout carries only the document shell. Chrome lives in the
 * `(site)` group so that auth screens can render without a marketing header or
 * footer, which is what a sign-up form should look like.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${syne.variable} ${inter.variable}`}>
      <head>
        {/*
          Applies the saved theme and locale before the first paint. Without it a
          visitor who chose light would see a dark flash on every navigation.
          It reads two localStorage keys and writes two attributes; no data.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('apex:theme');var l=localStorage.getItem('apex:locale');var d=document.documentElement;if(t==='light'||t==='dark'){d.dataset.theme=t;d.style.colorScheme=t;}if(l){d.lang=l;d.dir=(l==='ur'||l==='ar')?'rtl':'ltr';}}catch(e){}})();`,
          }}
        />
      </head>
      <body className="min-h-dvh bg-canvas text-body antialiased">
        {children}
        <script
          type="application/ld+json"
          // Business facts come from site-config; no user input reaches this.
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'AutoDealer',
              name: site.name,
              legalName: site.legalName,
              url: site.url,
              telephone: site.phone,
              email: site.email,
              image: `${site.url}/og.jpg`,
              priceRange: '$$$',
              address: {
                '@type': 'PostalAddress',
                streetAddress: site.address.street,
                addressLocality: site.address.city,
                addressRegion: site.address.region,
                postalCode: site.address.postalCode,
                addressCountry: site.address.country,
              },
              geo: {
                '@type': 'GeoCoordinates',
                latitude: site.geo.latitude,
                longitude: site.geo.longitude,
              },
              openingHoursSpecification: [
                {
                  '@type': 'OpeningHoursSpecification',
                  dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                  opens: '09:00',
                  closes: '18:00',
                },
              ],
            }),
          }}
        />
      </body>
    </html>
  );
}
