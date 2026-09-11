/**
 * Client Playbook Generator
 * Generates a 1-page deployment guide PDF/HTML for delivered projects.
 */
import express from 'express';
import { protect, authorize } from '../middleware/auth.js';
import logger from '../utils/logger.js';

const router = express.Router();

/**
 * GET /api/playbook/:projectType — generate client playbook
 * projectType: ecommerce | medical | saas
 */
router.get('/:projectType', protect, authorize('admin', 'vendor'), (req, res, next) => {
  try {
    const { projectType } = req.params;
    const { brandName = 'Your Brand', domain = 'yourbrand.com' } = req.query;

    const playbooks = {
      ecommerce: generateEcommercePlaybook(brandName, domain),
      medical: generateMedicalPlaybook(brandName, domain),
      saas: generateSaaSPlaybook(brandName, domain),
    };

    const html = playbooks[projectType];
    if (!html) {
      return res.status(400).json({ success: false, error: 'Invalid project type. Use: ecommerce, medical, or saas' });
    }

    res.setHeader('Content-Type', 'text/html');
    res.send(html);
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/playbook/:projectType/json — playbook as JSON for frontend rendering
 */
router.get('/:projectType/json', protect, authorize('admin', 'vendor'), (req, res, next) => {
  try {
    const { projectType } = req.params;
    const { brandName = 'Your Brand', domain = 'yourbrand.com' } = req.query;

    const data = {
      ecommerce: getEcommerceData(brandName, domain),
      medical: getMedicalData(brandName, domain),
      saas: getSaaSData(brandName, domain),
    };

    if (!data[projectType]) {
      return res.status(400).json({ success: false, error: 'Invalid project type' });
    }

    res.json({ success: true, data: data[projectType] });
  } catch (error) {
    next(error);
  }
});

function getEcommerceData(brand, domain) {
  return {
    title: `${brand} — Client Playbook`,
    sections: [
      {
        step: 1,
        title: 'Connect Your Stripe Account',
        items: [
          'Go to dashboard.stripe.com and create an account (or log in).',
          'Navigate to Developers → API Keys.',
          'Copy your Publishable Key (pk_test_...) and Secret Key (sk_test_...).',
          'In your Vercel dashboard, go to Settings → Environment Variables.',
          'Add STRIPE_SECRET_KEY = sk_test_... and STRIPE_PUBLISHABLE_KEY = pk_test_....',
          'Redeploy the project to apply the new keys.',
          'Test with card number 4242 4242 4242 4242, any future date, any CVC.',
        ],
      },
      {
        step: 2,
        title: 'Customize Your Branding',
        items: [
          `Update the site name in public/index.html and src/config/brand.js to "${brand}".`,
          'Replace the logo in src/assets/logos/ with your own SVG or PNG logo.',
          'Update colors in tailwind.config.js → theme → colors → primary.',
          'Change the favicon in public/favicon.ico.',
          'Update meta tags in public/index.html (title, description, OG image).',
        ],
      },
      {
        step: 3,
        title: 'Set Up Your Domain',
        items: [
          `Purchase ${domain} from your registrar (Namecheap, Google Domains, etc.).`,
          'In Vercel, go to your project → Settings → Domains.',
          `Add ${domain} and www.${domain}.`,
          'Update your DNS records as Vercel instructs (A record or CNAME).',
          'SSL certificate is automatically provisioned by Vercel.',
          'Enable "Always HTTPS" in Vercel domain settings.',
        ],
      },
      {
        step: 4,
        title: 'Add Your Products',
        items: [
          'Log in as admin (admin@example.com / Password123!).',
          'Go to Admin Dashboard → Products → Add New Product.',
          'Upload product photos (recommended: 800x800px, white background).',
          'Set prices, stock levels, and categories.',
          'Enable "Featured" for products you want on the homepage.',
        ],
      },
      {
        step: 5,
        title: 'Going Live Checklist',
        items: [
          'Switch Stripe keys from test (pk_test_) to live (pk_live_).',
          'Update Vercel env vars with live Stripe keys.',
          'Update CORS_ORIGIN in backend .env to your production domain.',
          'Enable rate limiting and security headers.',
          'Test a real $1 transaction to verify payment flow.',
          'Set up Stripe webhooks: dashboard.stripe.com → Webhooks → Add endpoint.',
          'Webhook URL: https://yourdomain.com/api/payments/webhook',
          'Select events: checkout.session.completed, payment_intent.succeeded',
        ],
      },
    ],
    support: {
      email: 'support@lumicorepro.com',
      docs: 'https://docs.lumicorepro.com',
      uptime: '99.9% SLA on Vercel/Railway',
    },
  };
}

function getMedicalData(brand, domain) {
  return {
    title: `${brand} — Medical Portal Playbook`,
    sections: [
      {
        step: 1,
        title: 'Configure Stripe for Deposits',
        items: [
          'Create or log in to your Stripe account.',
          'Enable Stripe Connect if you need multi-doctor payouts.',
          'Set deposit amounts per service in the admin dashboard.',
          'Add STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY to Vercel env.',
          'Test deposits with card 4242 4242 4242 4242.',
        ],
      },
      {
        step: 2,
        title: 'Add Your Doctors',
        items: [
          'Go to Admin → Doctors → Add Doctor.',
          'Upload professional headshots (recommended: 400x400px).',
          'Set specialties, qualifications, consultation fees, and working hours.',
          'Configure slot duration (15/30/45/60 minutes).',
        ],
      },
      {
        step: 3,
        title: 'Set Up Services & Pricing',
        items: [
          'Go to Admin → Services → Add Service.',
          'Define service name, duration, price, and deposit amount.',
          'Assign services to specific doctors or leave general.',
          'Categories: general, dermatology, dental, cardiology, orthodontics.',
        ],
      },
      {
        step: 4,
        title: 'Email Configuration',
        items: [
          'Configure SMTP settings in backend .env (Gmail, SendGrid, etc.).',
          'Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS.',
          'Test with a booking to verify confirmation emails are sent.',
          'Customize email templates in backend/services/email.service.js.',
        ],
      },
      {
        step: 5,
        title: 'Go Live Checklist',
        items: [
          'Switch Stripe to live mode.',
          'Update domain and CORS settings.',
          'Enable HIPAA-compliant hosting if handling PHI.',
          'Set up appointment reminder emails (24h before).',
          'Test full booking flow: patient books → email → doctor confirms.',
        ],
      },
    ],
    support: {
      email: 'support@lumicorepro.com',
      docs: 'https://docs.lumicorepro.com/medical',
    },
  };
}

function getSaaSData(brand, domain) {
  return {
    title: `${brand} — SaaS Setup Playbook`,
    sections: [
      {
        step: 1,
        title: 'Set Up Stripe Subscriptions',
        items: [
          'Create products in Stripe Dashboard: Starter ($19/mo), Pro ($49/mo), Enterprise ($99/mo).',
          'Copy the Price IDs (price_...) for each plan.',
          'Add plans via Admin → Pricing → Add Plan.',
          'Paste Stripe Price IDs into each plan record.',
          'Add STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY to Vercel env.',
        ],
      },
      {
        step: 2,
        title: 'Configure Google OAuth',
        items: [
          'Go to console.cloud.google.com → APIs & Services → Credentials.',
          'Create OAuth 2.0 Client ID (Web application).',
          'Add authorized redirect URI: https://yourdomain.com/api/auth/oauth/google/callback.',
          'Copy Client ID and Client Secret to backend .env:',
          'GOOGLE_CLIENT_ID=... and GOOGLE_CLIENT_SECRET=...',
          'Enable the Google+ API in the console.',
        ],
      },
      {
        step: 3,
        title: 'Customize Your Branding',
        items: [
          `Update brand name in src/config/brand.js and public/index.html.`,
          'Replace logo and update color scheme in tailwind.config.js.',
          'Customize the pricing page copy and feature lists.',
          'Update the landing page hero section.',
        ],
      },
      {
        step: 4,
        title: 'Set Up Credits System',
        items: [
          'Configure credits per plan in the admin dashboard.',
          'Set up credit消耗 tracking in the backend.',
          'Add credit purchase as a one-time option (credit packs).',
          'Monitor credit usage in Admin → Analytics.',
        ],
      },
      {
        step: 5,
        title: 'Go Live Checklist',
        items: [
          'Switch all Stripe keys to live mode.',
          'Set up webhook: checkout.session.completed, customer.subscription.*',
          'Enable email notifications for subscription events.',
          'Test: signup → Google OAuth → subscribe → dashboard → credits.',
          'Set up monitoring (Vercel Analytics, Stripe Dashboard alerts).',
        ],
      },
    ],
    support: {
      email: 'support@lumicorepro.com',
      docs: 'https://docs.lumicorepro.com/saas',
    },
  };
}

function generateEcommercePlaybook(brand, domain) {
  const data = getEcommerceData(brand, domain);
  return wrapHTML(data);
}

function generateMedicalPlaybook(brand, domain) {
  const data = getMedicalData(brand, domain);
  return wrapHTML(data);
}

function generateSaaSPlaybook(brand, domain) {
  const data = getSaaSData(brand, domain);
  return wrapHTML(data);
}

function wrapHTML(data) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>${data.title}</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f8fafc;color:#1e293b;line-height:1.6;padding:2rem}
  .container{max-width:800px;margin:0 auto}
  h1{font-size:1.8rem;margin-bottom:0.5rem;color:#0f172a}
  .subtitle{color:#64748b;margin-bottom:2rem;font-size:0.95rem}
  .step{background:#fff;border-radius:12px;padding:1.5rem;margin-bottom:1rem;border:1px solid #e2e8f0;box-shadow:0 1px 3px rgba(0,0,0,0.04)}
  .step-header{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem}
  .step-num{background:#3b82f6;color:#fff;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;flex-shrink:0}
  .step-title{font-size:1.1rem;font-weight:600;color:#0f172a}
  .step ul{padding-left:1.25rem}
  .step li{margin-bottom:0.4rem;color:#475569;font-size:0.9rem}
  .step li code{background:#f1f5f9;padding:0.15rem 0.4rem;border-radius:4px;font-size:0.82rem;color:#7c3aed}
  .footer{margin-top:2rem;padding-top:1rem;border-top:1px solid #e2e8f0;color:#94a3b8;font-size:0.8rem;text-align:center}
  @media print{body{padding:1rem}.step{break-inside:avoid}}
</style>
</head>
<body>
<div class="container">
  <h1>${data.title}</h1>
  <p class="subtitle">Follow these steps to get your project live. Estimated time: 30-45 minutes.</p>
  ${data.sections.map(s => `
  <div class="step">
    <div class="step-header">
      <div class="step-num">${s.step}</div>
      <div class="step-title">${s.title}</div>
    </div>
    <ul>
      ${s.items.map(i => `<li>${i}</li>`).join('\n      ')}
    </ul>
  </div>`).join('')}
  <div class="footer">
    Generated by LumicorePro | Support: ${data.support.email} | Docs: ${data.support.docs}
  </div>
</div>
</body>
</html>`;
}

export default router;
