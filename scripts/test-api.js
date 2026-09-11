#!/usr/bin/env node

/**
 * LumiCorePro API Testing Script
 * Tests API connectivity for configured providers
 */

const https = require('https');
const http = require('http');

// Load .env file
require('dotenv').config({ path: './.env' });

const providers = [
  {
    name: 'Google Gemini',
    key: process.env.GEMINI_API_KEY,
    testFn: testGemini,
  },
  {
    name: 'DeepSeek',
    key: process.env.DEEPSEEK_API_KEY,
    testFn: testDeepSeek,
  },
  {
    name: 'OpenRouter',
    key: process.env.OPENROUTER_API_KEY,
    testFn: testOpenRouter,
  },
  {
    name: 'Stripe',
    key: process.env.STRIPE_SECRET_KEY,
    testFn: testStripe,
  },
];

async function main() {
  console.log('\n🧪 LumiCorePro - API Connection Tests\n');
  console.log('Testing API connectivity for configured providers...\n');

  let passed = 0;
  let failed = 0;
  let skipped = 0;

  for (const provider of providers) {
    if (!provider.key || provider.key.startsWith('your_')) {
      console.log(`⏭️ ${provider.name}: Skipped (no API key configured)`);
      skipped++;
      continue;
    }

    try {
      const result = await provider.testFn(provider.key);
      if (result.success) {
        console.log(`✅ ${provider.name}: Connected successfully (${result.message})`);
        passed++;
      } else {
        console.log(`❌ ${provider.name}: Failed (${result.message})`);
        failed++;
      }
    } catch (error) {
      console.log(`❌ ${provider.name}: Error (${error.message})`);
      failed++;
    }
  }

  console.log(`\n--- Test Summary ---`);
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`⏭️ Skipped: ${skipped}`);
  console.log('');

  if (failed > 0) {
    console.log('Some tests failed. Check your API keys and configuration.\n');
    process.exit(1);
  } else {
    console.log('All tests passed! Your API configuration is working correctly.\n');
  }
}

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const isHttps = url.startsWith('https');
    const lib = isHttps ? https : http;
    
    const req = lib.request(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    
    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    req.end();
  });
}

async function testGemini(apiKey) {
  // Test by fetching available models
  const result = await makeRequest(
    `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`
  );
  
  if (result.status === 200 && result.body.models) {
    return { success: true, message: `${result.body.models.length} models available` };
  }
  return { success: false, message: `HTTP ${result.status}: Invalid API key` };
}

async function testDeepSeek(apiKey) {
  const result = await makeRequest('https://api.deepseek.com/v1/models', {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (result.status === 200 && result.body.data) {
    return { success: true, message: `${result.body.data.length} models available` };
  }
  return { success: false, message: `HTTP ${result.status}: Invalid API key` };
}

async function testOpenRouter(apiKey) {
  const result = await makeRequest('https://openrouter.ai/api/v1/auth/key', {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
  });
  
  if (result.status === 200) {
    return { success: true, message: 'API key is valid' };
  }
  return { success: false, message: `HTTP ${result.status}: Invalid API key` };
}

async function testStripe(apiKey) {
  const result = await makeRequest('https://api.stripe.com/v1/account', {
    headers: {
      'Authorization': `Bearer ${apiKey}`,
    },
  });
  
  if (result.status === 200) {
    return { success: true, message: 'Connected to Stripe account' };
  }
  return { success: false, message: `HTTP ${result.status}: Invalid API key` };
}

// Handle missing dotenv gracefully
if (!process.env.GEMINI_API_KEY && !process.env.DEEPSEEK_API_KEY && !process.env.OPENROUTER_API_KEY && !process.env.STRIPE_SECRET_KEY) {
  console.log('\n⚠️  No API keys found. Make sure .env file exists with valid API keys.\n');
  console.log('Available environment variables:\n');
  console.log('  GEMINI_API_KEY, DEEPSEEK_API_KEY, OPENROUTER_API_KEY, STRIPE_SECRET_KEY\n');
} else {
  main().catch(console.error);
}