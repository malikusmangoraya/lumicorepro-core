# SEO Meta Tags Reference — meridian-capital

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>Meridian Capital - Shop Smarter, Delivered Faster</title>
<meta name="title" content="Meridian Capital - Shop Smarter, Delivered Faster" />
<meta
  name="description"
  content="Discover a premium shopping experience: secure checkout, fast delivery, smart search, and 24/7 online ordering built to scale with your brand."
/>
<meta
  name="keywords"
  content="online store, ecommerce website, secure checkout, shop online, fast delivery"
/>
<meta name="robots" content="index, follow" />
<meta name="language" content="English" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="canonical" href="https://www.meridian-capital.com" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://www.meridian-capital.com" />
<meta property="og:title" content="Meridian Capital - Shop Smarter, Delivered Faster" />
<meta
  property="og:description"
  content="A faster, smarter online store. Browse, buy, and track in minutes."
/>
<meta property="og:image" content="https://www.meridian-capital.com/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://www.meridian-capital.com" />
<meta property="twitter:title" content="Meridian Capital - Shop Smarter, Delivered Faster" />
<meta
  property="twitter:description"
  content="A faster, smarter online store. Browse, buy, and track in minutes."
/>
<meta property="twitter:image" content="https://www.meridian-capital.com/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Meridian Capital",
    "url": "https://www.meridian-capital.com",
    "description": "A faster, smarter online store. Browse, buy, and track in minutes.",
    "foundingDate": "2026",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Urdu"]
    },
    "sameAs": [
      "https://www.facebook.com/meridian-capital",
      "https://www.instagram.com/meridian-capital",
      "https://twitter.com/meridian-capital"
    ]
  }
</script>
```

## Multilingual (hreflang) — Add if i18n enabled

```html
<link rel="alternate" hreflang="en" href="https://www.meridian-capital.com/" />
<link rel="alternate" hreflang="ur" href="https://www.meridian-capital.com/ur/" />
<link rel="alternate" hreflang="ar" href="https://www.meridian-capital.com/ar/" />
<link rel="alternate" hreflang="x-default" href="https://www.meridian-capital.com/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Meridian Capital" />
```
