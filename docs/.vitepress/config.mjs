import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'LumicorePro Documentation',
  description:
    'Official documentation for LumicorePro — an AI-powered web project generator with a premium React + Express e-commerce storefront.',
  lang: 'en-US',
  cleanUrls: true,
  lastUpdated: true,
  themeConfig: {
    logo: '/lumicorepro-logo.svg',
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Getting Started', link: '/getting-started' },
      { text: 'API Reference', link: '/api-reference' },
      { text: 'Deployment', link: '/DEPLOYMENT' },
      { text: 'GitHub', link: 'https://github.com/', target: '_self' }
    ],
    sidebar: [
      {
        text: 'Build',
        items: [
          { text: 'AI Website Generation Standard', link: '/AI_WEBSITE_GENERATION_STANDARD' },
          { text: 'Website Build Playbook', link: '/WEBSITE_BUILD_PLAYBOOK' }
        ]
      },
      {
        text: 'Getting Started',
        items: [
          { text: 'Introduction', link: '/' },
          { text: 'Setup Guide', link: '/getting-started' }
        ]
      },
      {
        text: 'API Reference',
        items: [
          { text: 'Endpoints', link: '/api-reference' }
        ]
      },
      {
        text: 'Deployment Guide',
        items: [
          { text: 'Deployment Options', link: '/DEPLOYMENT' }
        ]
      },
      {
        text: 'Product Guides',
        items: [
          { text: 'Product Manual', link: '/PRODUCT_MANUAL' },
          { text: 'Selling on Lemon Squeezy', link: '/SELLING_GUIDE' }
        ]
      },
      {
        text: 'Design',
        items: [
          { text: 'Unique Project Playbook', link: '/UNIQUE_PROJECT_PLAYBOOK' }
        ]
      },
      {
        text: 'Architecture',
        items: [
          { text: 'Open-Source Alternatives', link: '/OPENSOURCE_ALTERNATIVES' },
          { text: 'Generator Comparison', link: '/WEBSITE_GENERATOR_COMPARISON' }
        ]
      }
    ],
    socialLinks: [{ icon: 'github', link: 'https://github.com/' }],
    footer: {
      message: 'LumicorePro Core — AI web project generation studio.',
      copyright: 'Copyright © 2026 LumicorePro'
    },
    outline: {
      level: [2, 3],
      label: 'On this page'
    },
    search: {
      provider: 'local'
    }
  }
})