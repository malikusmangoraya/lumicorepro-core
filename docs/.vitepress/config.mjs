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
      { text: 'Deployment', link: '/deployment' },
      { text: 'GitHub', link: 'https://github.com/', target: '_self' }
    ],
    sidebar: [
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
          { text: 'Deployment Options', link: '/deployment' }
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