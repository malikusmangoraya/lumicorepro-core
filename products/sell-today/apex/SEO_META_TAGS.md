# SEO Meta Tags Reference — apex

## Essential Meta Tags (add to index.html <head>)

```html
<!-- Primary Meta Tags -->
<title>Apex - Ship Faster, Scale Further</title>
<meta name="title" content="Apex - Ship Faster, Scale Further" />
<meta
  name="description"
  content="Launch a high-converting SaaS site with flexible pricing, real-time analytics, and security baked into every page."
/>
<meta
  name="keywords"
  content="saas website, software platform, pricing page, free trial, analytics"
/>
<meta name="robots" content="index, follow" />
<meta name="language" content="English" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<link rel="canonical" href="https://malikusmangoraya.github.io/apex-digital" />

<!-- Open Graph / Facebook -->
<meta property="og:type" content="website" />
<meta property="og:url" content="https://malikusmangoraya.github.io/apex-digital" />
<meta property="og:title" content="Apex - Ship Faster, Scale Further" />
<meta
  property="og:description"
  content="Pricing, onboarding, and analytics built in — launch in days."
/>
<meta property="og:image" content="https://malikusmangoraya.github.io/apex-digital/og-image.jpg" />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content="https://malikusmangoraya.github.io/apex-digital" />
<meta property="twitter:title" content="Apex - Ship Faster, Scale Further" />
<meta
  property="twitter:description"
  content="Pricing, onboarding, and analytics built in — launch in days."
/>
<meta property="twitter:image" content="https://malikusmangoraya.github.io/apex-digital/twitter-image.jpg" />

<!-- JSON-LD Structured Data -->
<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Apex",
    "url": "https://malikusmangoraya.github.io/apex-digital",
    "description": "Pricing, onboarding, and analytics built in — launch in days.",
    "foundingDate": "2026",
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "availableLanguage": ["English", "Urdu"]
    },
    "sameAs": [
      "https://www.facebook.com/apex",
      "https://www.instagram.com/apex",
      "https://twitter.com/apex"
    ]
  }
</script>
```

## Multilingual (hreflang) — Add if i18n enabled

```html
<link rel="alternate" hreflang="en" href="https://malikusmangoraya.github.io/apex-digital/" />
<link rel="alternate" hreflang="ur" href="https://malikusmangoraya.github.io/apex-digital/ur/" />
<link rel="alternate" hreflang="ar" href="https://malikusmangoraya.github.io/apex-digital/ar/" />
<link rel="alternate" hreflang="x-default" href="https://malikusmangoraya.github.io/apex-digital/" />
```

## PWA Meta Tags — Add if PWA enabled

```html
<link rel="manifest" href="/manifest.json" />
<meta name="theme-color" content="#0d9488" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="Apex" />
```
