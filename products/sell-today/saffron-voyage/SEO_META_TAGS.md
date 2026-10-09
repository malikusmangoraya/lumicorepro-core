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
<link rel="canonical" href="https://malikusmangoraya.github.io/saffron-voyage" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://malikusmangoraya.github.io/saffron-voyage" />
<meta property="og:title" content="Saffron Voyage - Pack Light. Travel Far." />
<meta
  property="og:description"
  content="Curated packages and instant booking. Your next adventure awaits."
/>
<meta property="og:image" content="https://malikusmangoraya.github.io/saffron-voyage/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://malikusmangoraya.github.io/saffron-voyage" />
<meta property="twitter:title" content="Saffron Voyage - Pack Light. Travel Far." />
<meta
  property="twitter:description"
  content="Curated packages and instant booking. Your next adventure awaits."
/>
<meta property="twitter:image" content="https://malikusmangoraya.github.io/saffron-voyage/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Saffron Voyage",
    "url": "https://malikusmangoraya.github.io/saffron-voyage",
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
<link rel="alternate" hreflang="en" href="https://malikusmangoraya.github.io/saffron-voyage/" />
<link rel="alternate" hreflang="ur" href="https://malikusmangoraya.github.io/saffron-voyage/ur/" />
<link rel="alternate" hreflang="ar" href="https://malikusmangoraya.github.io/saffron-voyage/ar/" />
<link rel="alternate" hreflang="x-default" href="https://malikusmangoraya.github.io/saffron-voyage/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Saffron Voyage" />
```
