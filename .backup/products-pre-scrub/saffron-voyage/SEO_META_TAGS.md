# SEO Meta Tags Reference — saffron-voyage

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>Saffron Voyage - Pack Light. Travel Far.</title>
<meta name="title" content="Saffron Voyage - Pack Light. Travel Far." />
<meta
  name="description"
  content="Explore curated travel packages, compare itineraries, and book securely online. Your dream trip starts here."
/>
<meta
  name="keywords"
  content="tour packages, travel booking, holidays, itinerary, adventure trips"
/>
<meta name="robots" content="index, follow" />
<meta name="language" content="English" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="canonical" href="https://www.saffron-voyage.com" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://www.saffron-voyage.com" />
<meta property="og:title" content="Saffron Voyage - Pack Light. Travel Far." />
<meta
  property="og:description"
  content="Curated packages and instant booking. Your next adventure awaits."
/>
<meta property="og:image" content="https://www.saffron-voyage.com/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://www.saffron-voyage.com" />
<meta property="twitter:title" content="Saffron Voyage - Pack Light. Travel Far." />
<meta
  property="twitter:description"
  content="Curated packages and instant booking. Your next adventure awaits."
/>
<meta property="twitter:image" content="https://www.saffron-voyage.com/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Saffron Voyage",
    "url": "https://www.saffron-voyage.com",
    "description": "Curated packages and instant booking. Your next adventure awaits.",
    "foundingDate": "2026",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Urdu"]
    },
    "sameAs": [
      "https://www.facebook.com/saffron-voyage",
      "https://www.instagram.com/saffron-voyage",
      "https://twitter.com/saffron-voyage"
    ]
  }
</script>
```

## Multilingual (hreflang) — Add if i18n enabled

```html
<link rel="alternate" hreflang="en" href="https://www.saffron-voyage.com/" />
<link rel="alternate" hreflang="ur" href="https://www.saffron-voyage.com/ur/" />
<link rel="alternate" hreflang="ar" href="https://www.saffron-voyage.com/ar/" />
<link rel="alternate" hreflang="x-default" href="https://www.saffron-voyage.com/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Saffron Voyage" />
```
