# SEO Meta Tags Reference — nuage-events

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>Nuage Events - Pack Light. Travel Far.</title>
<meta name="title" content="Nuage Events - Pack Light. Travel Far." />
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
<link rel="canonical" href="https://malikusmangoraya.github.io/nuage-events" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://malikusmangoraya.github.io/nuage-events" />
<meta property="og:title" content="Nuage Events - Pack Light. Travel Far." />
<meta
  property="og:description"
  content="Curated packages and instant booking. Your next adventure awaits."
/>
<meta property="og:image" content="https://malikusmangoraya.github.io/nuage-events/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://malikusmangoraya.github.io/nuage-events" />
<meta property="twitter:title" content="Nuage Events - Pack Light. Travel Far." />
<meta
  property="twitter:description"
  content="Curated packages and instant booking. Your next adventure awaits."
/>
<meta property="twitter:image" content="https://malikusmangoraya.github.io/nuage-events/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Nuage Events",
    "url": "https://malikusmangoraya.github.io/nuage-events",
    "description": "Curated packages and instant booking. Your next adventure awaits.",
    "foundingDate": "2026",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Urdu"]
    },
    "sameAs": [
      "https://www.facebook.com/nuage-events",
      "https://www.instagram.com/nuage-events",
      "https://twitter.com/nuage-events"
    ]
  }
</script>
```

## Multilingual (hreflang) — Add if i18n enabled

```html
<link rel="alternate" hreflang="en" href="https://malikusmangoraya.github.io/nuage-events/" />
<link rel="alternate" hreflang="ur" href="https://malikusmangoraya.github.io/nuage-events/ur/" />
<link rel="alternate" hreflang="ar" href="https://malikusmangoraya.github.io/nuage-events/ar/" />
<link rel="alternate" hreflang="x-default" href="https://malikusmangoraya.github.io/nuage-events/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Nuage Events" />
```
