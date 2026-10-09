# SEO Meta Tags Reference — studio-lumen

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>Studio Lumen - Work That Speaks For Itself</title>
<meta name="title" content="Studio Lumen - Work That Speaks For Itself" />
<meta
  name="description"
  content="A professional portfolio with case studies, client results, and work that converts visitors into enquiries."
/>
<meta
  name="keywords"
  content="portfolio, case studies, freelance designer, hire designer, creative work"
/>
<meta name="robots" content="index, follow" />
<meta name="language" content="English" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="canonical" href="https://www.studio-lumen.com" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://www.studio-lumen.com" />
<meta property="og:title" content="Studio Lumen - Work That Speaks For Itself" />
<meta
  property="og:description"
  content="Case studies, client results, and work you'll want to hire."
/>
<meta property="og:image" content="https://www.studio-lumen.com/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://www.studio-lumen.com" />
<meta property="twitter:title" content="Studio Lumen - Work That Speaks For Itself" />
<meta
  property="twitter:description"
  content="Case studies, client results, and work you'll want to hire."
/>
<meta property="twitter:image" content="https://www.studio-lumen.com/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Studio Lumen",
    "url": "https://www.studio-lumen.com",
    "description": "Case studies, client results, and work you'll want to hire.",
    "foundingDate": "2026",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Urdu"]
    },
    "sameAs": [
      "https://www.facebook.com/studio-lumen",
      "https://www.instagram.com/studio-lumen",
      "https://twitter.com/studio-lumen"
    ]
  }
</script>
```

## Multilingual (hreflang) — Add if i18n enabled

```html
<link rel="alternate" hreflang="en" href="https://www.studio-lumen.com/" />
<link rel="alternate" hreflang="ur" href="https://www.studio-lumen.com/ur/" />
<link rel="alternate" hreflang="ar" href="https://www.studio-lumen.com/ar/" />
<link rel="alternate" hreflang="x-default" href="https://www.studio-lumen.com/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Studio Lumen" />
```
