# 🚀 LumiCorePro - Complete API Setup Guide

This guide will walk you through setting up all API keys step-by-step. Your keys are stored securely in your browser's localStorage.

---

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Getting API Keys](#getting-api-keys)
3. [Configuration](#configuration)
4. [Testing Your Setup](#testing-your-setup)
5. [Troubleshooting](#troubleshooting)
6. [Security Best Practices](#security-best-practices)

---

## Quick Start

### Option 1: Using the Web Interface (Recommended)

1. Navigate to `/api-settings` in the app
2. Enter your API keys in the provided forms
3. Click "Test Connection" for each provider
4. Save the configuration

### Option 2: Using Environment Variables

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```env
GEMINI_API_KEY=your_gemini_key_here
DEEPSEEK_API_KEY=your_deepseek_key_here
OPENROUTER_API_KEY=your_openrouter_key_here
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key_here
```

3. Restart your application

---

## Getting API Keys

### 🔑 Google Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key
5. Paste it in the Gemini section in `/api-settings`

### 🔑 DeepSeek API Key

1. Visit [DeepSeek Platform](https://platform.deepseek.com/api_keys)
2. Create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste it in the DeepSeek section

### 🔑 OpenRouter API Key

1. Visit [OpenRouter](https://openrouter.ai/keys)
2. Sign up or log in
3. Create a new key
4. Copy and paste it in the OpenRouter section

### 💳 Stripe API Keys

1. Visit [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Sign in or create account
3. You'll find two types of keys:
   - **Publishable Key** (starts with `pk_test_` or `pk_live_`)
   - **Secret Key** (starts with `sk_test_` or `sk_live_`)
4. Paste both keys in the Stripe section

---

## Configuration

### API Configuration Service

All API keys are managed by `src/services/apiConfig.js`:

```javascript
import apiConfig from './services/apiConfig';

// Get current configuration
const config = apiConfig.getApiConfig();

// Update a specific provider
apiConfig.updateProviderConfig('gemini', { apiKey: 'your-key-here' });

// Test API connection
const result = await apiConfig.testGeminiApi('your-key-here');

// Export configuration for backup
const json = apiConfig.exportApiConfig();

// Import configuration from backup
apiConfig.importApiConfig(jsonString);
```

### Storage

- API keys are stored in `localStorage` under key `lumicorepro_api_config`
- Keys are never sent to any third-party servers except the API providers themselves
- Configuration can be exported/imported for backup purposes

---

## Testing Your Setup

### Using the Web Interface

1. Go to `/api-settings`
2. Click "Test Connection" for each provider
3. Green checkmark (✅) = Working
4. Red X (❌) = Issue detected

### Manual Testing

```bash
# Test Gemini API
curl "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY"

# Test DeepSeek API
curl "https://api.deepseek.com/v1/models" \
  -H "Authorization: Bearer YOUR_KEY"

# Test OpenRouter API
curl "https://openrouter.ai/api/v1/auth/key" \
  -H "Authorization: Bearer YOUR_KEY"
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS Error | Ensure you're running the app on `localhost:5173` (dev) or your configured domain |
| Invalid Key | Double-check you copied the entire key without spaces |
| Connection Timeout | Check your internet connection; some regions may need a proxy |
| Stripe Backend Required | Full Stripe testing requires the backend server to be running |
| Rate Limited | Wait a few minutes and retry; some providers have request limits |

### Debug Mode

Enable debug logging in `.env`:
```env
VITE_LOG_LEVEL=debug
```

### Clear Configuration

To reset all API keys:
```javascript
// In browser console
localStorage.removeItem('lumicorepro_api_config');
// Then refresh the page
```

Or use the "Reset All" button in `/api-settings`.

---

## Security Best Practices

### 🔒 DO:
- Use test API keys during development
- Keep your keys private and secure
- Export configuration before making changes
- Use environment variables for production deployment
- Regularly rotate your API keys

### ❌ DON'T:
- Share your API keys publicly
- Commit `.env` files to version control
- Use production keys in development
- Store keys in client-side code for production apps
- Ignore rate limits

### Production Deployment

For production, use environment variables instead of localStorage:

```bash
# Server-side environment
export GEMINI_API_KEY="your-key-here"
export DEEPSEEK_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"
export STRIPE_SECRET_KEY="your-secret-key-here"
```

---

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Enable debug mode in `.env`
3. Export your configuration for debugging
4. Contact support with your exported configuration (keys removed)

---

## API Endpoint Reference

| API | Base URL | Auth Method |
|-----|----------|-------------|
| Gemini | `https://generativelanguage.googleapis.com` | API Key in URL param |
| DeepSeek | `https://api.deepseek.com` | Bearer Token |
| OpenRouter | `https://openrouter.ai` | Bearer Token |
| Stripe | `https://api.stripe.com` | Basic Auth / Bearer |

---

*Last updated: September 2026*
*Version: 1.0.0*