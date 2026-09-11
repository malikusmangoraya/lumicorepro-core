#!/usr/bin/env node

/**
 * LumiCorePro Setup Script
 * This script helps clients set up the application with API keys
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = (query) => new Promise((resolve) => rl.question(query, resolve));

async function main() {
  console.log('\n🚀 Welcome to LumiCorePro Setup!\n');
  console.log('This script will help you configure your API keys and get started.\n');

  // Check if .env file exists
  const envPath = path.join(__dirname, '..', '.env');
  const envExamplePath = path.join(__dirname, '..', '.env.example');

  if (!fs.existsSync(envPath)) {
    console.log('� Creating .env file from .env.example...');
    if (fs.existsSync(envExamplePath)) {
      fs.copyFileSync(envExamplePath, envPath);
      console.log('✅ .env file created successfully!\n');
    } else {
      console.error('❌ .env.example not found. Please create a .env file manually.\n');
      process.exit(1);
    }
  } else {
    console.log('✅ .env file already exists.\n');
  }

  console.log('🔑 Setup Options:\n');
  console.log('1. Configure AI Provider Keys (Gemini, DeepSeek, OpenRouter)');
  console.log('2. Configure Payment Keys (Stripe)');
  console.log('3. Configure Database (MongoDB)');
  console.log('4. Configure Email Service (SMTP)');
  console.log('5. Skip setup (I will configure manually)\n');

  const choice = await question('Enter your choice (1-5): ');

  switch (choice.trim()) {
    case '1':
      await setupAIKeys();
      break;
    case '2':
      await setupStripe();
      break;
    case '3':
      await setupDatabase();
      break;
    case '4':
      await setupEmail();
      break;
    case '5':
      console.log('\n⏭️ Skipping automated setup. You can configure .env manually.\n');
      break;
    default:
      console.log('\n� Invalid choice. Please run the script again.\n');
      process.exit(1);
  }

  console.log('\n✨ Setup complete! Next steps:');
  console.log('1. Run: npm install (if not already done)');
  console.log('2. Run: npm run dev (to start frontend)');
  console.log('3. Visit: http://localhost:5173');
  console.log('4. Navigate to "API Settings" to test your API keys\n');

  rl.close();
}

async function setupAIKeys() {
  console.log('\n--- AI Provider Setup ---\n');
  console.log('Get your API keys from:');
  console.log('  • Gemini:    https://aistudio.google.com/app/apikey');
  console.log('  • DeepSeek:  https://platform.deepseek.com/api_keys');
  console.log('  • OpenRouter: https://openrouter.ai/keys\n');

  const geminiKey = await question('Enter your Gemini API Key (or press Enter to skip): ');
  const deepseekKey = await question('Enter your DeepSeek API Key (or press Enter to skip): ');
  const openrouterKey = await question('Enter your OpenRouter API Key (or press Enter to skip): ');

  if (geminiKey || deepseekKey || openrouterKey) {
    updateEnvFile('GEMINI_API_KEY', geminiKey || 'your_gemini_key');
    updateEnvFile('DEEPSEEK_API_KEY', deepseekKey || 'your_deepseek_key');
    updateEnvFile('OPENROUTER_API_KEY', openrouterKey || 'your_openrouter_key');
  }

  console.log('\n✅ AI Provider keys configured!\n');
}

async function setupStripe() {
  console.log('\n--- Stripe Payment Setup ---\n');
  console.log('Get your API keys from: https://dashboard.stripe.com/api-keys\n');

  const secretKey = await question('Enter your Stripe Secret Key (sk_...): ');
  const publishableKey = await question('Enter your Stripe Publishable Key (pk_...): ');

  if (secretKey) updateEnvFile('STRIPE_SECRET_KEY', secretKey);
  if (publishableKey) updateEnvFile('STRIPE_PUBLISHABLE_KEY', publishableKey);

  console.log('\n✅ Stripe keys configured!\n');
}

async function setupDatabase() {
  console.log('\n--- Database Setup ---\n');
  console.log('Get your MongoDB connection string from: https://www.mongodb.com/cloud/atlas\n');

  const mongoUri = await question('Enter your MongoDB URI (or press Enter to use default): ');

  if (mongoUri.trim()) {
    updateEnvFile('MONGODB_URI', mongoUri);
  }

  console.log('\n✅ Database configured!\n');
}

async function setupEmail() {
  console.log('\n--- Email Service Setup ---\n');

  const host = await question('SMTP Host (e.g., smtp.gmail.com): ');
  const port = await question('SMTP Port (default: 587): ');
  const user = await question('SMTP Username (your email): ');
  const pass = await question('SMTP Password/App Password: ');

  if (host) updateEnvFile('SMTP_HOST', host);
  if (port) updateEnvFile('SMTP_PORT', port);
  if (user) updateEnvFile('SMTP_USER', user);
  if (pass) updateEnvFile('SMTP_PASS', pass);

  console.log('\n✅ Email service configured!\n');
}

function updateEnvFile(key, value) {
  const envPath = path.join(__dirname, '..', '.env');
  let envContent = fs.existsSync(envPath) ? fs.readFileSync(envPath, 'utf8') : '';

  const regex = new RegExp(`^${key}=.*`, 'm');
  if (regex.test(envContent)) {
    envContent = envContent.replace(regex, `${key}=${value}`);
  } else {
    envContent += `\n${key}=${value}`;
  }

  fs.writeFileSync(envPath, envContent);
  console.log(`  ✓ ${key} updated`);
}

main().catch((err) => {
  console.error('\n❌ Setup failed:', err.message);
  rl.close();
  process.exit(1);
});