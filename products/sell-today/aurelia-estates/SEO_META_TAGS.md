# SEO Meta Tags Reference — aurelia-estates

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>Aurelia Estates - Your Property, Perfectly Presented</title>
<meta name="title" content="Aurelia Estates - Your Property, Perfectly Presented" />
<meta
  name="description"
  content="Browse premium property listings with virtual tours, verified photos, and instant lead capture. Find buyers and tenants faster with a listing site that presents like a showcase."
/>
<meta
  name="keywords"
  content="real estate, property listings, virtual tour, house for sale, rent apartment"
/>
<meta name="robots" content="index, follow" />
<meta name="language" content="English" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="canonical" href="https://malikusmangoraya.github.io/aurelia-estates" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://malikusmangoraya.github.io/aurelia-estates" />
<meta property="og:title" content="Aurelia Estates - Your Property, Perfectly Presented" />
<meta
  property="og:description"
  content="Beautifully presented listings with virtual tours and instant lead alerts."
/>
<meta property="og:image" content="https://malikusmangoraya.github.io/aurelia-estates/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://malikusmangoraya.github.io/aurelia-estates" />
<meta property="twitter:title" content="Aurelia Estates - Your Property, Perfectly Presented" />
<meta
  property="twitter:description"
  content="Beautifully presented listings with virtual tours and instant lead alerts."
/>
<meta property="twitter:image" content="https://malikusmangoraya.github.io/aurelia-estates/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Aurelia Estates",
    "url": "https://malikusmangoraya.github.io/aurelia-estates",
    "description": "Beautifully presented listings with virtual tours and instant lead alerts.",
    "foundingDate": "2026",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Urdu"]
    },
    "sameAs": [
      "https://www.facebook.com/aurelia-estates",
      "https://www.instagram.com/aurelia-estates",
      "https://twitter.com/aurelia-estates"
    ]
  }
</script>
```

## Multilingual (hreflang) — Add if i18n enabled

```html
<link rel="alternate" hreflang="en" href="https://malikusmangoraya.github.io/aurelia-estates/" />
<link rel="alternate" hreflang="ur" href="https://malikusmangoraya.github.io/aurelia-estates/ur/" />
<link rel="alternate" hreflang="ar" href="https://malikusmangoraya.github.io/aurelia-estates/ar/" />
<link rel="alternate" hreflang="x-default" href="https://malikusmangoraya.github.io/aurelia-estates/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Aurelia Estates" />
```
